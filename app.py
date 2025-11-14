from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.secret_key = 'krish_secure_key'

# MySQL Config
# SQLite Config (works anywhere, no setup required)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

# -------------------------
# Database Models
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    account = db.relationship('Account', backref='user', uselist=False)  # One-to-One

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_no = db.Column(db.Integer, unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# -------------------------
# Routes
# -------------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# -------------------------
# Signup
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash("User already exists! Please login.", "warning")
            return redirect(url_for('login'))

        new_user = User(name=name, email=email, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

# -------------------------
# Login
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('login.html')

# -------------------------
# Dashboard
# -------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    acc = Account.query.filter_by(user_id=user.id).first()
    return render_template('dashboard.html', username=user.username, account=acc)

# -------------------------
# Logout
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# -------------------------
# Add Account (1 per user)
# -------------------------
def generate_unique_account_no():
    while True:
        num = random.randint(100, 999)
        if not Account.query.filter_by(account_no=num).first():
            return num

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    existing_account = Account.query.filter_by(user_id=session['user_id']).first()
    if existing_account:
        flash("You already have an account!", "info")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        initial = request.form.get('initial', 0)
        try:
            initial = float(initial)
        except:
            initial = 0.0

        account_no = generate_unique_account_no()
        new_acc = Account(account_no=account_no, balance=initial, user_id=session['user_id'])
        db.session.add(new_acc)
        db.session.commit()
        flash(f"Account Created! Account No: {account_no}", "success")
        return redirect(url_for('dashboard'))

    return render_template('add.html')

# -------------------------
# Deposit
# -------------------------
@app.route('/depo', methods=['GET', 'POST'])
def depo():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    acc = Account.query.filter_by(user_id=session['user_id']).first()
    if not acc:
        flash("You don’t have an account!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        acc.balance += amount
        db.session.commit()
        flash(f"₹{amount} deposited successfully! New Balance: ₹{acc.balance}", "success")
        return redirect(url_for('dashboard'))
    return render_template('depo.html', account=acc)

# -------------------------
# Withdraw
# -------------------------
@app.route('/withd',methods=['GET','POST'])
def withd():
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))
    
    acc = Account.query.filter_by(user_id=session['user_id']).first()
    if not acc:
        flash("You don't have an account")
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        amount = float(request.form['amount'])
        if 0<amount<=acc.balance:
            acc.balance-=amount
        else:
            flash(f"Insiffcient balance", "warning")
        db.session.commit()
        flash(f"₹{amount} withdraw successfully! New Balance: ₹{acc.balance}", "success")
        return redirect(url_for('dashboard'))
    return render_template('with.html', account=acc)

# -------------------------
# Check Balance
# -------------------------
@app.route('/check', methods=['GET'])
def check():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login'))

    acc = Account.query.filter_by(user_id=session['user_id']).first()

    if acc:
        balance = acc.balance
        account_no = acc.account_no
        return render_template('check.html', balance=balance, account_no=account_no)
    else:
        flash("You don't have an account yet!", "danger")
        return redirect(url_for('dashboard'))



# -------------------------
# Run
# -------------------------
# LOCAL RUN
if __name__ == "__main__":
    app.run(debug=True)

# VERCEL RUN
def handler(environ, start_response):
    return app(environ, start_response)

