import os
from . import api_blueprint
from flask import request, jsonify, current_app
from flask_cors import CORS, cross_origin
from app.utils.helpers import generate_unique_account_number
from app.models import Account, Auth, Customer
from app import db

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
    # Assume other account details are handled here
    account_number = generate_unique_account_number()
    # new_account = Account(acct_no=account_number)
    # db.session.add(new_account)
    db.session.commit()
    return jsonify({'message': 'Account created', 'account_number': account_number}), 201