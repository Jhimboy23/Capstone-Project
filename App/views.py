import csv
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from . import db  # Import db from your application

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        first_name = request.form.get('firstName', '').strip()
        password1 = request.form.get('password1', '').strip()
        password2 = request.form.get('password2', '').strip()

        # Initialize a flag to track if any changes are made
        changes_made = False

        # Validate and update email
        if email and len(email) >= 4:
            if current_user.email != email:
                current_user.email = email
                changes_made = True
        else:
            flash('Email must be greater than 4 characters.', category='error')

        # Validate and update first name
        if first_name and len(first_name) >= 2:
            if current_user.first_name != first_name:
                current_user.first_name = first_name
                changes_made = True
        else:
            flash('First Name must be greater than 1 character.', category='error')

        # Validate and update password
        if password1 or password2:  # Only check if at least one password field is filled
            if password1 != password2:
                flash('Passwords do not match.', category='error')
            elif len(password1) < 7:
                flash('Password must be at least 7 characters long.', category='error')
            else:
                # If passwords match and are valid, update the password
                current_user.password = generate_password_hash(password1, method='pbkdf2:sha256')
                changes_made = True
        elif password1 or password2:
            flash('Passwords must match and be at least 7 characters long.', category='error')

        # Commit changes if any were made
        if changes_made:
            db.session.commit()
            flash('Account updated!', category='success')
            return redirect(url_for('views.settings'))

    return render_template("settings.html", user=current_user)


@views.route('/controlPanel')
@login_required
def control_panel():
    return render_template("controlPanel.html")
