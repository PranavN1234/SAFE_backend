import random
from app.models import Account
from app import db

def generate_unique_account_number():
    while True:
        number = random.randint(10000000, 99999999)  # Generates a random 8-digit number
        existing_account = Account.query.filter_by(acct_no=number).first()
        if not existing_account:
            return number
