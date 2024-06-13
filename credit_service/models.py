from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# class User(AbstractUser):
#     unique_user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
#     annual_income = models.DecimalField(max_digits=10, decimal_places=2)
#     credit_score = models.IntegerField(default=0)
    
#     # Avoiding clashes with Django's auth.User model
#     groups = models.ManyToManyField(
#         'auth.Group',
#         related_name='credit_service_user_set',  # Change related_name to avoid conflict
#         blank=True,
#         help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
#         verbose_name='groups',
#     )
#     user_permissions = models.ManyToManyField(
#         'auth.Permission',
#         related_name='credit_service_user_set',  # Change related_name to avoid conflict
#         blank=True,
#         help_text='Specific permissions for this user.',
#         verbose_name='user permissions',
#     )

class User(models.Model):
    unique_user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    credit_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('CC', 'Credit Card')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=2, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_period = models.IntegerField()
    disbursement_date = models.DateField()
    loan_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

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
