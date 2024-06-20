# Credit Service Application

## Overview
This project is a Django-based application that handles user registrations, loan applications, EMI payments, and billing processes. It includes various Django models, views, and Celery tasks for background processing.

## Installation

### Prerequisites
- Python 3.x
- Django
- Celery
- Redis

### Steps
1. Clone the repository:
    ```bash
    git clone https://github.com/shashank-23002/Credit-Service
    cd Brightmoney
    ```

2. Create a virtual environment and activate it:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Apply the migrations:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. Run the development server:
    ```bash
    python manage.py runserver
    ```

## Configuration

### Django Settings

Ensure that your `settings.py` file has the necessary configurations for Celery:

```python
# settings.py

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

6. Ensure Redis is installed and running on your system. You can start Redis using:
    ```bash
    redis-server
    ```

7. Start the Celery worker:
    ```bash
    celery -A Brightmoney worker --loglevel=info
    ```

8. Start the Celery task asynchronously:
    ```bash
    python manage.py import_transactions
    ```

9. Setup Cron Job  :
    ```bash
    python manage.py billing
    ```


## Models

### User
- `aadhar_id`: CharField (Primary Key)
- `name`: CharField
- `email`: EmailField
- `annual_income`: DecimalField
- `credit_score`: IntegerField
- `created_at`: DateTimeField

### Loan
- `user_id`: ForeignKey(User)
- `loan_type`: CharField
- `loan_amount`: DecimalField
- `interest_rate`: DecimalField
- `term_period`: IntegerField
- `disbursement_date`: DateField
- `principal_balance`: DecimalField
- `is_closed`: BooleanField
- `emi_dates`: TextField

### EMI
- `loan`: ForeignKey(Loan)
- `date`: DateField
- `amount_due`: DecimalField
- `is_paid`: BooleanField

### Transaction
- `user`: ForeignKey(User)
- `date`: DateField
- `amount`: DecimalField
- `transaction_type`: CharField

### Billing
- `user`: ForeignKey(User)
- `billing_date`: DateField
- `min_due`: DecimalField
- `due_date`: DateField

### Payment
- `loan`: ForeignKey(Loan)
- `date`: DateField
- `amount`: DecimalField

## Views and JSON Formats

### Register User
**URL:** `api/register-user/`

**Method:** POST

**Request JSON:**
```json
{
    "aadhar_id": "8bac0a2d-f31a-4fc4-a5d2-2e86b379915b",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "annual_income": "500000.00"
}
```

**Response JSON:**
```json
{
    "aadhar_id": "8bac0a2d-f31a-4fc4-a5d2-2e86b379915b"
}
```

### Apply Loan
**URL:** `api/apply-loan/`

**Method:** POST

**Request JSON:**
```json
{
    "user_id": "8bac0a2d-f31a-4fc4-a5d2-2e86b379915b",
    "loan_amount": "2000",
    "interest_rate": "5",
    "term_period": 6,
    "loan_type": "CREDIT_CARD",
    "disbursement_date": "2024-06-14"
}

```

**Response JSON:**
```json
{
    "loan_id": 3,
    "due_dates": [
        {"date": "2024-07-14", "amount_due": "338.21"},
        {"date": "2024-08-14", "amount_due": "338.21"},
    ]
}
```

### Make Payment
**URL:** `api/make-payment/`

**Method:** POST

**Request JSON:**
```json
{
    "loan_id": 1,
    "amount": "420.00"
}
```

**Response JSON:**
```json
{
    "message": "Payment recorded successfully."
}
```

### Get Statement
**URL:** `api/get-statement/`

**Method:** GET

**Query Parameters:** loan_id

**Example:** `api/get-statement/?loan_id=1`

**Response JSON:**
```json
{
    "error": null,
    "past_transactions": [
        {"date": "2024-06-14", "amount_paid": "420.00"},
        ...
    ],
    "upcoming_transactions": [
        {"date": "2024-08-13", "amount_due": "321.85"},
        {"date": "2024-09-12", "amount_due": "321.85"},
        ...
    ]
}
```

