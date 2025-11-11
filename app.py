from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import random
from datetime import datetime

app = Flask(_name_)
app.secret_key = 'quiz_app_secret_key_123'
app.config['DATABASE'] = 'quiz.db'

# Database initialization
def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            total_questions INTEGER,
            percentage REAL,
            time_taken REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rating INTEGER,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Quiz questions
quiz_questions = [
    {
        "id": 1,
        "question": "What is the capital of France?",
        "options": ["Berlin", "London", "Paris", "Madrid"],
        "answer": 3,
        "points": 1
    },
    {
        "id": 2,
        "question": "Which number is a prime?",
        "options": ["4", "6", "7", "9"],
        "answer": 3,
        "points": 1
    },
    {
        "id": 3,
        "question": "Which language is used for web apps?",
        "options": ["Python", "HTML", "C++", "Java"],
        "answer": 2,
        "points": 1
    },
    {
        "id": 4,
        "question": "What is 5 + 3?",
        "options": ["6", "8", "7", "10"],
        "answer": 2,
        "points": 1
    },
    {
        "id": 5,
        "question": "What is the largest planet in our solar system?",
        "options": ["Earth", "Saturn", "Jupiter", "Mars"],
        "answer": 3,
        "points": 1
    }
]

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form.get('email', '')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 4:
            flash('Password must be at least 4 characters!', 'error')
            return render_template('register.html')
        
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                (username, hash_password(password), email)
            )
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get user stats
    user_stats = conn.execute('''
        SELECT COUNT(*) as total_quizzes, 
               COALESCE(SUM(score), 0) as total_score,
               COALESCE(AVG(percentage), 0) as avg_percentage
        FROM quiz_results 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    # Get recent results
    recent_results = conn.execute('''
        SELECT * FROM quiz_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         stats=user_stats, 
                         recent_results=recent_results)

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    random.shuffle(quiz_questions)
    return render_template('quiz.html', questions=quiz_questions)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    user_answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)
    
    score = 0
    total_questions = len(quiz_questions)
    total_points = 0
    
    # Calculate score
    for question in quiz_questions:
        q_id = str(question['id'])
        if q_id in user_answers and int(user_answers[q_id]) == question['answer']:
            score += 1
            total_points += question['points']
    
    percentage = (score / total_questions) * 100
    
    # Save result to database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO quiz_results (user_id, score, total_questions, percentage, time_taken)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], score, total_questions, percentage, time_taken))
    conn.commit()
    conn.close()
    
    return jsonify({
        'score': score,
        'total_questions': total_questions,
        'percentage': round(percentage, 2),
        'time_taken': time_taken,
        'total_points': total_points
    })

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user_results = conn.execute('''
        SELECT * FROM quiz_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('results.html', results=user_results)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        rating = request.form['rating']
        comments = request.form['comments']
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO feedback (user_id, rating, comments) VALUES (?, ?, ?)',
            (session['user_id'], rating, comments)
        )
        conn.commit()
        conn.close()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('feedback.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    
    user_stats = conn.execute('''
        SELECT COUNT(*) as total_quizzes, 
               COALESCE(SUM(score), 0) as total_score,
               COALESCE(AVG(percentage), 0) as avg_percentage
        FROM quiz_results 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()
    
    conn.close()
    
    return render_template('profile.html', user=user, stats=user_stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

if _name_ == '_main_':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)