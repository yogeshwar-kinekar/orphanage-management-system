# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db # Import db from the app package (__init__.py)
from app.models import Admin, Orphan, Donation, Expense, NGOMember
from app.forms import LoginForm, OrphanForm, DonationForm, ExpenseForm, MemberForm
# werkzeug.security is usually handled within the model, but keep if needed elsewhere
# from werkzeug.security import check_password_hash
from sqlalchemy import func, desc # Import func for aggregations, desc for sorting
from decimal import Decimal # Import Decimal for calculations
from datetime import datetime, date # Import date for age calculation
from flask_wtf import FlaskForm # Import FlaskForm for CSRF token in list views

bp = Blueprint('main', __name__)

# --- Helper Function for formatting currency ---
def format_currency(value):
    if value is None:
        return "Rs0.00"
    # Ensure value is Decimal for formatting
    if not isinstance(value, Decimal):
        try:
            value = Decimal(value)
        except:
            return "Rs0.00" # Return default if conversion fails
    return "Rs{:,.2f}".format(value)

@bp.app_context_processor
def inject_utility_processor():
    # Pass the datetime.utcnow function itself, or the result if needed frequently
    # Passing the function allows {{ now().year }} in the template
    return dict(
        format_currency=format_currency,
        now=datetime.utcnow  # Use utcnow for consistency
    )

# --- Authentication Routes ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin is None or not admin.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('main.login'))
        login_user(admin, remember=form.remember_me.data)
        flash('Login successful!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

# --- Dashboard Route (with Chart Data Logic) ---
@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    try:
        # --- Standard Stats ---
        total_orphans = db.session.query(func.count(Orphan.id)).scalar() or 0
        total_donations = db.session.query(func.sum(Donation.amount)).scalar() or Decimal('0.00')
        # Note: Consider filtering total_expenses by month if that's what the card should show
        total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or Decimal('0.00')
        active_members = db.session.query(func.count(NGOMember.id)).filter(NGOMember.is_active == True).scalar() or 0

        # --- Chart Data Calculation ---

        # 1. Expenses Breakdown Data (All Categories)
        expenses_query = db.session.query(
                Expense.category,
                func.sum(Expense.amount).label('total_amount')
            ).group_by(Expense.category)\
            .order_by(desc('total_amount')).all()

        # Prepare data for Chart.js
        expense_labels = [item.category for item in expenses_query]
        # Convert Decimal to float for JSON serialization compatibility with Chart.js
        expense_data = [float(item.total_amount) for item in expenses_query]

        # 2. Orphan Age Distribution Data
        orphans = Orphan.query.all()
        today = date.today()
        age_brackets = {
            "0-2 yrs": 0,
            "3-5 yrs": 0,
            "6-9 yrs": 0,
            "10-12 yrs": 0,
            "13-16 yrs": 0,
            "17+ yrs": 0 # Catch older ones or errors
        }

        for orphan in orphans:
            if orphan.date_of_birth:
                try:
                    # Calculate age accurately
                    age = today.year - orphan.date_of_birth.year - \
                          ((today.month, today.day) < (orphan.date_of_birth.month, orphan.date_of_birth.day))

                    # Assign to bracket
                    if 0 <= age <= 2:
                        age_brackets["0-2 yrs"] += 1
                    elif 3 <= age <= 5:
                        age_brackets["3-5 yrs"] += 1
                    elif 6 <= age <= 9:
                        age_brackets["6-9 yrs"] += 1
                    elif 10 <= age <= 12:
                        age_brackets["10-12 yrs"] += 1
                    elif 13 <= age <= 16:
                        age_brackets["13-16 yrs"] += 1
                    else: # Age 17+ or potential edge cases
                        age_brackets["17+ yrs"] += 1
                except Exception as age_calc_error:
                     # Log specific error during age calculation
                     current_app.logger.error(f"Error calculating age for orphan {orphan.id} (DOB: {orphan.date_of_birth}): {age_calc_error}")
                     age_brackets["17+ yrs"] += 1 # Assign to 'other' on error
            else:
                 # Log warning for orphans missing DOB
                 current_app.logger.warning(f"Orphan {orphan.id} (Name: {orphan.name}) missing date_of_birth for age calculation.")
                 age_brackets["17+ yrs"] += 1 # Assign to 'other' if no DOB

        # Prepare data for Chart.js (Python 3.7+ dicts maintain insertion order)
        age_labels = list(age_brackets.keys())
        age_data = list(age_brackets.values())

        # --- Combine All Stats for Template ---
        stats = {
            'total_orphans': total_orphans,
            'total_donations': total_donations,
            'total_expenses': total_expenses, # This is still the *total* expense value
            'active_members': active_members,
            # Add chart data
            'expense_labels': expense_labels,
            'expense_data': expense_data,
            'age_labels': age_labels,
            'age_data': age_data,
        }

    except Exception as e:
         # Log the general error fetching dashboard data
         current_app.logger.error(f"Error fetching dashboard data: {e}", exc_info=True) # Log traceback
         flash("Error loading dashboard data. Please try again later.", "danger") # User-friendly message
         stats = { # Provide default empty values on error
            'total_orphans': 0,
            'total_donations': Decimal('0.00'),
            'total_expenses': Decimal('0.00'),
            'active_members': 0,
            'expense_labels': [],
            'expense_data': [],
            'age_labels': [],
            'age_data': [],
         }

    return render_template('dashboard.html', title='Dashboard', stats=stats)


# --- Orphan CRUD ---
@bp.route('/orphans')
@login_required
def list_orphans():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')
    query = Orphan.query

    if search_term:
        query = query.filter(Orphan.name.ilike(f'%{search_term}%'))

    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    allowed_sort_columns = ['id', 'name', 'date_of_birth', 'admission_date', 'gender', 'created_at']
    if sort_by not in allowed_sort_columns:
        sort_by = 'name' # Default to a safe column

    sort_column = getattr(Orphan, sort_by, Orphan.name) # Default to name

    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    orphans = query.paginate(page=page, per_page=10, error_out=False)
    form = FlaskForm() # Pass form for CSRF token in delete buttons
    return render_template(
        'orphans/list.html',
        title='Orphans',
        orphans=orphans,
        search_term=search_term,
        form=form # Pass the form
    )

@bp.route('/orphans/add', methods=['GET', 'POST'])
@login_required
def add_orphan():
    form = OrphanForm()
    if form.validate_on_submit():
        orphan = Orphan()
        form.populate_obj(orphan) # Populate model directly from form
        try:
            db.session.add(orphan)
            db.session.commit()
            flash('Orphan added successfully!', 'success')
            return redirect(url_for('main.list_orphans'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding orphan: {e}", exc_info=True)
            flash('Error adding orphan. Please check the details and try again.', 'danger')
    return render_template('orphans/form.html', title='Add Orphan', form=form, form_action=url_for('main.add_orphan'))

@bp.route('/orphans/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_orphan(id):
    orphan = Orphan.query.get_or_404(id)
    form = OrphanForm(obj=orphan) # Pre-populate form with orphan data
    if form.validate_on_submit():
        form.populate_obj(orphan) # Update model directly from form
        try:
            db.session.commit()
            flash('Orphan updated successfully!', 'success')
            return redirect(url_for('main.list_orphans'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating orphan {id}: {e}", exc_info=True)
            flash('Error updating orphan. Please check the details and try again.', 'danger')
    # Ensure date fields are set correctly for the form input type="date" on GET
    elif request.method == 'GET':
        form.date_of_birth.data = orphan.date_of_birth
        form.admission_date.data = orphan.admission_date
    return render_template('orphans/form.html', title='Edit Orphan', form=form, form_action=url_for('main.edit_orphan', id=id))

@bp.route('/orphans/delete/<int:id>', methods=['POST']) # Use POST for delete
@login_required
def delete_orphan(id):
    orphan = Orphan.query.get_or_404(id)
    try:
        # CSRF protection is typically handled by Flask-WTF globally if configured
        db.session.delete(orphan)
        db.session.commit()
        flash('Orphan deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting orphan {id}: {e}", exc_info=True)
        flash('Error deleting orphan.', 'danger')
    return redirect(url_for('main.list_orphans'))


# --- Donation CRUD ---
@bp.route('/donations')
@login_required
def list_donations():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')
    query = Donation.query
    if search_term:
        query = query.filter(Donation.donor_name.ilike(f'%{search_term}%'))

    sort_by = request.args.get('sort_by', 'donation_date')
    sort_order = request.args.get('sort_order', 'desc')

    allowed_sort_columns = ['id', 'donor_name', 'amount', 'donation_date', 'purpose', 'payment_method', 'created_at']
    if sort_by not in allowed_sort_columns:
        sort_by = 'donation_date'

    sort_column = getattr(Donation, sort_by, Donation.donation_date)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    donations = query.paginate(page=page, per_page=10, error_out=False)
    form = FlaskForm() # Pass form for CSRF token in delete buttons
    return render_template(
        'donations/list.html',
        title='Donations',
        donations=donations,
        search_term=search_term,
        form=form
    )

@bp.route('/donations/add', methods=['GET', 'POST'])
@login_required
def add_donation():
    form = DonationForm()
    if form.validate_on_submit():
        donation = Donation()
        form.populate_obj(donation) # Populate model from form
        try:
            db.session.add(donation)
            db.session.commit()
            flash('Donation added successfully!', 'success')
            return redirect(url_for('main.list_donations'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding donation: {e}", exc_info=True)
            flash('Error adding donation. Please try again.', 'danger')
    return render_template('donations/form.html', title='Add Donation', form=form, form_action=url_for('main.add_donation'))

@bp.route('/donations/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_donation(id):
    donation = Donation.query.get_or_404(id)
    form = DonationForm(obj=donation)
    if form.validate_on_submit():
        form.populate_obj(donation)
        try:
            db.session.commit()
            flash('Donation updated successfully!', 'success')
            return redirect(url_for('main.list_donations'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating donation {id}: {e}", exc_info=True)
            flash('Error updating donation. Please try again.', 'danger')
    elif request.method == 'GET':
        form.donation_date.data = donation.donation_date
    return render_template('donations/form.html', title='Edit Donation', form=form, form_action=url_for('main.edit_donation', id=id))

@bp.route('/donations/delete/<int:id>', methods=['POST'])
@login_required
def delete_donation(id):
    donation = Donation.query.get_or_404(id)
    try:
        db.session.delete(donation)
        db.session.commit()
        flash('Donation deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting donation {id}: {e}", exc_info=True)
        flash('Error deleting donation.', 'danger')
    return redirect(url_for('main.list_donations'))


# --- Expense CRUD ---
@bp.route('/expenses')
@login_required
def list_expenses():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')
    query = Expense.query
    if search_term:
         query = query.filter(
             (Expense.description.ilike(f'%{search_term}%')) |
             (Expense.category.ilike(f'%{search_term}%'))
         )

    sort_by = request.args.get('sort_by', 'expense_date')
    sort_order = request.args.get('sort_order', 'desc')

    allowed_sort_columns = ['id', 'description', 'amount', 'expense_date', 'category', 'created_at']
    if sort_by not in allowed_sort_columns:
        sort_by = 'expense_date'

    sort_column = getattr(Expense, sort_by, Expense.expense_date)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column.asc() if hasattr(sort_column, 'asc') else sort_column)

    expenses = query.paginate(page=page, per_page=10, error_out=False)
    form = FlaskForm() # Pass form for CSRF token in delete buttons
    return render_template(
        'expenses/list.html',
        title='Expenses',
        expenses=expenses,
        search_term=search_term,
        form=form
    )

# routes.py - Inside add_expense()

# app/routes.py - Ensure this is your add_expense function

@bp.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    current_app.logger.info("--- ENTERING add_expense route ---") # Use logger
    try:
        form = ExpenseForm() # Creates form instance
        current_app.logger.info("--- ExpenseForm instantiated successfully ---") # Log success
    except Exception as form_error:
        current_app.logger.error(f"--- ERROR Instantiating ExpenseForm: {form_error} ---", exc_info=True)
        flash("Error preparing the expense form. Please contact support.", "danger")
        return redirect(url_for('main.list_expenses')) # Redirect on form error

    if form.validate_on_submit(): # This is FALSE for a GET request
        # ... POST logic ...
        current_app.logger.info("--- Processing POST request for add_expense ---")
        try:
            expense = Expense()
            form.populate_obj(expense)
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('main.list_expenses'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding expense (POST): {e}", exc_info=True)
            flash('Error saving expense. Please try again.', 'danger')
            # Re-render form on POST error, potentially with errors shown
            return render_template('expenses/form.html', title='Add Expense', form=form, form_action=url_for('main.add_expense'))

    # --- GET Request Logic ---
    current_app.logger.info("--- Preparing to render expenses/form.html for GET request ---")
    current_app.logger.info(f"--- Passing title='Add Expense', form={type(form)}, action={url_for('main.add_expense')}")
    try:
        # Render the simplified template first
        return render_template('expenses/form.html', title='Add Expense', form=form, form_action=url_for('main.add_expense'))
    except Exception as render_error:
        current_app.logger.error(f"--- ERROR Rendering expenses/form.html: {render_error} ---", exc_info=True)
        flash("Error displaying the expense form. Please contact support.", "danger")
        return redirect(url_for('main.list_expenses')) # Redirect on render error
     
@bp.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    form = ExpenseForm(obj=expense)
    if form.validate_on_submit():
        form.populate_obj(expense)
        try:
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('main.list_expenses'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating expense {id}: {e}", exc_info=True)
            flash('Error updating expense. Please try again.', 'danger')
    elif request.method == 'GET':
        form.expense_date.data = expense.expense_date
    return render_template('expenses/form.html', title='Edit Expense', form=form, form_action=url_for('main.edit_expense', id=id))


@bp.route('/expenses/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting expense {id}: {e}", exc_info=True)
        flash('Error deleting expense.', 'danger')
    return redirect(url_for('main.list_expenses'))


# --- NGO Member CRUD (UPDATED) ---
@bp.route('/members')
@login_required
def list_members():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')
    query = NGOMember.query
    if search_term:
         # CORRECTED: Use designation and email for search
         query = query.filter(
             (NGOMember.name.ilike(f'%{search_term}%')) |
             (NGOMember.designation.ilike(f'%{search_term}%')) |
             (NGOMember.email.ilike(f'%{search_term}%'))
         )

    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    # CORRECTED: Use updated columns for sorting
    allowed_sort_columns = ['id', 'name', 'designation', 'email', 'phone', 'join_date', 'is_active', 'created_at']
    if sort_by not in allowed_sort_columns:
        sort_by = 'name'

    sort_column = getattr(NGOMember, sort_by, NGOMember.name)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    members = query.paginate(page=page, per_page=10, error_out=False)
    form = FlaskForm() # CORRECTED: Pass form for CSRF in delete
    return render_template(
        'members/list.html',
        title='NGO Members',
        members=members,
        search_term=search_term,
        form=form # CORRECTED: Pass the form
    )

@bp.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    form = MemberForm()
    if form.validate_on_submit():
        # CORRECTED: Use populate_obj for cleaner code
        member = NGOMember()
        form.populate_obj(member)
        # Manual assignment (alternative if needed):
        # member = NGOMember(
        #     name=form.name.data,
        #     designation=form.designation.data, # Changed from role
        #     email=form.email.data,             # Added email
        #     phone=form.phone.data,             # Added phone
        #     join_date=form.join_date.data,     # Added join_date
        #     is_active=form.is_active.data
        #     # Removed contact_info
        # )
        try:
            db.session.add(member)
            db.session.commit()
            flash('NGO Member added successfully!', 'success')
            return redirect(url_for('main.list_members'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding member: {e}", exc_info=True)
            flash('Error adding member. Please check the details and try again.', 'danger') # User-friendly message
    elif request.method == 'GET' and not form.join_date.data:
        # Pre-populate join_date with today's date only on initial GET request if not already set (e.g. validation error redisplay)
        form.join_date.data = date.today() # Use date.today()
    return render_template('members/form.html', title='Add NGO Member', form=form, form_action=url_for('main.add_member'))


@bp.route('/members/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    member = NGOMember.query.get_or_404(id)
    form = MemberForm(obj=member) # Pre-populate form
    if form.validate_on_submit():
        # CORRECTED: Use populate_obj for cleaner update
        form.populate_obj(member)
        # Manual assignment (alternative):
        # member.name=form.name.data
        # member.designation=form.designation.data # Changed from role
        # member.email=form.email.data             # Added email
        # member.phone=form.phone.data             # Added phone
        # member.join_date=form.join_date.data     # Added join_date
        # member.is_active=form.is_active.data
        # Removed contact_info updates
        try:
            db.session.commit()
            flash('NGO Member updated successfully!', 'success')
            return redirect(url_for('main.list_members'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating member {id}: {e}", exc_info=True)
            flash('Error updating member. Please check the details and try again.', 'danger')
    elif request.method == 'GET':
        # Ensure date is set correctly for the form on GET request (needed if obj=member doesn't format it perfectly)
        form.join_date.data = member.join_date
    return render_template('members/form.html', title='Edit NGO Member', form=form, form_action=url_for('main.edit_member', id=id))

@bp.route('/members/delete/<int:id>', methods=['POST'])
@login_required
def delete_member(id):
    member = NGOMember.query.get_or_404(id)
    try:
        # CSRF protection handled by Flask-WTF if configured
        db.session.delete(member)
        db.session.commit()
        flash('NGO Member deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting member {id}: {e}", exc_info=True)
        flash('Error deleting member.', 'danger')
    return redirect(url_for('main.list_members'))