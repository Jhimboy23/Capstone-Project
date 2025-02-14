import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from flask import Blueprint, render_template, jsonify, request, flash, redirect, send_file, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from App.models import Data
from . import db  # Import db from your application
import psycopg2
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import csv
import os
import threading
import pandas as pd
import joblib
from datetime import timedelta

views = Blueprint('views', __name__)

# Path to the CSV file
CSV_FILE_PATH = "data.csv"

# Function to get the database connection
def get_db_connection():
    try:
        connection = psycopg2.connect(
            host="dpg-cub3sbogph6c73a37ub0-a.oregon-postgres.render.com",
            port="5432",
            database="demodatabase_5309",
            user="demodatabase_5309_user",
            password="lpETIp3Oyydp0ihdfg3R6G2Ox4WgwM6Y"
        )
        return connection
    except Exception as e:
        print(f"Error while connecting to the database: {e}")
        return None

# Function to convert status into integers
def convert_status(status_str):
    if status_str.lower() == "low":
        return 1
    elif status_str.lower() == "moderate":
        return 2
    elif status_str.lower() == "high":
        return 3
    else:
        return 0  # Default value for unknown statuses

# Function to initialize the CSV file
def initialize_csv():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT distance, status, duration, fuel_consumed, percentage, datetime FROM public."data";')
            all_data = cursor.fetchall()
            cursor.close()
            connection.close()

            # Convert status to integers
            formatted_data = [
                (
                    row[0],  # distance
                    convert_status(row[1]),  # status as integer
                    row[2],  # duration
                    row[3],  # fuel_consumed
                    row[4],  # percentage
                    row[5]   # datetime
                )
                for row in all_data
            ]

            with open(CSV_FILE_PATH, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["distance", "status", "duration", "fuel_consumed", "percentage", "datetime"])  # Header
                writer.writerows(formatted_data)
            print(f"CSV file '{CSV_FILE_PATH}' initialized with data from the database.")
    except Exception as e:
        print(f"Error while initializing CSV file: {e}")

# Function to refresh the CSV file if new data is added
def refresh_csv():
    last_row_count = 0  # Track the number of rows in the database
    while True:
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute('SELECT COUNT(*) FROM public."data";')  # Get total rows
                current_row_count = cursor.fetchone()[0]

                if current_row_count > last_row_count:  # New data detected
                    cursor.execute('SELECT distance, status, duration, fuel_consumed, percentage, datetime FROM public."data";')
                    all_data = cursor.fetchall()
                    cursor.close()
                    connection.close()

                    # Convert status to integers
                    formatted_data = [
                        (
                            row[0],  # distance
                            convert_status(row[1]),  # status as integer
                            row[2],  # duration
                            row[3],  # fuel_consumed
                            row[4],  # percentage
                            row[5]   # datetime
                        )
                        for row in all_data
                    ]

                    with open(CSV_FILE_PATH, mode="w", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(["distance", "status", "duration", "fuel_consumed", "percentage", "datetime"])  # Header
                        writer.writerows(formatted_data)

                    print(f"CSV file updated with {current_row_count - last_row_count} new rows.")
                    last_row_count = current_row_count  # Update row count tracker
                else:
                    cursor.close()
                    connection.close()

        except Exception as e:
            print(f"Error while refreshing CSV file: {e}")

        time.sleep(10)  # Wait for 10 seconds before checking again

# Start the CSV refresh thread
csv_refresh_thread = threading.Thread(target=refresh_csv, daemon=True)
csv_refresh_thread.start()

# Initialize the CSV file with all data from the database
initialize_csv()

# Function to append data to the CSV file
def append_to_csv(data):
    with open(CSV_FILE_PATH, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)
        
@views.route('/', methods=['GET'])
def home():
    averages = {}  # Dictionary to store averages for today, week, and month
    latest_liters = None  # Store latest liters value
    latest_distance = None  # Store latest distance value
    latest_remaining_fuel = None  # Store latest remaining fuel value

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query to fetch the last percentage, liters, distance, remainingFuel, and status
        query = "SELECT percentage, liters, distance, remainingFuel, status FROM data ORDER BY datetime DESC LIMIT 1"
        cursor.execute(query)
        latest_reading = cursor.fetchone()  # Fetch the latest reading

        if latest_reading:
            latest_liters = latest_reading[1]  # Extract liters value
            latest_distance = latest_reading[2]  # Extract distance value
            latest_remaining_fuel = latest_reading[3]  # Extract remainingFuel value

        # Define date ranges
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        # Last week's range: Sunday to Saturday
        week_end = today_start - timedelta(days=today_start.weekday() + 1)  # Last Saturday
        week_start = week_end - timedelta(days=6)  # The previous Sunday

        # Last month's range: First and last day of the previous calendar month
        first_day_this_month = today_start.replace(day=1)
        last_month_end = first_day_this_month - timedelta(days=1)  # Last day of the previous month
        last_month_start = last_month_end.replace(day=1)  # First day of the previous month

        # Queries to calculate averages
        avg_queries = {
            "today": "SELECT AVG(percentage) FROM data WHERE datetime BETWEEN %s AND %s",
            "week": "SELECT AVG(percentage) FROM data WHERE datetime BETWEEN %s AND %s",
            "month": "SELECT AVG(percentage) FROM data WHERE datetime BETWEEN %s AND %s",
        }
        params = {
            "today": (today_start, today_end),
            "week": (week_start, week_end),
            "month": (last_month_start, last_month_end),
        }

        # Execute average queries
        for period, query in avg_queries.items():
            cursor.execute(query, params[period])
            avg_value = cursor.fetchone()[0]
            averages[period] = "{:.4f}".format(avg_value) if avg_value is not None else 'No Data'

        cursor.close()
        connection.close()

        return render_template(
            "home.html",
            user=current_user,
            latest_data=latest_reading,
            averages=averages,
            latest_liters=latest_liters,
            latest_distance=latest_distance,
            latest_remaining_fuel=latest_remaining_fuel  # Pass remainingFuel value
        )

    except Exception as e:
        print(f"Error during request processing: {e}")
        return jsonify({'error': str(e)}), 500


@views.route('/get_percentage_data', methods=['GET'])
def get_percentage_data():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        range_type = request.args.get('range', 'today')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if range_type == "today":
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end = datetime.now()
        elif range_type == "week":
            end = datetime.now()
            start = end - timedelta(days=7)
        elif range_type == "month":
            end = datetime.now()
            start = end - timedelta(days=30)
        elif range_type == "custom" and start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            return jsonify({'error': 'Invalid range'}), 400

        query = """
        SELECT datetime, remainingFuel 
        FROM data 
        WHERE datetime BETWEEN %s AND %s 
        ORDER BY datetime ASC
        """
        cursor.execute(query, (start, end))
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        formatted_data = [
            {"datetime": row[0].strftime("%Y-%m-%d %H:%M:%S"), "remainingFuel": row[1]} 
            for row in data
        ]

        return jsonify(formatted_data)

    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({'error': str(e)}), 500


@views.route('/get_liters', methods=['GET'])
def get_liters():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch the latest liters value
        query = "SELECT liters FROM data ORDER BY datetime DESC LIMIT 1"
        cursor.execute(query)
        latest_liters = cursor.fetchone()

        cursor.close()
        connection.close()

        if latest_liters:
            return jsonify({"liters": latest_liters[0]})
        else:
            return jsonify({"liters": "No Data"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@views.route('/status', methods=['GET'])
@login_required
def get_status():
    # Initialize the latest reading variable
    latest_reading = None

    try:
        # Connect to PostgreSQL database
        connection = get_db_connection()
        if connection is None:
            raise Exception("Database connection failed")

        cursor = connection.cursor()

        # Query to fetch the last distance and status
        cursor.execute('SELECT remainingFuel, status FROM public."data" ORDER BY datetime DESC LIMIT 1;')
        latest_reading = cursor.fetchone()

    except Exception as e:
        flash(f"Database error: {str(e)}", category="error")
        latest_reading = None

    finally:
        if connection:
            connection.close()

    # Prepare data to return as JSON
    status = latest_reading[1] if latest_reading else None
    remainingFuel = latest_reading[0] if latest_reading else None

    return jsonify({"remainingFuel": remainingFuel, "status": status})


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
@login_required  # Ensure the user is logged in
def control_panel():
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query to fetch all rows from the "data" table
        cursor.execute('SELECT * FROM public."data";')
        data_rows = cursor.fetchall()  # Fetch all rows

        cursor.close()
        connection.close()

        # Render the controlPanel.html template with data and user passed to it
        return render_template('controlPanel.html', data_rows=data_rows, user=current_user)

    except Exception as e:
        # Return error response if something goes wrong
        return jsonify({'error': str(e)}), 500

def check_for_notifications():
    try:
        # Get PostgreSQL connection
        connection = get_db_connection()
        if connection is None:
            raise Exception("Failed to connect to the database.")

        cursor = connection.cursor()

        # Query to fetch the latest percentage and status
        query = 'SELECT remainingFuel, status FROM public."data" ORDER BY datetime DESC LIMIT 1;'
        cursor.execute(query)
        latest_reading = cursor.fetchone()

        if latest_reading:
            remainingFuel, status = latest_reading

            # Prepare notification details based on the status
            if status == 'high':
                # No notification for high status
                return None
            elif status == 'moderate':
                # Notification for moderate status
                message = f"Fuel supply is <span style='color:orange;'>{remainingFuel}%</span>. Fuel level: <span style='color:orange;'>Moderate</span>."
                return {
                    'message': message,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'icon_class': 'fa-exclamation-circle',  # Orange moderate level icon
                    'color': 'orange'  # Text color for moderate level
                }
            elif status == 'low':
                # Notification for low status
                message = f"Fuel supply is <span style='color:red;'>{remainingFuel}%</span>. Fuel level: <span style='color:red;'>Low</span>."
                return {
                    'message': message,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'icon_class': 'fa-exclamation-triangle',  # Red warning triangle icon
                    'color': 'red'  # Text color for low level
                }

        return None  # No notification if no reading is found

    except Exception as e:
        print(f"Error while checking notifications: {e}")
        return None

    finally:
        if connection:
            connection.close()

@views.route('/notifications', methods=['GET'])
def get_notifications():
    # Check for any notifications based on sensor data
    notification = check_for_notifications()
    if notification:
        return jsonify({'notification': notification}), 200
    else:
        return jsonify({'notification': None}), 200


@views.route('/distance', methods=['GET'])
@login_required
def get_distance():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()

            # Query to fetch the latest distance, liters, remainingFuel, percentage, status, and datetime
            query = "SELECT percentage, distance, liters, remainingFuel, status, datetime FROM public.\"data\" ORDER BY datetime DESC LIMIT 10"
            cursor.execute(query)
            readings = cursor.fetchall()

            if readings:
                # Format the readings into a list of dictionaries
                formatted_readings = [
                    {
                        'percentage': reading[0],
                        'distance': reading[1],
                        'liters': reading[2],
                        'remainingFuel': reading[3],
                        'status': reading[4],
                        'datetime': reading[5]
                    }
                    for reading in readings
                ]
                return jsonify({'readings': formatted_readings})
            else:
                return jsonify({'error': 'No data found'}), 404
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()


# Route to download the PDF with sensor data
@views.route('/download_pdf')
@login_required  # Ensure the user is logged in
def download_pdf():
    try:
        # Get database connection
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Unable to connect to the database'}), 500

        cursor = connection.cursor()

        # Query to fetch all rows from the "data" table
        cursor.execute('SELECT distance, status, datetime, duration, fuel_consumed, percentage FROM public."data";')
        data_rows = cursor.fetchall()

        cursor.close()
        connection.close()

        # Create a PDF in memory using SimpleDocTemplate and Table for better layout
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Create current date and time string
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare data for the table (Remove ID column)
        table_data = [
            ["Distance", "Status", "Date/Time", "Duration", "Fuel Consumed", "Percentage"]  # Updated Headers
        ]

        # Add rows of data to table
        for row in data_rows:
            table_data.append([str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5])])

        # Create a Table object
        table = Table(table_data)

        # Style the table (add borders, alignment, padding, etc.)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Table header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all content
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font style
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for header
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Background color for data rows
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid (borders) around the table
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Data font style
            ('FONTSIZE', (0, 0), (-1, -1), 10),  # Font size
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Align all text to the center
            ('TOPPADDING', (0, 0), (-1, -1), 8),  # Padding for cells
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))

        # Start building the PDF
        content = []

        # Add the table to the PDF content
        content.append(table)

        # Add the footer with the current date and time
        doc.build(content, onFirstPage=lambda canvas, doc: draw_footer(canvas, current_datetime), onLaterPages=lambda canvas, doc: draw_footer(canvas, current_datetime))

        # Move to the beginning of the buffer
        buffer.seek(0)

        # Serve the PDF file for download
        return send_file(buffer, as_attachment=True, download_name="sensor_data_report.pdf", mimetype='application/pdf')

    except Exception as e:
        # Handle errors gracefully
        return jsonify({'error': str(e)}), 500

# Function to draw the footer on each page (right side)
def draw_footer(canvas, current_datetime):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.black)
    
    # Adjust the position to ensure it stays within the margin and is aligned to the right
    x_position = 400  # Adjusted x position to fit text within page margins
    y_position = 15   # Set at the bottom of the page, but not overlapping the margin
    
    # Draw the footer text ensuring it's within page width
    footer_text = f"Data Report Generated on: {current_datetime}"
    canvas.drawString(x_position, y_position, footer_text)
    canvas.restoreState()

# Define the relative paths for the CSV file and the model
CSV_FILE_PATH = "data.csv"
MODEL_FILE_PATH = "gradient_boosting_pipeline.pkl"

# Function to generate forecast data
def generate_forecast_data(days=30, csv_file_path=None):
    try:
        if not csv_file_path or not os.path.exists(csv_file_path):
            print("CSV file not found!")
            return []

        # Check if the model file exists
        if not os.path.exists(MODEL_FILE_PATH):
            print("Model file not found!")
            return []

        # Load the trained model
        model = joblib.load(MODEL_FILE_PATH)
        print("Model loaded successfully.")

        # Load the latest data from the CSV file
        last_data = pd.read_csv(csv_file_path)
        last_data['datetime'] = pd.to_datetime(last_data['datetime'], errors='coerce')
        latest_row = last_data.iloc[-1]

        # Prepare features for forecasting
        current_datetime = latest_row['datetime'] + timedelta(days=1)
        current_duration = latest_row['duration']
        current_percentage = latest_row['percentage']

        # Initialize predictions list
        predictions = []

        # Generate forecasts for the specified number of days
        for day in range(days):
            feature_vector = pd.DataFrame({
                'timestamp': [current_datetime.timestamp()],
                'duration': [current_duration],
                'hour': [current_datetime.hour],
                'day_of_week': [current_datetime.dayofweek],
                'percentage': [current_percentage]
            })

            # Predict the next value
            predicted_value = model.predict(feature_vector)[0]
            predicted_value = int(round(predicted_value))

            # Append prediction to the list
            predictions.append({
                "date": current_datetime.strftime('%Y-%m-%d'),
                "prediction": predicted_value
            })

            # Update the current values for the next iteration
            current_datetime += timedelta(days=1)
            current_duration += 1
            # Update the percentage dynamically (custom logic, if required)
            current_percentage = max(0, min(100, current_percentage + 1))  # Example logic: Increment percentage, keep it between 0 and 100

        print("Forecast data generated successfully.")
        return predictions

    except Exception as e:
        print(f"Error generating forecast data: {e}")
        return []

# Flask Route for Forecast
@views.route('/forecast', methods=['GET'])
def forecast():
    try:
        # Load actual data
        if not os.path.exists(CSV_FILE_PATH):
            return jsonify({"error": "CSV file not found"})

        actual_data = pd.read_csv(CSV_FILE_PATH)
        actual_data['datetime'] = pd.to_datetime(actual_data['datetime'])
        
        # Aggregate to daily averages
        actual_data['date'] = actual_data['datetime'].dt.date
        daily_avg = actual_data.groupby('date').agg({'fuel_consumed': 'mean'}).reset_index()
        daily_avg = daily_avg.rename(columns={'date': 'datetime', 'fuel_consumed': 'value'})
        daily_avg['datetime'] = daily_avg['datetime'].astype(str)  # Convert back to string for JSON serialization

        # Generate forecast
        days = int(request.args.get('days', 30))
        forecast_data = generate_forecast_data(days=days, csv_file_path=CSV_FILE_PATH)

        return jsonify({
            "actual": daily_avg.to_dict(orient="records"),
            "forecast": forecast_data
        })

    except Exception as e:
        return jsonify({"error": str(e)})


# Control panel route
@views.route('/forecasting', methods=['GET', 'POST'])
@login_required
def forecasting():
    return render_template("forecasting.html", user=current_user)


# Reading Sensor route
@views.route('/reading_sensor', methods=['GET', 'POST'])
def reading_sensor():
    if request.method == 'POST':
        try:
            if request.content_type == "application/x-www-form-urlencoded":
                # Access form data
                distance = request.form.get('distance')
                status = request.form.get('status')
                duration = request.form.get('duration')
                fuel_consumed = request.form.get('fuel_consumed')
                percentage = request.form.get('percentage')
                liters = request.form.get('liters')  
                remainingFuel = request.form.get('remainingFuel')  # Get remaining fuel directly

                if not (liters and remainingFuel):
                    return jsonify({"error": "Missing liters or remainingFuel value"}), 400

            else:
                return jsonify({"error": "Unsupported Content-Type"}), 415

            # Save to database
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO public.\"data\" (distance, status, duration, fuel_consumed, percentage, liters, remainingFuel) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING datetime",
                (distance, status, duration, fuel_consumed, percentage, liters, remainingFuel)
            )
            datetime = cursor.fetchone()[0]  # Fetch the `datetime` value of the inserted record
            connection.commit()
            cursor.close()
            connection.close()

            # Append to CSV
            append_to_csv([distance, status, duration, fuel_consumed, percentage, liters, remainingFuel, datetime])

            return jsonify({"message": "Data saved successfully and added to CSV!"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        # Handle GET request
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM public."data" ORDER BY datetime DESC LIMIT 1;')
            latest_data = cursor.fetchone()
            cursor.close()
            connection.close()
            return render_template("reading_sensor.html", user=current_user, latest_data=latest_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
