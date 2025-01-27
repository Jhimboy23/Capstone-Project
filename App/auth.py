from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db  # Import db from your application
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user: 
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again', category='error')
        else:
            flash('Email does not exist', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        first_name = request.form.get('firstName', '').strip()  # Use first_name to match your model
        password1 = request.form.get('password1', '').strip()
        password2 = request.form.get('password2', '').strip()

        # Debugging: print the form data
        print(f"Email: {email}, First Name: {first_name}, Password1: {password1}, Password2: {password2}")

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exist', category='error') 

        if not email or len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif not first_name or len(first_name) < 2:
            flash('First Name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif not password1 or len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            # Check if the user already exists
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email address already exists.', category='error')
            else:
                # Add user to the database
                new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='pbkdf2:sha256'))
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect(url_for('views.home'))  # Ensure views.home route exists

    return render_template("sign_up.html", user=current_user)
