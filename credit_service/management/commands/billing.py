from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from credit_service.models import User, Billing

class Command(BaseCommand):
    help = 'Initiates billing process for users'

    def handle(self, *args, **kwargs):
        # Fetch users who need billing
        users_to_bill = User.objects.all()

        billings = []

        for user in users_to_bill:
            print("Processing user:", user)

            billing_date = timezone.now().date()
            due_date = billing_date + timedelta(days=15)
            # Calculate min due amount (adjust this as per your requirements)
            min_due = user.annual_income * Decimal('0.1') 
            
            try:
                print("User:", user)
                if user.pk:  # Check if user primary key exists
                    billing = Billing.objects.create(user=user, billing_date=billing_date, due_date=due_date, min_due=min_due)
                    billings.append(billing)
                else:
                    print("User has no primary key:", user)
            except Exception as e:
                print("Error creating billing for user:", user)
                print(e)

        if billings:
                Billing.objects.bulk_create(billings)
                self.stdout.write(self.style.SUCCESS('Successfully populated transactions'))
        else:
            self.stdout.write(self.style.WARNING('No transactions to populate'))
