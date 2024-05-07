import os
from . import api_blueprint
from flask import request, jsonify, current_app
from flask_cors import CORS, cross_origin
from app.utils.helpers import generate_unique_account_number, generate_unique_transaction_id, calculate_balances
from app.models import Account, Auth, Customer, CheckingAccount, SavingsAccount, Loan, University, StudentLoan, PersonalLoan, HomeLoan, Transaction
from app import db
from datetime import datetime, timedelta
from decimal import Decimal
import stripe
import os
from sqlalchemy.orm import aliased


@api_blueprint.route('/', methods=['GET'])
def hello_world():
    return jsonify({"hello world": "hello world"})

@api_blueprint.route('/accounts', methods=['GET'])
def get_accounts():
    accounts = Account.query.all()
    accounts_list = [{
        'account_number': acct.acct_no,
        'account_name': acct.acct_name,
        'account_street': acct.acct_street,
        'account_city': acct.acct_city,
        'account_state': acct.acct_state,
        'account_zip': acct.acct_zip,
        'account_type': acct.acct_type,
        'date_opened': acct.date_opened.strftime('%Y-%m-%d'),  # Formatting date
        'customer_id': acct.customerid
    } for acct in accounts]
    return jsonify(accounts_list)

@api_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    cfname = data.get('cfname')
    clname = data.get('clname')
    cstreet = data.get('cstreet')
    ccity = data.get('ccity')
    czip = data.get('czip')
    cstate = data.get('cstate')
    username = data.get('username')
    password = data.get('password')

    if not all([cfname, clname, cstreet, ccity, czip, cstate, username, password]):
        return jsonify({'error': 'Missing information'}), 400

    if Auth.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    # Create new Customer entry
    new_customer = Customer(cfname=cfname, clname=clname, cstreet=cstreet, ccity=ccity, czip=czip, cstate=cstate)
    db.session.add(new_customer)
    db.session.flush()  # Flush to assign an ID to new_customer

    # Create Auth entry linked to the new Customer
    new_auth = Auth(customer_id=new_customer.customerid, username=username)
    new_auth.set_password(password)
    db.session.add(new_auth)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@api_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = Auth.query.filter_by(username=username).first()
    if user and user.check_password(password):
        customer = Customer.query.get(user.customer_id)
        if customer:
            fullname = f"{customer.cfname} {customer.clname}"
            return jsonify({'message': 'Login successful', 'username': username, 'customer_id': user.customer_id, 'fullname': fullname, 'is_admin': user.is_admin}), 200
        else:
            return jsonify({'error': 'Customer not found'}), 404
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@api_blueprint.route('/create_account', methods=['POST'])
def create_account():
    data = request.get_json()

    print(data)
    required_fields = ['acctType', 'acctStreet', 'acctCity', 'acctState', 'acctZip', 'customerId']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    customer = Customer.query.get(data['customerId'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    account_number = generate_unique_account_number()
    account_name = f"{customer.cfname} {customer.clname} {data['acctType']}"

    new_account = Account(
        acct_no=account_number,
        acct_name=account_name,
        acct_street=data['acctStreet'],
        acct_city=data['acctCity'],
        acct_state=data['acctState'],
        acct_zip=data['acctZip'],
        acct_type=data['acctType'],
        date_opened=datetime.utcnow(),
        customerid=data['customerId'],
        status='pending'  # Assuming all new accounts start as 'pending'
    )
    db.session.add(new_account)
    if data['acctType'] == 'Checking':
        new_checking_account = CheckingAccount(
            acct_no=account_number,
            service_charge=data.get('serviceCharge')
        )
        db.session.add(new_checking_account)
    elif data['acctType'] == 'Savings':
        new_savings_account = SavingsAccount(
            acct_no=account_number,
            interest_rate=data.get('interestRate')
        )
        db.session.add(new_savings_account)
    elif data['acctType'] == 'Loan':
        new_loan_account = Loan(
            acct_no=account_number,
            loan_rate=data.get('loanRate'),
            loan_amount=data.get('loanAmount'),
            loan_payment=0,
            loan_months=data.get('loanMonths'),
            loan_type=data.get('loanType'),
        )
        db.session.add(new_loan_account)

        if data['loanType'] == 'Student':
            # Check if the university already exists
            university = University.query.filter_by(universityname=data['universityname']).first()
            if not university:

                university = University(universityname=data['universityname'])
                db.session.add(university)
                db.session.flush()  # Flush to get the new university ID

            new_student_loan = StudentLoan(
                acct_no=account_number,
                studentid=data['studentid'],
                status=data['studentStatus'],
                expecteddate=datetime.strptime(data['expecteddate'], '%Y-%m-%d'),
                universityid=university.universityid  # Use the ID from existing or new university
            )
            db.session.add(new_student_loan)

        elif data['loanType'] == 'Personal':
            new_personal_loan = PersonalLoan(
                acct_no=account_number
            )
            db.session.add(new_personal_loan)

        elif data['loanType'] == 'Home':
            new_home_loan = HomeLoan(
                acct_no=account_number,
                builtyear=data['builtyear'],
                hianumber=data['hianumber'],
                icname=data['icname'],
                icstreet=data['icstreet'],
                iccity=data['iccity'],
                icstate=data['icstate'],
                iczip=data['iczip'],
                premium=data['premium']
            )
            db.session.add(new_home_loan)




    db.session.commit()
    return jsonify({'message': 'Account created', 'account_number': account_number}), 201

@api_blueprint.route('/get_accounts', methods=['GET'])
def get_accounts_customer():
    print('get accounts called!!')
    customer_id = request.args.get('customer_id')
    print(customer_id)
    if not customer_id:
        return jsonify({'error': 'Customer ID is required'}), 400

    try:
        customer_id = int(customer_id)  # Convert to integer, handle possible ValueError
    except ValueError:
        return jsonify({'error': 'Invalid customer ID'}), 400

    accounts = Account.query.filter_by(customerid=customer_id).all()
    print(accounts)
    if not accounts:
        return jsonify({'message': 'No accounts found for this customer'}), 404

    accounts_list = []
    for account in accounts:
        account_info = {
            'account_number': account.acct_no,
            'account_name': account.acct_name,
            'account_type': account.acct_type,
            'date_opened': account.date_opened.strftime('%Y-%m-%d'),
            'status': account.status
        }

        if account.acct_type == 'Checking':
            checking = CheckingAccount.query.filter_by(acct_no=account.acct_no).first()
            account_info['balance'] = checking.balance

        if account.acct_type == 'Savings':
            saving = SavingsAccount.query.filter_by(acct_no=account.acct_no).first()
            account_info['balance'] = saving.balance

        if account.acct_type == 'Loan':
            loan = Loan.query.filter_by(acct_no=account.acct_no).first()
            if loan:
                loan_info = {
                    'loan_amount': loan.loan_amount,
                    'loan_rate': loan.loan_rate,
                    'loan_months': loan.loan_months,
                    'loan_type': loan.loan_type
                }
                account_info['LoanInfo'] = loan_info

                if loan.loan_type == 'Student':
                    student_loan = StudentLoan.query.filter_by(acct_no=account.acct_no).join(University).first()
                    if student_loan:
                        student_info = {
                            'student_id': student_loan.studentid,
                            'status': student_loan.status,
                            'expected_date': student_loan.expecteddate.strftime('%Y-%m-%d'),
                            'university_name': student_loan.university.universityname
                        }
                        loan_info['StudentInfo'] = student_info
                elif loan.loan_type == 'Home':
                    home_loan = HomeLoan.query.filter_by(acct_no=account.acct_no).first()
                    if home_loan:
                        home_info = {
                            'builtyear': home_loan.builtyear,
                            'hianumber': home_loan.hianumber,
                            'icname': home_loan.icname,
                            'icstreet': home_loan.icstreet,
                            'iccity': home_loan.iccity,
                            'icstate': home_loan.icstate,
                            'iczip': home_loan.iczip,
                            'premium': home_loan.premium
                        }
                        loan_info['HomeInfo'] = home_info

        accounts_list.append(account_info)


    return jsonify(accounts_list)

@api_blueprint.route('/pending_accounts', methods=['GET'])
def get_pending_accounts():
    # Query to join Account, Customer, and optionally Loan based on account status 'Pending'
    results = (db.session.query(Account, Customer, Loan)
                .join(Customer, Account.customerid == Customer.customerid)
                .outerjoin(Loan, Account.acct_no == Loan.acct_no)
                .filter(Account.status == 'Pending')
                .all())

    accounts_list = []
    for account, customer, loan in results:
        # Basic account and customer info
        account_info = {
            'customer_name': f"{customer.cfname} {customer.clname}",
            'customer_id': customer.customerid,
            'account_number': account.acct_no,
            'account_type': account.acct_type,
            'loan_type': None,
            'loan_amount': None
        }

        # Include loan info if present
        if loan:
            account_info['loan_type'] = loan.loan_type if loan.loan_type else "N/A"
            account_info['loan_amount'] = loan.loan_amount if loan.loan_amount else "N/A"

        accounts_list.append(account_info)

    return jsonify(accounts_list)


@api_blueprint.route('/approve_accounts', methods=['POST'])
def approve_accounts():
    data = request.get_json()
    account_numbers = data.get('account_numbers')

    if not account_numbers:
        return jsonify({'error': 'No account numbers provided'}), 400

    accounts_to_approve = Account.query.filter(Account.acct_no.in_(account_numbers), Account.status == 'pending').all()

    for account in accounts_to_approve:
        account.status = 'approved'

    db.session.commit()

    return jsonify({'message': f'{len(accounts_to_approve)} accounts approved successfully'}), 200

@api_blueprint.route('/balances/<int:customer_id>', methods=['GET'])
def get_balances(customer_id):
    # Retrieve all accounts linked to the customer
    accounts = Account.query.filter_by(customerid=customer_id).all()

    # Initialize balances
    balances = {
        'checking_balance': 0,
        'savings_balance': 0
    }

    # Iterate over accounts to find checking and savings accounts
    for account in accounts:
        if account.acct_type == 'Checking' and hasattr(account, 'checking_account'):
            balances['checking_balance'] += account.checking_account.balance
        elif account.acct_type == 'Savings' and hasattr(account, 'savings_account'):
            balances['savings_balance'] += account.savings_account.balance

    # Check if balances were updated from their initial state
    if balances['checking_balance'] == 0 and balances['savings_balance'] == 0:
        return jsonify({'error': 'No checking or savings accounts found for this customer'}), 404

    return jsonify(balances), 200

@api_blueprint.route('/transfer_money', methods=['POST'])
def transfer_money():
    data = request.get_json()
    from_customer_id = data.get('from_customer_id')
    to_acct_no = data.get('to_acct_no')
    from_account_type = data.get('type')  # 'checking' or 'savings'
    amount = Decimal(data.get('amount'))

    if not all([from_customer_id, to_acct_no, amount, from_account_type]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Start a transaction
        db.session.begin()

        # Locking accounts for update to ensure atomicity and prevent deadlocks
        from_account, from_account_main = get_account(from_customer_id, from_account_type, lock=True)
        to_account, to_account_main = get_account_by_number(to_acct_no, lock=True)

        if not from_account or not to_account:
            db.session.rollback()
            return jsonify({'error': 'One or more accounts not found'}), 404

        # account = Account.query.filter_by(acct_no=account_number).one_or_none()
        from_acct = Account.query.filter_by(customerid=from_customer_id).first()
        to_acct = Account.query.filter_by(acct_no=to_acct_no).first()

        if from_acct.status == 'pending' or to_acct.status=='pending':
            db.session.rollback()
            return jsonify({'error': 'One or more accounts not approved'}), 404

        print(from_acct.status, to_acct.status)
        if from_account.balance < amount:
            db.session.rollback()
            return jsonify({'error': 'Insufficient funds'}), 403

        # Adjust balances
        from_account.balance -= amount
        to_account.balance += amount

        # Create and record the transaction
        transaction = Transaction(
            t_id=generate_unique_transaction_id(),
            from_account=from_account_main.acct_no,
            to_account=to_account_main.acct_no,
            amount=amount
        )
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'message': 'Transfer successful'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def get_account(customer_id, account_type, lock=False):
    """Fetch account based on type and customer ID with optional locking."""
    if account_type.lower() == 'checking':
        account_class = CheckingAccount
    else:
        account_class = SavingsAccount
    query = db.session.query(account_class).join(Account).filter(Account.customerid == customer_id)
    if lock:
        query = query.with_for_update()
    account = query.first()
    if account:
        return account, account.account
    return None, None

def get_account_by_number(account_number, lock=False):
    """Fetch account by account number with optional locking."""
    account = Account.query.filter_by(acct_no=account_number).one_or_none()
    if account:
        sub_account = CheckingAccount.query.filter_by(acct_no=account_number).first() \
                     if account.acct_type == 'Checking' else \
                     SavingsAccount.query.filter_by(acct_no=account_number).first()
        if lock and sub_account:
            db.session.query(type(sub_account)).filter_by(acct_no=account_number).with_for_update().first()
        return sub_account, account
    return None, None


@api_blueprint.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.get_json()
    customer_id = data.get('customer_id')
    current_password = data.get('current_password')
    new_username = data.get('new_username', None)
    new_password = data.get('new_password', None)

    if not all([customer_id, current_password]):
        return jsonify({'error': 'Missing required information'}), 400

    # Fetch the user's authentication record
    auth_record = Auth.query.filter_by(customer_id=customer_id).first()
    if not auth_record:
        return jsonify({'error': 'User not found'}), 404

    # Verify the current password
    if not auth_record.check_password(current_password):
        return jsonify({'error': 'Incorrect password'}), 401

    # Update username if provided
    if new_username:
        # Check if the new username is already taken
        if Auth.query.filter(Auth.username == new_username, Auth.customer_id != customer_id).first():
            return jsonify({'error': 'Username already taken'}), 409
        auth_record.username = new_username

    # Update password if provided
    if new_password:
        auth_record.set_password(new_password)

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


@api_blueprint.route('/account_balance_over_time/<int:customer_id>', methods=['GET'])
def get_account_balance_over_time(customer_id):
    # Fetch the customer
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    # Prepare the response dictionary
    response = {}

    # Check for a Checking account
    checking_account = Account.query.filter_by(customerid=customer_id, acct_type='Checking').first()
    if checking_account:
        checking_balances = calculate_balances(checking_account.acct_no)
        response['checking'] = checking_balances

    # Check for a Savings account
    savings_account = Account.query.filter_by(customerid=customer_id, acct_type='Savings').first()
    if savings_account:
        savings_balances = calculate_balances(savings_account.acct_no)
        response['savings'] = savings_balances

    return jsonify(response)

@api_blueprint.route('/loan_status_by_customer/<int:customer_id>', methods=['GET'])
def get_loan_status_by_customer(customer_id):
    # Retrieve all loans linked to any accounts owned by the customer
    loans = Loan.query.join(Account).filter(Account.customerid == customer_id).all()

    loans_data = []

    for loan in loans:
        remaining_loan = loan.loan_amount - loan.loan_payment
        loans_data.append({
            'account_number': loan.acct_no,
            'loan_amount': loan.loan_amount,
            'loan_paid': loan.loan_payment,
            'remaining_loan': remaining_loan,
        })

    return jsonify(loans_data)

@api_blueprint.route('/transactions/<int:customer_id>', methods=['GET'])
def get_customer_transactions(customer_id):
    # First, find all account numbers associated with the customer
    accounts = Account.query.filter_by(customerid=customer_id).all()
    account_numbers = [account.acct_no for account in accounts]

    # Then, retrieve all transactions that involve any of these account numbers
    transactions = Transaction.query.filter(
        (Transaction.from_account.in_(account_numbers)) | (Transaction.to_account.in_(account_numbers))
    ).all()

    # Format the transactions for the response
    transactions_data = [{
        'transaction_id': transaction.t_id,
        'from_account': transaction.from_account,
        'to_account': transaction.to_account,
        'amount': str(transaction.amount),
        'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for transaction in transactions]

    return jsonify(transactions_data), 200

@api_blueprint.route('/delete_account', methods=['POST'])
def delete_account():
    pass
@api_blueprint.route('/add_funds', methods=['POST'])
def add_funds():
    data = request.get_json()
    customer_id = data.get('customer_id')
    payment_method_id = data.get('paymentMethodId')
    amount = data.get('amount')

    amount_in_cents = int(Decimal(amount) * 100)

    try:
        # Correctly configure the PaymentIntent to avoid redirect-based payment methods
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='usd',
            payment_method=payment_method_id,
            confirm=True,  # Automatically confirm the payment
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never'  # Correct usage according to the Stripe documentation
            }
        )

        if intent.status == 'succeeded':
            # If payment is successful, update the user's checking account
            account = CheckingAccount.query.join(Account).filter(
                Account.customerid == customer_id,
                Account.acct_type == 'Checking'
            ).first()

            if account:
                account.balance += Decimal(amount)
                db.session.commit()
                transaction_id = generate_unique_transaction_id()

                # Record the transaction as both from and to the same account
                transaction = Transaction(
                    t_id=transaction_id,
                    from_account=account.acct_no,
                    to_account=account.acct_no,
                    amount=Decimal(amount)
                )
                db.session.add(transaction)
                db.session.commit()

                return jsonify({'message': 'Payment successful and funds added', 'new_balance': str(account.balance)}), 200
            else:
                return jsonify({'error': 'Checking account not found'}), 404
        else:
            return jsonify({'error': 'Payment failed', 'details': intent.status}), 400

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500




    # For now, just return a success message with the received amount
@api_blueprint.route('/pay_loan', methods=['POST'])
def pay_loan():
    data = request.get_json()
    loan_account_number = data.get('loanAccountNumber')
    payment_account_type = data.get('paymentAccountType')
    payment_amount = Decimal(data.get('paymentAmount'))
    customer_id = data.get('customerId')

    if not all([loan_account_number, payment_account_type, payment_amount, customer_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Fetch the loan account
    loan_account = Loan.query.join(Account).filter(Account.acct_no == loan_account_number).first()
    if not loan_account:
        return jsonify({'error': 'Loan account not found'}), 404

    # Check if the loan is already fully paid
    if loan_account.loan_amount <= loan_account.loan_payment:
        return jsonify({'error': 'Loan already fully paid'}), 400

    # Fetch the payment source account
    if payment_account_type.lower() == 'checking':
        payment_account = CheckingAccount.query.join(Account).filter(Account.customerid == customer_id).first()
    elif payment_account_type.lower() == 'savings':
        payment_account = SavingsAccount.query.join(Account).filter(Account.customerid == customer_id).first()
    else:
        return jsonify({'error': 'Invalid account type specified'}), 400

    if not payment_account:
        return jsonify({'error': 'Payment account not found'}), 404

    # Check if there are sufficient funds in the payment account
    if payment_account.balance < payment_amount:
        return jsonify({'error': 'Insufficient funds'}), 403

    # Process the payment
    payment_account.balance -= payment_amount
    loan_account.loan_payment += payment_amount
    remaining_balance = loan_account.loan_amount - loan_account.loan_payment

    # Create a transaction record
    transaction = Transaction(
        t_id=generate_unique_transaction_id(),
        from_account=payment_account.acct_no,
        to_account=loan_account.account.acct_no,
        amount=payment_amount
    )
    db.session.add(transaction)

    db.session.commit()

    return jsonify({
        'message': 'Payment successful',
        'remaining_balance': remaining_balance
    }), 200


