from flask import Flask, redirect, url_for, session, request, render_template, flash
from mysql.connector import connect
from requests_oauthlib import OAuth1Session
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set the secret key from environment variables
app.secret_key = os.getenv('SECRET_KEY')  # Ensure this is set in your .env file

# Twitter OAuth credentials
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_CALLBACK_URL = 'http://localhost:5000/callback'

# MySQL database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'port': 3306,
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Helper function to connect to MySQL
def get_db_connection():
    return connect(**DB_CONFIG)

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Doctor login route
@app.route('/doctor/login')
def doctor_login():
    return render_template('doctor_login.html')

# Patient login route
@app.route('/patient/login')
def patient_login():
    return render_template('patient_login.html')

# Start Twitter OAuth flow
@app.route('/login/<role>')
def login(role):
    twitter = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET, callback_uri=TWITTER_CALLBACK_URL)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    fetch_response = twitter.fetch_request_token(request_token_url)
    session['oauth_token'] = fetch_response.get('oauth_token')
    session['oauth_token_secret'] = fetch_response.get('oauth_token_secret')
    session['role'] = role
    auth_url = f"https://api.twitter.com/oauth/authorize?oauth_token={fetch_response.get('oauth_token')}"
    return redirect(auth_url)



# Callback route after Twitter authorization
@app.route('/callback')
def callback():
    oauth_token = session.pop('oauth_token', None)
    oauth_token_secret = session.pop('oauth_token_secret', None)
    role = session.pop('role', None)
    
    if not oauth_token or not oauth_token_secret or not role:
        flash("Authorization failed. Please try again.", "danger")
        return redirect(url_for('home'))

    # Set up Twitter OAuth session
    twitter = OAuth1Session(
        TWITTER_API_KEY,
        client_secret=TWITTER_API_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=request.args.get('oauth_verifier')
    )
    
    try:
        # Get access token
        access_token_url = 'https://api.twitter.com/oauth/access_token'
        access_token_response = twitter.fetch_access_token(access_token_url)
        
        # Extract Twitter user data
        user_id = access_token_response.get('user_id')
        screen_name = access_token_response.get('screen_name')
        
        # Save user to database
        save_user_to_db(user_id, screen_name, role)
        
        # Set session data
        session['user_id'] = user_id
        session['role'] = role
        
        # Redirect based on role
        if role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
            
    except Exception as e:
        flash(f"Authentication error: {str(e)}", "danger")
        return redirect(url_for('home'))

# Save user data to MySQL
def save_user_to_db(user_id, screen_name, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, screen_name, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE screen_name = %s, role = %s
    ''', (user_id, screen_name, role, screen_name, role))
    conn.commit()
    cursor.close()
    conn.close()



# Doctor dashboard route
@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch doctor's name
    cursor.execute('SELECT screen_name FROM users WHERE user_id = %s', (session['user_id'],))
    doctor = cursor.fetchone()

    # Fetch appointments with patient profile picture for the doctor
    cursor.execute('''
        SELECT a.appointment_id, a.patient_id, a.appointment_date, u.profile_picture
        FROM appointments a
        LEFT JOIN users u ON a.patient_id = u.user_id
        WHERE a.doctor_id = %s
    ''', (session['user_id'],))
    
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('doctor_dashboard.html', doctor_name=doctor, appointments=appointments)

# Patient dashboard route
@app.route('/patient/dashboard')
def patient_dashboard():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE role = "doctor"')
    doctors = cursor.fetchall()
    cursor.execute('SELECT * FROM medical_records WHERE patient_id = %s', (session['user_id'],))
    medical_records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('patient_dashboard.html', doctors=doctors, medical_records=medical_records)

# Book appointment route
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('home'))
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (patient_id, doctor_id, appointment_date)
        VALUES (%s, %s, %s)
    ''', (session['user_id'], doctor_id, appointment_date))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Appointment booked successfully!', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/add_medical_record_form/<int:patient_id>')
def add_medical_record_form(patient_id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('home'))
    return render_template('add_medical_record.html', patient_id=patient_id)


# Add medical record route (for doctors)
import os
from flask import Flask, request, redirect, url_for, session, flash, render_template
from werkzeug.utils import secure_filename

@app.route('/add_medical_record', methods=['POST'])
def add_medical_record():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('home'))

    patient_id = request.form.get('patient_id')
    diagnosis = request.form.get('diagnosis')
    prescription = request.form.get('prescription')
    notes = request.form.get('notes')

    # Ensure connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # File handling - check if files exist before reading
    medical_image = request.files.get('medical_image')
    x_ray_image = request.files.get('x_ray_image')
    lab_report = request.files.get('lab_report')

    # Read files only if uploaded
    medical_image_data = medical_image.read() if medical_image and medical_image.filename else None
    x_ray_image_data = x_ray_image.read() if x_ray_image and x_ray_image.filename else None
    lab_report_data = lab_report.read() if lab_report and lab_report.filename else None

    # Insert into database
    cursor.execute('''
        INSERT INTO medical_records (patient_id, doctor_id, diagnosis, prescription, notes, image_data, x_ray_image, lab_report)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (patient_id, session['user_id'], diagnosis, prescription, notes, medical_image_data, x_ray_image_data, lab_report_data))

    conn.commit()
    cursor.close()
    conn.close()

    flash('Medical record added successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))




# @app.route('/get-image/<int:record_id>')
# def get_image(record_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT image_data FROM medical_records WHERE record_id = %s", (record_id,))
#     result = cursor.fetchone()
#     cursor.close()
#     conn.close()
#     if result and result[0]:
#         return send_file(io.BytesIO(result[0]), mimetype='image/jpeg')
#     return "Image not found", 404




from flask import Flask, request, redirect, url_for, session, flash, render_template, Response

@app.route('/medical_image/<string:image_type>/<int:record_id>')
def get_medical_image(image_type, record_id):
    if image_type not in ['image_data', 'x_ray_image', 'lab_report', 'profile_picture']:  
        return "Invalid file type", 400  

    conn = get_db_connection()
    cursor = conn.cursor()

    # Using safer SQL query formatting
    query = "SELECT {} FROM medical_records WHERE record_id = %s".format(image_type)
    cursor.execute(query, (record_id,))
    
    image_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if image_data and image_data[0]:
        return Response(image_data[0], mimetype='image/jpeg')  # Adjust MIME type if needed
    return "No file available", 404


from flask import Response

@app.route('/profile_picture/<int:patient_id>')
def get_profile_picture(patient_id):
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to fetch the profile picture for the given patient_id
    cursor.execute('''
        SELECT profile_picture 
        FROM users 
        WHERE user_id = %s
    ''', (patient_id,))
    
    profile_picture = cursor.fetchone()

    cursor.close()
    conn.close()

    if profile_picture and profile_picture[0]:
        return Response(profile_picture[0], mimetype='image/jpeg')
    return "No image available", 404


from flask import Response, send_file
import io

@app.route('/download_medical_image/<int:record_id>')
def download_medical_image(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_data FROM medical_records WHERE record_id = %s", (record_id,))
    image_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if image_data and image_data[0]:
        return send_file(io.BytesIO(image_data[0]), 
                         mimetype='image/jpeg',  # Adjust if storing PNG (e.g., 'image/png')
                         as_attachment=True, 
                         download_name=f"medical_record_{record_id}.jpg")
    return "No image available", 404


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)