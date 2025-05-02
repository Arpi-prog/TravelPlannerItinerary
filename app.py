from flask import Flask, render_template, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from planner import generate_itinerary_node, suggest_destinations_node  # LangGraph node functions

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For production, use a fixed secret key

USER_FILE = 'users.json'


def load_users():
    try:
        if not os.path.exists(USER_FILE):
            with open(USER_FILE, 'w') as f:
                json.dump({}, f)
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        flash("Error loading user data. Please try again.", "error")
        return {}


def save_users(users):
    try:
        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=4)
    except IOError:
        flash("Error saving user data. Please try again.", "error")


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('login'))  # fixed blueprint reference

    itinerary = None
    destination_suggestions = None

    if request.method == 'POST':
        city = request.form.get('city', '').strip()
        interests = request.form.get('interests', '').strip()
        days_input = request.form.get('days', '1').strip()

        try:
            days = int(days_input)
            days = max(1, min(days, 30))
        except ValueError:
            flash("Please enter a valid number of days (1-30)", "error")
            return render_template('dashboard.html', username=session['username'], itinerary=None, destination_suggestions=None)

        if not city or not interests:
            flash("City and interests are required", "error")
        else:
            itinerary_data = generate_itinerary_node({
                "city": city,
                "interests": interests,
                "days": days
            })
            itinerary = itinerary_data.get("itinerary", "").strip()
            itinerary = itinerary.replace('\n', '<br>')

            destination_data = suggest_destinations_node({
                "city": city,
                "interests": interests,
                "days": days
            })
            destination_suggestions = destination_data.get("destination_suggestions", [])

    return render_template('dashboard.html',
                           username=session['username'],
                           itinerary=itinerary,
                           destination_suggestions=destination_suggestions)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username and password required", "error")
        elif username in users and check_password_hash(users[username], password):
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "error")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username and password required", "error")
        elif username in users:
            flash("Username already exists", "error")
        else:
            users[username] = generate_password_hash(password)
            save_users(users)
            flash("Registration successful! Please login", "success")
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out", "info")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
