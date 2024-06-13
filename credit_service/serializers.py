from rest_framework import serializers
from .models import User, Loan, Transaction, Billing, Payment, EMI

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'annual_income']


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['unique_user_id', 'loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursement_date']

# class PaymentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Payment
#         fields = ['loan_id', 'amount']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class BillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Billing
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class EMISerializer(serializers.ModelSerializer):
    class Meta:
        model = EMI
        fields = '__all__'
