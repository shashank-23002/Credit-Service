from django.shortcuts import render
from rest_framework import generics, status
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, Loan , EMI , Transaction, Billing, Payment
from .serializers import UserSerializer , LoanSerializer
from .tasks import calculate_credit_score
from decimal import Decimal
from datetime import date, timedelta
import json

class RegisterUserView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        print(request.data, " Line 20")
        if serializer.is_valid():
            serializer.save()
            calculate_credit_score.delay(request.data['aadhar_id'])
            return Response({'aadhar_id': request.data['aadhar_id']}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ApplyLoanView(generics.CreateAPIView):
    serializer_class = LoanSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            loan_amount = serializer.validated_data['loan_amount']
            interest_rate = serializer.validated_data['interest_rate']
            term_period = serializer.validated_data['term_period']

            try:
                user = User.objects.get(aadhar_id=request.data['user_id'])
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

            # Check credit score and annual income
            if user.credit_score < 450:
                return Response({"error": "User's credit score is below the required threshold."}, status=status.HTTP_400_BAD_REQUEST)
            if user.annual_income < 150000:
                return Response({"error": "User's annual income is below the required threshold."}, status=status.HTTP_400_BAD_REQUEST)
            if loan_amount > 5000:
                return Response({"error": "Requested loan amount exceeds the maximum limit of Rs. 5000."}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate EMIs
            emi_amount = self.calculate_emi(loan_amount, interest_rate, term_period, user.annual_income)
            if emi_amount is None:
                return Response({"error": "EMI exceeds 20% of the user's monthly income."}, status=status.HTTP_400_BAD_REQUEST)


            # Generate EMI schedule
            emi_dates = self.generate_emi_schedule(emi_amount, term_period)

            # Convert Decimal objects to strings
            loan_amount_str = str(loan_amount)

            # Convert date objects to strings
            emi_dates_str = [{k: str(v) if isinstance(v, date) else str(v) for k, v in emi_date.items()} for emi_date in emi_dates]

            # Create loan
            loan = Loan.objects.create(
                user_id=user,
                loan_type='Credit Card',
                loan_amount=loan_amount_str,
                interest_rate=interest_rate,
                term_period=term_period,
                disbursement_date=date.today(),
                emi_dates=json.dumps(emi_dates_str),  # Convert to JSON string
            )

            self.populate_emi_table(loan, emi_dates_str)

            return Response({"loan_id": loan.id, "due_dates": emi_dates_str}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def calculate_emi(self, principal, interest_rate, term_period, annual_income):
        monthly_income = Decimal(annual_income) / 12
        rate_per_month = Decimal(interest_rate) / Decimal(100) / 12
        emi = (principal * rate_per_month * (1 + rate_per_month)**term_period) / ((1 + rate_per_month)**term_period - 1)
        
        # Ensure EMI does not exceed 20% of monthly income
        if emi > monthly_income * Decimal('0.2'):
            return None
        return round(emi, 2)

    def generate_emi_schedule(self, emi_amount, term_period):
        emi_dates = []
        current_date = date.today()
        for i in range(term_period):
            emi_date = current_date + timedelta(days=30 * (i + 1))
            emi_dates.append({"date": emi_date, "amount_due": emi_amount})
        return emi_dates

    def populate_emi_table(self, loan, emi_dates_str):
        for emi_data in emi_dates_str:
            EMI.objects.create(
                loan=loan,
                date=emi_data['date'],
                amount_due=emi_data['amount_due'],
                is_paid=False  # Assuming all EMIs are initially unpaid
            )


class MakePaymentView(APIView):
    def post(self, request, *args, **kwargs):
        loan_id = request.data.get('loan_id')
        amount = Decimal(request.data.get('amount'))

        # Retrieve the loan object
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if payment already recorded for the specified date
        if Payment.objects.filter(loan=loan, date=date.today()).exists():
            return Response({"error": "Payment already recorded for today."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if previous EMIs remain unpaid
        unpaid_emis = EMI.objects.filter(loan=loan, is_paid=False, date__lt=date.today()).exists()
        if unpaid_emis:
            return Response({"error": "Previous EMIs remain unpaid."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the next due EMI
        try:
            next_emi = EMI.objects.filter(loan=loan, is_paid=False).earliest('date')
        except EMI.DoesNotExist:
            return Response({"error": "No upcoming EMIs found."}, status=status.HTTP_400_BAD_REQUEST)

        # Recalculate the EMI if the paid amount is not equal to the due amount
        if amount != next_emi.amount_due:
            # Update the EMI amount and adjust for future EMIs
            remaining_amount = next_emi.amount_due - amount
            next_emi.amount_due = amount
            next_emi.is_paid = True
            next_emi.save()

            # Adjust future EMIs (simplified recalculation for demonstration)
            remaining_emis = EMI.objects.filter(loan=loan, is_paid=False).order_by('date')
            for emi in remaining_emis:
                emi.amount_due += remaining_amount / len(remaining_emis)
                emi.save()
        else:
            next_emi.is_paid = True
            next_emi.save()

        # Record the payment
        Payment.objects.create(loan=loan, amount=amount, date=date.today())

        return Response({"message": "Payment recorded successfully."}, status=status.HTTP_200_OK)


class GetStatementView(APIView):
    def get(self, request, *args, **kwargs):
        loan_id = request.query_params.get('loan_id')

        # Retrieve the loan object
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch past transactions
        past_transactions = Payment.objects.filter(loan=loan)
        past_transactions_data = [
            {
                "date": transaction.date,
                "amount_paid": transaction.amount,
            }
            for transaction in past_transactions
        ]

        # Fetch upcoming EMIs
        upcoming_emis = EMI.objects.filter(loan=loan, date__gte=date.today(), is_paid=False)
        upcoming_emis_data = [
            {
                "date": emi.date,
                "amount_due": emi.amount_due,
            }
            for emi in upcoming_emis
        ]

        return Response({
            "error": None,
            "past_transactions": past_transactions_data,
            "upcoming_transactions": upcoming_emis_data
        }, status=status.HTTP_200_OK)