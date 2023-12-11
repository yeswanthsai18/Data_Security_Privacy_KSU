# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, Flask, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_principal import Principal, Permission

from app.models import db, User, HealthRecord, data_encryption
from config import Config
import pandas as pd
from app.models import data_decryption

bp = Blueprint('main', __name__)
login_manager = LoginManager()
login_manager.login_view = 'main.login'  # Adjust this based on your route configuration

principal = Principal()

# Define roles
admin_permission = Permission('admin')
readonly_permission = Permission('readonly')

from .models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)

    # Initialize login manager and principal
    login_manager.init_app(app)
    principal.init_app(app)

    # Register blueprints or other configurations
    from .routes import bp as main_bp  # Import route definitions
    app.register_blueprint(main_bp)

    return app


# authentication and authorization decorators
@admin_permission.require(http_exception=403)
def admin_route():
    pass


@readonly_permission.require(http_exception=403)
def readonly_route():
    pass


# Helper functions to fetch data based on user group
def get_data_for_group_H():
    # Fetch health records excluding First_name and Last_name
    records = HealthRecord.query.all()

    data = []
    for record in records:
        data.append({
            'First_name': record.First_name,
            'Last_name': record.Last_name,
            'age': record.age,
            'Gender': record.Gender,
            'weight': record.weight,
            'height': record.height,
            'health_history': record.health_history,
        })

    return data


def get_data_for_group_R():
    # Fetch health records excluding First_name and Last_name
    records = HealthRecord.query.all()

    data = []
    for record in records:
        data.append({
            'age': record.age,
            'Gender': record.Gender,
            'weight': record.weight,
            'height': record.height,
            'health_history': record.health_history,
        })

    return data


@bp.route('/insert_data')
def insert_data():
    file_path = r"C:\Users\saisu\PycharmProjects\DataSecurityPrivacy_Project\patientsdetails.xlsx"
    df = pd.read_excel(file_path)

    for index, row in df.iterrows():
        if row['Gender'] not in ['Male', 'Female']:
            row['Gender'] = 'Male'  # or 'Female' based on your choice for non-standard values

# encrypting the data in database
        age_encrypted = data_encryption(row['age'])
        gender_encrypted = data_encryption(row['gender'])
        health_history_encrypted = data_encryption(row['health_history'])



        new_record = HealthRecord(
            First_name=row['First_name'],
            Last_name=row['Last_name'],
            age=row['age_encrypted'],
            Gender=row['gender_encrypted'],
            weight=row['weight'],
            height=row['height'],
            health_history=row['health_history_encrypted']
        )
        db.session.add(new_record)

    db.session.commit()
    return 'Data inserted successfully!'


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        group = request.form['group']  # Add this line to get the group from the form

        new_user = User(username=username, group=group)
        new_user.password_set(password)

        db.session.add(new_user)
        db.session.commit()

        # Log the user in after signup
        login_user(new_user)

        return redirect(url_for('main.dashboard'))

    return render_template('signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password_check(password):
            # Log the user in after successful login
            login_user(user)

            return redirect(url_for('main.dashboard'))

        else:
            return render_template('login.html', message='Invalid username or password')

    return render_template('login.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    # Assuming you have a function to fetch data based on user group
    if current_user.group == 'H':
        health_data = get_data_for_group_H()
    elif current_user.group == 'R':
        health_data = get_data_for_group_R()
    else:
        # Handle the case where user group is not set
        flash('Invalid user group', 'error')
        return redirect(url_for('main.login'))
        # Decrypt the data before passing it to the template

    ##decrypted_health_data = decrypt_health_data(health_data)

    return render_template('dashboard.html', health_data=health_data)


@bp.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if current_user.group == 'H':
        if request.method == 'POST':
            # Get form data
            First_name = request.form['First_name']
            Last_name = request.form['Last_name']
            age = request.form['age']
            Gender = request.form['Gender']
            weight = request.form['weight']
            height = request.form['height']
            health_history = request.form['health_history']

            # Create a new HealthRecord object
            new_record = HealthRecord(
                First_name=First_name,
                Last_name=Last_name,
                age=age,
                Gender=Gender,
                weight=weight,
                height=height,
                health_history=health_history
            )

            # Add the new record to the database
            db.session.add(new_record)
            db.session.commit()

            flash('New patient added successfully!', 'success')

            return redirect(url_for('main.dashboard'))

        return render_template('add_patient.html')

    else:
        flash('Invalid user group.', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('main.login'))
