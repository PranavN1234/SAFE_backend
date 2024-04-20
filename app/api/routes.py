import os
from . import api_blueprint
from flask import request, jsonify, current_app
from flask_cors import CORS, cross_origin
from app.models import Account

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