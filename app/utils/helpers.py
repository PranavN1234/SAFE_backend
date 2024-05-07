import random
import string
from app.models import Account, Transaction, Customer
from datetime import datetime, timedelta
from decimal import Decimal
from app import db
from sqlalchemy.orm import aliased


def generate_unique_account_number():
    while True:
        number = random.randint(10000000, 99999999)  # Generates a random 8-digit number
        existing_account = Account.query.filter_by(acct_no=number).first()
        if not existing_account:
            return number

def generate_unique_transaction_id():
    while True:
        # Generate a random 7-character alphanumeric string
        transaction_id = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
        # Check if this ID already exists in the database
        existing_transaction = Transaction.query.filter_by(t_id=transaction_id).first()
        if not existing_transaction:
            return transaction_id


def calculate_balances(account_id):
    # Fetch the last 30 transactions for the given account
    transactions = (
        Transaction.query
        .filter(
            (Transaction.from_account == account_id) | (Transaction.to_account == account_id)
        )
        .order_by(Transaction.timestamp.desc())  # Order by descending to get the latest first
        .limit(30)  # Only fetch the latest 30 transactions
        .all()
    )

    transactions.reverse()  # Reverse to process them from oldest to newest

    balance = Decimal(500)  # Starting balance
    balances = []

    # Calculate the effect of each transaction on the balance
    for transaction in transactions:
        if transaction.to_account == account_id:
            balance += transaction.amount
        elif transaction.from_account == account_id:
            balance -= transaction.amount
        balances.append({
            "date": transaction.timestamp.strftime('%Y-%m-%d'),
            "balance": format(balance, '.2f')  # Formatting balance to 2 decimal places
        })

    return balances

