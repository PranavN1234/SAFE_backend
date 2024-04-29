import os
from . import api_blueprint
from flask import request, jsonify, current_app
from flask_cors import CORS, cross_origin
from app.utils.helpers import generate_unique_account_number
from app.models import Account, Auth, Customer, CheckingAccount, SavingsAccount, Loan, University, StudentLoan, PersonalLoan, HomeLoan
from app import db
from datetime import datetime

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
        return jsonify({'message': 'Login successful', 'username': username, 'customer_id': user.customer_id}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@api_blueprint.route('/create_account', methods=['POST'])
def create_account():
    data = request.get_json()

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