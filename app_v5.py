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

# Onboarding route
@app.route('/onboarding')
def onboarding():
    return render_template('onboarding.html')

# Start Twitter OAuth flow
@app.route('/login/<role>')
def login(role):
    # Validate role
    if role not in ['doctor', 'patient']:
        flash('Invalid role selected', 'error')
        return redirect(url_for('home'))
    
    # Store role in session for later use
    session['intended_role'] = role
    
    twitter = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET, callback_uri=TWITTER_CALLBACK_URL)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    fetch_response = twitter.fetch_request_token(request_token_url)
    session['oauth_token'] = fetch_response.get('oauth_token')
    session['oauth_token_secret'] = fetch_response.get('oauth_token_secret')
    auth_url = f"https://api.twitter.com/oauth/authorize?oauth_token={fetch_response.get('oauth_token')}"
    return redirect(auth_url)

# Callback route after Twitter authorization
@app.route('/callback')
def callback():
    # Retrieve stored OAuth and role information
    oauth_token = session.pop('oauth_token', None)
    oauth_token_secret = session.pop('oauth_token_secret', None)
    intended_role = session.pop('intended_role', None)
    
    if not oauth_token or not oauth_token_secret or not intended_role:
        flash('Authorization failed. Please try again.', 'error')
        return redirect(url_for('home'))

    twitter = OAuth1Session(
        TWITTER_API_KEY,
        client_secret=TWITTER_API_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=request.args.get('oauth_verifier')
    )
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    access_token_response = twitter.fetch_access_token(access_token_url)

    # Extract user details from Twitter response
    user_id = access_token_response.get('user_id')
    screen_name = access_token_response.get('screen_name')

    # Check if user exists in the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if user exists and has the correct role
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # User exists, check if role matches
        if existing_user['role'] == intended_role:
            # Log in the user
            session['user_id'] = user_id
            session['role'] = intended_role
            cursor.close()
            conn.close()
            
            # Redirect to appropriate dashboard
            return redirect(url_for('doctor_dashboard' if intended_role == 'doctor' else 'patient_dashboard'))
        else:
            # User exists but with a different role
            cursor.close()
            conn.close()
            flash('User already registered with a different role', 'error')
            return redirect(url_for('home'))
    
    # New user - insert into database
    try:
        cursor.execute('''
            INSERT INTO users (user_id, screen_name, role) 
            VALUES (%s, %s, %s)
        ''', (user_id, screen_name, intended_role))
        conn.commit()
        
        # Set session variables
        session['user_id'] = user_id
        session['role'] = intended_role
        
        cursor.close()
        conn.close()
        
        # Redirect to appropriate dashboard
        return redirect(url_for('doctor_dashboard' if intended_role == 'doctor' else 'patient_dashboard'))
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        flash('Registration failed. Please try again.', 'error')
        return redirect(url_for('home'))

# Doctor dashboard route
@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM appointments WHERE doctor_id = %s', (session['user_id'],))
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('doctor_dashboard.html', appointments=appointments)

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

# Add medical record route (for doctors)
@app.route('/add_medical_record', methods=['POST'])
def add_medical_record():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect(url_for('home'))
    patient_id = request.form.get('patient_id')
    diagnosis = request.form.get('diagnosis')
    prescription = request.form.get('prescription')
    notes = request.form.get('notes')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO medical_records (patient_id, doctor_id, diagnosis, prescription, notes)
        VALUES (%s, %s, %s, %s, %s)
    ''', (patient_id, session['user_id'], diagnosis, prescription, notes))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Medical record added successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)