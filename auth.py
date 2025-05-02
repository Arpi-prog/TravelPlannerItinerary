from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from planner import suggest_destinations_node  # LangGraph destination suggestion node

auth_blueprint = Blueprint('auth', __name__)

USER_FILE = 'users.json'

def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, 'w') as f:
            json.dump({}, f)
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        flash("Error loading user data.", "error")
        return {}

def save_users(users):
    try:
        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=4)
    except IOError:
        flash("Error saving user data.", "error")

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username and password are required", "error")
        elif username in users and check_password_hash(users[username], password):
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for('auth.dashboard'))
        else:
            flash("Invalid username or password", "error")

    return render_template('login.html')

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username and password are required", "error")
        elif username in users:
            flash("Username already exists", "error")
        else:
            users[username] = generate_password_hash(password)
            save_users(users)
            flash("Registration successful! Please login", "success")
            return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_blueprint.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out", "info")
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('auth.login'))

    destination_suggestions = None

    if request.method == 'POST':
        interests = request.form.get('interests', '').strip()
        city = request.form.get('city', '').strip()
        budget = request.form.get('budget', 'moderate').strip()
        season = request.form.get('season', 'any').strip()

        if not city or not interests:
            flash("City and interests are required", "error")
        else:
            state = {
                "city": city,
                "interests": interests,
                "days": 7,  # Default duration
                "budget": budget,
                "season": season,
                "itinerary": "",
                "destination_suggestions": ""
            }

            result = suggest_destinations_node(state)
            destination_suggestions = result.get("destination_suggestions")

    return render_template('dashboard.html',
                           username=session['username'],
                           destination_suggestions=destination_suggestions)
