from django.core.management.base import BaseCommand
from django.utils import timezone
from credit_service.models import User, Loan , EMI , Transaction, Billing, Payment

class Command(BaseCommand):
    help = 'Run daily billing process'

    def handle(self, *args, **kwargs):
        loans = Loan.objects.filter(is_closed=False)
        for loan in loans:
            # Perform billing logic
            pass