from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, Loan , EMI , Transaction, Billing, Payment
from .serializers import UserSerializer , LoanSerializer
from .tasks import calculate_credit_score_task
from decimal import Decimal
from datetime import date, timedelta
import uuid
import csv
from io import StringIO

class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            csv_file = request.FILES['file']  # Assuming the CSV file is sent in the request
            csv_reader = csv.reader(StringIO(csv_file.read().decode('utf-8')))
            next(csv_reader)  # Skip the header row

            transactions = []
            for row in csv_reader:
                user_id, date, transaction_type, amount = row
                if user_id == str(user.unique_user_id):
                    transactions.append(Transaction(
                        user=user,
                        date=date,
                        transaction_type=transaction_type,
                        amount=Decimal(amount)
                    ))
            Transaction.objects.bulk_create(transactions)
            
            calculate_credit_score_task.delay(user.unique_user_id)
            return Response({"unique_user_id": user.unique_user_id}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ApplyLoanView(generics.CreateAPIView):
    serializer_class = LoanSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['unique_user_id']
            loan_amount = serializer.validated_data['loan_amount']
            interest_rate = serializer.validated_data['interest_rate']
            term_period = serializer.validated_data['term_period']

            try:
                user = User.objects.get(unique_user_id=user_id)
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

            # Create loan
            loan = Loan.objects.create(
                user=user,
                loan_type='Credit Card',
                loan_amount=loan_amount,
                interest_rate=interest_rate,
                term_period=term_period,
                disbursement_date=date.today(),
                emi_dates=emi_dates,
            )

            return Response({"loan_id": loan.loan_id, "due_dates": emi_dates}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def calculate_emi(self, principal, interest_rate, term_period, annual_income):
        monthly_income = annual_income / 12
        rate_per_month = (interest_rate / 100) / 12
        emi = (principal * rate_per_month * (1 + rate_per_month)**term_period) / ((1 + rate_per_month)**term_period - 1)
        
        # Ensure EMI does not exceed 20% of monthly income
        if emi > monthly_income * 0.2:
            return None
        return round(emi, 2)

    def generate_emi_schedule(self, emi_amount, term_period):
        emi_dates = []
        current_date = date.today()
        for i in range(term_period):
            emi_date = current_date + timedelta(days=30 * (i + 1))
            emi_dates.append({"date": emi_date, "amount_due": emi_amount})
        return emi_dates


class MakePaymentView(APIView):
    def post(self, request, *args, **kwargs):
        loan_id = request.data.get('loan_id')
        amount = Decimal(request.data.get('amount'))

        # Retrieve the loan object
        try:
            loan = Loan.objects.get(loan_id=loan_id)
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
            loan = Loan.objects.get(loan_id=loan_id)
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