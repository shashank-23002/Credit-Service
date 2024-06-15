from django.db import models
import uuid

class User(models.Model):
    aadhar_id = models.CharField(max_length=50, unique=True, blank=True, primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    credit_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.aadhar_id:
            self.aadhar_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card')
    ]
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, to_field='aadhar_id')
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_period = models.IntegerField()  # in months
    disbursement_date = models.DateField()
    principal_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_closed = models.BooleanField(default=False)
    emi_dates = models.TextField(blank=True, null=True)


class EMI(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=6)

class Billing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    billing_date = models.DateField()
    min_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

class Payment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
