import csv
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from credit_service.models import User, Transaction

class Command(BaseCommand):
    help = 'Import transactions from a .csv file'

    def handle(self, *args, **kwargs):
        file_path = 'data/transactions.csv'
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user_id = row['user']
                date = parse_date(row['date'])
                transaction_type = row['transaction_type']
                amount = row['amount']

                user, created = User.objects.get_or_create(unique_user_id=user_id)

                Transaction.objects.create(
                    user=user,
                    date=date,
                    transaction_type=transaction_type,
                    amount=amount
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully imported transactions'))