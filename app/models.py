# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# --- Admin Model (for Login) ---
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256') # Explicit method

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'

# --- Orphan Model ---
class Orphan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    admission_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    gender = db.Column(db.String(10), nullable=False) # e.g., 'Male', 'Female', 'Other'
    guardian_info = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Orphan {self.name}>'

# --- Donation Model ---
class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False) # Suitable for currency
    donation_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    purpose = db.Column(db.String(200), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True) # e.g., 'Credit Card', 'Bank Transfer', 'Cash'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Donation {self.id} by {self.donor_name}>'

# --- Expense Model ---
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False) # e.g., 'Food', 'Utilities', 'Education', 'Healthcare'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.id} - {self.description}>'

# --- NGO Member Model ---
class NGOMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    join_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NGOMember {self.name} ({self.designation})>'