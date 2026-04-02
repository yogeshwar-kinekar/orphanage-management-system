# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, SelectField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange, ValidationError
from app.models import Admin

# --- Login Form ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# --- Orphan Form ---
class OrphanForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    admission_date = DateField('Admission Date', format='%Y-%m-%d', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    guardian_info = StringField('Guardian Info (Optional)', validators=[Optional(), Length(max=200)])
    notes = TextAreaField('Notes (Optional)', validators=[Optional()])
    submit = SubmitField('Save Orphan')

# --- Donation Form ---
class DonationForm(FlaskForm):
    donor_name = StringField('Donor Name', validators=[DataRequired(), Length(max=100)])
    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    donation_date = DateField('Donation Date', format='%Y-%m-%d', validators=[DataRequired()])
    purpose = StringField('Purpose (Optional)', validators=[Optional(), Length(max=200)])
    payment_method = StringField('Payment Method (Optional)', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Donation')

# --- Expense Form ---
class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    expense_date = DateField('Expense Date', format='%Y-%m-%d', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired(), Length(max=50)]) # Could be SelectField if categories are fixed
    submit = SubmitField('Save Expense')

# --- NGO Member Form ---
class MemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    designation = StringField('Designation', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    join_date = DateField('Join Date', format='%Y-%m-%d', validators=[DataRequired()])
    is_active = BooleanField('Is Active?', default=True)
    submit = SubmitField('Save Member')