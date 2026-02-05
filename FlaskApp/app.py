# app.py (updated)
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash, jsonify
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(
    BASE_DIR, '..', 'heart_disease_data.csv'))
DB_PATH = os.path.join(BASE_DIR, 'heart_care.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['DATABASE'] = DB_PATH

# Initialize database


def init_db():
    if not os.path.exists(DB_PATH):
        from init_db import init_database
        init_database()

# Database connection helper


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Login required decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# Initialize default values
FEATURES = []
EXAMPLE = []
EXAMPLE_DICT = {}
training_data_accuracy = 0
test_data_accuracy = 0
report = {}
model = None

# Load data and train model on startup
try:
    heart_data = pd.read_csv(DATA_PATH)
    X = heart_data.drop(columns='target', axis=1)
    Y = heart_data['target']
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, stratify=Y, random_state=2)
    model = LogisticRegression(max_iter=500, solver='liblinear')
    model.fit(X_train, Y_train)

    training_data_accuracy = accuracy_score(model.predict(X_train), Y_train)
    test_data_accuracy = accuracy_score(model.predict(X_test), Y_test)

    y_pred = model.predict(X_test)
    report = classification_report(Y_test, y_pred, output_dict=True)

    FEATURES = X.columns.tolist()
    EXAMPLE = X.iloc[0].tolist()
    EXAMPLE_DICT = dict(zip(FEATURES, EXAMPLE))
    
    print("✓ Model loaded and trained successfully")

except Exception as e:
    print(f"⚠ Error loading data: {e}")
    print(f"  Data path: {DATA_PATH}")


@app.template_filter()
def percent(value, digits=1):
    try:
        return f"{value * 100:.{int(digits)}f}%"
    except Exception:
        return value

# Helper function to generate patient ID


def generate_patient_id():
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    import random
    random_num = random.randint(100, 999)
    return f"HC{timestamp}{random_num}"

# Home page (public)


@app.route('/')
def home():
    return render_template('home.html',
                           test_acc=test_data_accuracy,
                           train_acc=training_data_accuracy,
                           report=report)

# Login routes


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['email'] = user['email']

            # Update last login
            conn = get_db()
            conn.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            conn.close()

            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Dashboard (for logged-in staff)


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()

    # Get statistics
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_patients,
            SUM(CASE WHEN prediction_result = 1 THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN prediction_result = 0 THEN 1 ELSE 0 END) as low_risk
        FROM patients
        WHERE created_by = ?
    ''', (session['user_id'],)).fetchone()

    # Get recent patients
    recent_patients = conn.execute('''
        SELECT p.*, u.full_name as created_by_name 
        FROM patients p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.created_by = ?
        ORDER BY p.created_at DESC
        LIMIT 10
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return render_template('dashboard.html',
                           stats=stats,
                           recent_patients=recent_patients,
                           user_role=session.get('role'),
                           test_acc=test_data_accuracy,
                           train_acc=training_data_accuracy)

# Patient Management Routes


@app.route('/patients')
@login_required
def patients():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')

    conn = get_db()

    query = '''
        SELECT p.*, u.full_name as created_by_name 
        FROM patients p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.created_by = ?
    '''
    params = [session['user_id']]

    if search:
        query += ' AND (p.full_name LIKE ? OR p.patient_id LIKE ? OR p.contact_number LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])

    query += ' ORDER BY p.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    patients_data = conn.execute(query, params).fetchall()

    # Get total count for pagination
    count_query = 'SELECT COUNT(*) as total FROM patients WHERE created_by = ?'
    count_params = [session['user_id']]

    if search:
        count_query += ' AND (full_name LIKE ? OR patient_id LIKE ? OR contact_number LIKE ?)'
        count_params.extend([search_term, search_term, search_term])

    total = conn.execute(count_query, count_params).fetchone()['total']
    total_pages = (total + per_page - 1) // per_page

    conn.close()

    return render_template('patients.html',
                           patients=patients_data,
                           page=page,
                           total_pages=total_pages,
                           search=search)


@app.route('/patient/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    if request.method == 'POST':
        try:
            # Get form data
            patient_data = {
                'patient_id': generate_patient_id(),
                'full_name': request.form.get('full_name'),
                'age': int(request.form.get('age', 0)),
                'gender': request.form.get('gender'),
                'contact_number': request.form.get('contact_number'),
                'email': request.form.get('email'),
                'address': request.form.get('address'),

                # Medical parameters
                'cp': int(request.form.get('cp', 0)),
                'trestbps': int(request.form.get('trestbps', 0)),
                'chol': int(request.form.get('chol', 0)),
                'fbs': int(request.form.get('fbs', 0)),
                'restecg': int(request.form.get('restecg', 0)),
                'thalach': int(request.form.get('thalach', 0)),
                'exang': int(request.form.get('exang', 0)),
                'oldpeak': float(request.form.get('oldpeak', 0)),
                'slope': int(request.form.get('slope', 0)),
                'ca': int(request.form.get('ca', 0)),
                'thal': int(request.form.get('thal', 0)),

                'created_by': session['user_id']
            }

            # Make prediction
            features = [patient_data[col] for col in FEATURES]
            arr = np.array(features).reshape(1, -1)
            pred = int(model.predict(arr)[0])
            proba = model.predict_proba(arr)[0][1] if hasattr(
                model, 'predict_proba') else None

            patient_data['prediction_result'] = pred
            patient_data['prediction_probability'] = proba
            patient_data['prediction_notes'] = request.form.get(
                'prediction_notes', '')

            # Insert into database
            conn = get_db()
            cursor = conn.cursor()

            columns = ', '.join(patient_data.keys())
            placeholders = ', '.join(['?' for _ in patient_data])
            query = f'INSERT INTO patients ({columns}) VALUES ({placeholders})'

            cursor.execute(query, list(patient_data.values()))
            patient_id = cursor.lastrowid

            # Add to audit log
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, table_name, record_id, new_values)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], 'CREATE', 'patients', patient_id, json.dumps(patient_data)))

            conn.commit()
            conn.close()

            flash(
                f'Patient {patient_data["patient_id"]} created successfully!', 'success')
            return redirect(url_for('patient_detail', id=patient_id))

        except Exception as e:
            flash(f'Error creating patient: {str(e)}', 'danger')

    return render_template('patient_form.html', patient=None, features=FEATURES)


@app.route('/patient/<int:id>')
@login_required
def patient_detail(id):
    conn = get_db()
    patient = conn.execute('''
        SELECT p.*, u.full_name as created_by_name 
        FROM patients p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.id = ? AND p.created_by = ?
    ''', (id, session['user_id'])).fetchone()

    if not patient:
        flash('Patient not found or access denied.', 'danger')
        return redirect(url_for('patients'))

    conn.close()
    return render_template('patient_detail.html', patient=patient)


@app.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    conn = get_db()
    patient = conn.execute('''
        SELECT * FROM patients 
        WHERE id = ? AND created_by = ?
    ''', (id, session['user_id'])).fetchone()

    if not patient:
        flash('Patient not found or access denied.', 'danger')
        return redirect(url_for('patients'))

    if request.method == 'POST':
        try:
            # Get form data
            update_data = {
                'full_name': request.form.get('full_name'),
                'age': int(request.form.get('age', 0)),
                'gender': request.form.get('gender'),
                'contact_number': request.form.get('contact_number'),
                'email': request.form.get('email'),
                'address': request.form.get('address'),

                # Medical parameters
                'cp': int(request.form.get('cp', 0)),
                'trestbps': int(request.form.get('trestbps', 0)),
                'chol': int(request.form.get('chol', 0)),
                'fbs': int(request.form.get('fbs', 0)),
                'restecg': int(request.form.get('restecg', 0)),
                'thalach': int(request.form.get('thalach', 0)),
                'exang': int(request.form.get('exang', 0)),
                'oldpeak': float(request.form.get('oldpeak', 0)),
                'slope': int(request.form.get('slope', 0)),
                'ca': int(request.form.get('ca', 0)),
                'thal': int(request.form.get('thal', 0)),

                'prediction_notes': request.form.get('prediction_notes', ''),
                'updated_at': datetime.now().isoformat()
            }

            # Make new prediction if parameters changed
            features = [update_data[col] for col in FEATURES]
            arr = np.array(features).reshape(1, -1)
            pred = int(model.predict(arr)[0])
            proba = model.predict_proba(arr)[0][1] if hasattr(
                model, 'predict_proba') else None

            update_data['prediction_result'] = pred
            update_data['prediction_probability'] = proba

            # Update patient record
            set_clause = ', '.join(
                [f'{key} = ?' for key in update_data.keys()])
            query = f'UPDATE patients SET {set_clause} WHERE id = ?'

            cursor = conn.cursor()
            cursor.execute(query, list(update_data.values()) + [id])

            # Add to audit log
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], 'UPDATE', 'patients', id,
                  json.dumps(dict(patient)), json.dumps(update_data)))

            conn.commit()
            conn.close()

            flash('Patient updated successfully!', 'success')
            return redirect(url_for('patient_detail', id=id))

        except Exception as e:
            flash(f'Error updating patient: {str(e)}', 'danger')

    conn.close()
    return render_template('patient_form.html', patient=patient, features=FEATURES)


@app.route('/patient/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    conn = get_db()

    # Get patient data before deletion for audit log
    patient = conn.execute('SELECT * FROM patients WHERE id = ? AND created_by = ?',
                           (id, session['user_id'])).fetchone()

    if not patient:
        flash('Patient not found or access denied.', 'danger')
        return redirect(url_for('patients'))

    # Add to audit log
    conn.execute('''
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_values)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], 'DELETE', 'patients', id, json.dumps(dict(patient))))

    # Delete patient
    conn.execute('DELETE FROM patients WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients'))

# Public prediction route (no login required)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Prediction page - handles both form display and submission"""
    if request.method == 'POST':
        try:
            # Read form values
            values = []
            for f in FEATURES:
                val = request.form.get(f, '').strip()
                if not val:
                    # Fallback: support comma separated single input field
                    raw = request.form.get('raw_input', '')
                    parts = [p.strip()
                             for p in raw.split(',') if p.strip() != '']
                    if len(parts) == len(FEATURES):
                        values = [float(p) for p in parts]
                        break
                    else:
                        return render_template('predict.html',
                                               features=FEATURES,
                                               example=EXAMPLE_DICT,
                                               test_acc=test_data_accuracy,
                                               error=f'Please fill all fields or provide {len(FEATURES)} comma-separated values')
                values.append(float(val))

            arr = np.array(values).reshape(1, -1)
            pred = int(model.predict(arr)[0])
            proba = model.predict_proba(arr)[0][1] if hasattr(
                model, 'predict_proba') else None

            # Store result in session for display
            session['prediction_result'] = {
                'prediction': pred,
                'probability': proba,
                'values': values,
                'features': FEATURES
            }

            return redirect(url_for('predict'))

        except ValueError:
            return render_template('predict.html',
                                   features=FEATURES,
                                   example=EXAMPLE_DICT,
                                   test_acc=test_data_accuracy,
                                   error='Invalid input. Please enter numeric values only.')

    # GET request - show form
    prediction_result = session.pop('prediction_result', None)
    return render_template('predict.html',
                           features=FEATURES,
                           example=EXAMPLE_DICT,
                           test_acc=test_data_accuracy,
                           prediction_result=prediction_result)

# Admin routes


@app.route('/admin/users')
@admin_required
def manage_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users WHERE role = ? ORDER BY created_at DESC',
                         ('staff',)).fetchall()
    conn.close()
    return render_template('admin_users.html', users=users, DB_PATH=DB_PATH)


@app.route('/admin/user/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            full_name = request.form.get('full_name')
            email = request.form.get('email')

            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('new_user'))

            password_hash = generate_password_hash(password)

            conn = get_db()
            conn.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, full_name, email, 'staff'))

            conn.commit()
            conn.close()

            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('manage_users'))

        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'danger')

    return render_template('user_form.html', user=None)


@app.route('/admin/user/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()

    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            is_active = 1 if request.form.get('is_active') else 0

            # Update password if provided
            password = request.form.get('password')
            if password:
                password_hash = generate_password_hash(password)
                conn.execute('''
                    UPDATE users 
                    SET full_name = ?, email = ?, is_active = ?, password_hash = ?
                    WHERE id = ?
                ''', (full_name, email, is_active, password_hash, id))
            else:
                conn.execute('''
                    UPDATE users 
                    SET full_name = ?, email = ?, is_active = ?
                    WHERE id = ?
                ''', (full_name, email, is_active, id))

            conn.commit()
            conn.close()

            flash('User updated successfully!', 'success')
            return redirect(url_for('manage_users'))

        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'danger')

    conn.close()
    return render_template('user_form.html', user=user)


@app.route('/admin/user/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    if id == session.get('user_id'):
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('manage_users'))

    conn = get_db()

    # Check if user has created any patients
    patient_count = conn.execute('SELECT COUNT(*) as count FROM patients WHERE created_by = ?',
                                 (id,)).fetchone()['count']

    if patient_count > 0:
        flash(
            f'Cannot delete user. They have created {patient_count} patient records.', 'danger')
    else:
        conn.execute(
            'DELETE FROM users WHERE id = ? AND role = ?', (id, 'staff'))
        conn.commit()
        flash('User deleted successfully!', 'success')

    conn.close()
    return redirect(url_for('manage_users'))


@app.route('/admin/audit_log')
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db()
    logs = conn.execute('''
        SELECT al.*, u.username, u.full_name 
        FROM audit_log al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()

    total = conn.execute(
        'SELECT COUNT(*) as total FROM audit_log').fetchone()['total']
    total_pages = (total + per_page - 1) // per_page

    conn.close()
    return render_template('audit_log.html', logs=logs, page=page, total_pages=total_pages)

# Profile routes


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')

            conn = get_db()

            if current_password and new_password:
                # Verify current password
                user = conn.execute('SELECT password_hash FROM users WHERE id = ?',
                                    (session['user_id'],)).fetchone()

                if not check_password_hash(user['password_hash'], current_password):
                    flash('Current password is incorrect!', 'danger')
                    return redirect(url_for('profile'))

                # Update password
                new_password_hash = generate_password_hash(new_password)
                conn.execute('''
                    UPDATE users 
                    SET full_name = ?, email = ?, password_hash = ?
                    WHERE id = ?
                ''', (full_name, email, new_password_hash, session['user_id']))
            else:
                conn.execute('''
                    UPDATE users 
                    SET full_name = ?, email = ?
                    WHERE id = ?
                ''', (full_name, email, session['user_id']))

            conn.commit()
            conn.close()

            # Update session
            session['full_name'] = full_name
            session['email'] = email

            flash('Profile updated successfully!', 'success')

        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'danger')

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?',
                        (session['user_id'],)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)

# API endpoints for charts


@app.route('/api/patient_stats')
@login_required
def patient_stats():
    conn = get_db()

    # Daily patient count for last 7 days
    daily_stats = conn.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM patients
        WHERE created_by = ? AND created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', (session['user_id'],)).fetchall()

    # Risk distribution
    risk_dist = conn.execute('''
        SELECT 
            CASE 
                WHEN prediction_result = 1 THEN 'High Risk'
                ELSE 'Low Risk'
            END as risk_level,
            COUNT(*) as count
        FROM patients
        WHERE created_by = ?
        GROUP BY prediction_result
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return jsonify({
        'daily_stats': [dict(stat) for stat in daily_stats],
        'risk_distribution': [dict(dist) for dist in risk_dist]
    })

# Serve assets folder


@app.route('/assets/<path:filename>')
def assets(filename):
    assets_dir = os.path.join(BASE_DIR, 'assets')
    return send_from_directory(assets_dir, filename)


# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
