from app import db

class Customer(db.Model):
    __tablename__ = 'pba_customer'
    customerid = db.Column(db.Integer, primary_key=True, comment='Customer ID')
    cfname = db.Column(db.String(20), nullable=False, comment='Customer First Name')
    clname = db.Column(db.String(20), nullable=False, comment='Customer Last Name')
    cstreet = db.Column(db.String(20), nullable=False, comment='Customer Street')
    ccity = db.Column(db.String(20), nullable=False, comment='Customer City')
    cstate = db.Column(db.String(20), nullable=False, comment='Customer State')
    czip = db.Column(db.Integer, nullable=False, comment='Customer Zip')

    def __repr__(self):
        return f'<Customer {self.customerid} {self.cfname} {self.clname}>'

class Account(db.Model):
    __tablename__ = 'pba_account'
    acct_no = db.Column(db.Integer, primary_key=True, comment='Account number')
    acct_name = db.Column(db.String(50), nullable=False, comment='Account Name')
    acct_street = db.Column(db.String(20), nullable=False, comment='Account Street')
    acct_city = db.Column(db.String(20), nullable=False, comment='Account City')
    acct_state = db.Column(db.String(20), nullable=False, comment='Account State')
    acct_zip = db.Column(db.Integer, nullable=False, comment='Account Zip')
    acct_type = db.Column(db.String(11), nullable=False, comment='Account Type')
    date_opened = db.Column(db.DateTime, nullable=False, comment='Date Opened')
    customerid = db.Column(db.Integer, db.ForeignKey('pba_customer.customerid'), nullable=False, comment='Customer ID foreign key')

    checking_account = db.relationship('CheckingAccount', back_populates='account', uselist=False)
    savings_account = db.relationship('SavingsAccount', back_populates='account', uselist=False)
    loans = db.relationship('Loan', back_populates='account')
    def __repr__(self):
        return f'<Account {self.acct_name} {self.acct_type}>'

class CheckingAccount(db.Model):
    __tablename__ = 'pba_checking'
    acct_no = db.Column(db.Integer, db.ForeignKey('pba_account.acct_no'), primary_key=True, comment='Account number')
    service_charge = db.Column(db.Float, nullable=False, comment='Service Charge')

    # Relationship to link back to the Account model
    account = db.relationship('Account', back_populates='checking_account')

    def __repr__(self):
        return f'<CheckingAccount {self.acct_no} Service Charge: {self.service_charge}>'

class HomeLoan(db.Model):
    __tablename__ = 'pba_home'
    acct_no = db.Column(db.Integer, db.ForeignKey('pba_loan.acct_no'), primary_key=True, comment='Account number')
    builtyear = db.Column(db.SmallInteger, nullable=False, comment='Built Year')
    hianumber = db.Column(db.BigInteger, nullable=False, comment='Home Insurance Number')
    icname = db.Column(db.String(20), nullable=False, comment='Insurance Company Name')
    icstreet = db.Column(db.String(50), nullable=False, comment='Insurance Street')
    iccity = db.Column(db.String(20), nullable=False, comment='Insurance City')
    icstate = db.Column(db.String(20), nullable=False, comment='Insurance State')
    iczip = db.Column(db.Integer, nullable=False, comment='Insurance Zip')
    premium = db.Column(db.Integer, nullable=False, comment='Insurance Premium')

    # Relationship to link back to the Loan model (assuming Loan model is already defined)
    loan = db.relationship('Loan', back_populates='home_loan')

    def __repr__(self):
        return f'<HomeInsurance {self.acct_no} {self.icname}>'

class Loan(db.Model):
    __tablename__ = 'pba_loan'
    acct_no = db.Column(db.Integer, db.ForeignKey('pba_account.acct_no'), primary_key=True, comment='Account number')
    loan_rate = db.Column(db.Float, nullable=False, comment='Loan Rate')
    loan_amount = db.Column(db.BigInteger, nullable=False, comment='Loan Amount')
    loan_payment = db.Column(db.BigInteger, nullable=False, comment='Loan Payment')
    loan_months = db.Column(db.Integer, nullable=False, comment='Loan Months')
    loan_type = db.Column(db.String(8), nullable=False, comment='Loan Type')

    personal_loan = db.relationship('PersonalLoan', back_populates='loan', uselist=False)
    student_loan = db.relationship('StudentLoan', back_populates='loan', uselist=False)
    home_loan = db.relationship('HomeLoan', back_populates='loan', uselist=False)
    # Relationship to link back to the Account model
    account = db.relationship('Account', back_populates='loans')

    def __repr__(self):
        return f'<Loan {self.acct_no} Type: {self.loan_type}>'

class PersonalLoan(db.Model):
    __tablename__ = 'pba_personal'
    acct_no = db.Column(db.Integer, db.ForeignKey('pba_loan.acct_no'), primary_key=True, comment='Account number')

    # Relationship to link back to the Loan model
    loan = db.relationship('Loan', back_populates='personal_loan', uselist=False)

    def __repr__(self):
        return f'<PersonalLoan {self.acct_no}>'

class SavingsAccount(db.Model):
    __tablename__ = 'pba_savings'
    acct_no = db.Column(db.Integer, db.ForeignKey('pba_account.acct_no'), primary_key=True, comment='Account number')
    interest_rate = db.Column(db.Float, nullable=False, comment='Interest Rate')

    # Relationship to link back to the Account model
    account = db.relationship('Account', back_populates='savings_account')

    def __repr__(self):
        return f'<SavingsAccount {self.acct_no} Interest Rate: {self.interest_rate}>'

class StudentLoan(db.Model):
    __tablename__ = 'pba_student'
    acct_no = db.Column(db.Integer, db.ForeignKey('pba_loan.acct_no'), primary_key=True, comment='Account number')
    studentid = db.Column(db.Integer, nullable=False, comment='Student ID')
    status = db.Column(db.String(20), nullable=False, comment='Graduation status')
    expecteddate = db.Column(db.DateTime, nullable=False, comment='Expected Date')
    universityid = db.Column(db.Integer, db.ForeignKey('pba_university.universityid'), nullable=False, comment='University Id')

    # Relationship to link back to the Loan model
    loan = db.relationship('Loan', back_populates='student_loan')

    # Relationship to link to the University model (assumes a model University exists)
    university = db.relationship('University', back_populates='student_loans')

    def __repr__(self):
        return f'<StudentLoan {self.acct_no} Student ID: {self.studentid}>'

class University(db.Model):
    __tablename__ = 'pba_university'
    universityid = db.Column(db.Integer, primary_key=True, comment='UniversityId')
    universityname = db.Column(db.String(50), nullable=False, comment='University Name')

    # Relationship with StudentLoan, assuming you have a back reference set up in StudentLoan
    student_loans = db.relationship('StudentLoan', back_populates='university', lazy='dynamic')

    def __repr__(self):
        return f'<University {self.universityname}>'


