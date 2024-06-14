import csv
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from credit_service.models import User, Transaction
from django.conf import settings
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import transactions from a .csv file'

    def handle(self, *args, **kwargs):
        file_path = f"{settings.BASE_DIR}/data/transactions.csv"
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            transactions = []
            for row in reader:
                try:
                    user = User.objects.get(aadhar_id=row['user'])
                    transaction = Transaction(
                        user=user,
                        date=parse_date(row['date']),
                        amount=Decimal(row['amount']),
                        transaction_type=row['transaction_type'].upper()
                    )
                    transactions.append(transaction)
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'User with ID {row["user"]} does not exist.'))
                    break
            
            if transactions:
                Transaction.objects.bulk_create(transactions)
                self.stdout.write(self.style.SUCCESS('Successfully populated transactions'))
            else:
                self.stdout.write(self.style.WARNING('No transactions to populate'))

