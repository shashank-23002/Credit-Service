from celery import shared_task
from .models import User
import csv
from decimal import Decimal
from django.conf import settings

@shared_task
def calculate_credit_score(user_id):
    try:
        user = User.objects.get(aadhar_id=user_id)
    except User.DoesNotExist:
        return

    # Load CSV transactions for the user
    transactions = load_csv_transactions(user.aadhar_id)

    total_balance = sum(
        Decimal(transaction['amount']) if transaction['transaction_type'] == 'CREDIT' else -Decimal(transaction['amount'])
        for transaction in transactions
    )

    if total_balance >= 1000000:
        credit_score = 900
    elif total_balance <= 10000:
        credit_score = 300
    else:
        credit_score = 300 + int((total_balance - 10000) / 15000) * 10

    user.credit_score = min(credit_score, 900)
    user.save()

def load_csv_transactions(aadhar_id):
    transactions = []
    file_path = f"{settings.BASE_DIR}/data/transactions.csv"
    
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['user'] == aadhar_id:
                transactions.append({
                    'date': row['date'],
                    'amount': row['amount'],
                    'transaction_type': row['transaction_type']
                })
    return transactions
