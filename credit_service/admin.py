from django.contrib import admin
from .models import User, Transaction, Loan ,EMI, Billing, Payment

class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'aadhar_id', 'annual_income', 'credit_score', 'created_at')
    readonly_fields = ('aadhar_id', 'created_at')

class LoanAdmin(admin.ModelAdmin):
    list_display = ('id','user_id', 'loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursement_date', 'principal_balance', 'is_closed')

class EMIAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan', 'date', 'amount_due', 'is_paid')

class BillingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'billing_date', 'min_due', 'due_date')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan', 'date', 'amount')


admin.site.register(User, UserAdmin)
admin.site.register(Loan, LoanAdmin) 
admin.site.register(EMI, EMIAdmin)
admin.site.register(Billing, BillingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Transaction )

