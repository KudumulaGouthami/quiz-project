import streamlit as st
import sqlite3
import hashlib
import random
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Quiz Application",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database initialization
def init_db():
    conn = sqlite3.connect('quiz.db')
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

# Quiz questions
quiz_questions = [
    {
        "id": 1,
        "question": "What is the capital of France?",
        "options": ["Berlin", "London", "Paris", "Madrid"],
        "answer": 3
    },
    {
        "id": 2,
        "question": "Which number is a prime?",
        "options": ["4", "6", "7", "9"],
        "answer": 3
    },
    {
        "id": 3,
        "question": "Which language is used for web apps?",
        "options": ["Python", "HTML", "C++", "Java"],
        "answer": 2
    },
    {
        "id": 4,
        "question": "What is 5 + 3?",
        "options": ["6", "8", "7", "10"],
        "answer": 2
    },
    {
        "id": 5,
        "question": "What is the largest planet in our solar system?",
        "options": ["Earth", "Saturn", "Jupiter", "Mars"],
        "answer": 3
    }
]

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'quiz_start_time' not in st.session_state:
    st.session_state.quiz_start_time = None

# Authentication functions
def register_user(username, password, email):
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            (username, hash_password(password), email)
        )
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login_user(username, password):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?',
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    
    if user:
        return True, user
    else:
        return False, "Invalid username or password!"

# Page functions
def show_login():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                success, result = login_user(username, password)
                if success:
                    st.session_state.user_id = result['id']
                    st.session_state.username = result['username']
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result)
            else:
                st.error("Please fill in all fields")
    
    st.write("Don't have an account?")
    if st.button("Register here"):
        st.session_state.page = "register"
        st.rerun()

def show_register():
    st.title("📝 Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email (optional)")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
        
        if submit:
            if not username or not password:
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords don't match!")
            elif len(password) < 4:
                st.error("Password must be at least 4 characters!")
            else:
                success, message = register_user(username, password, email)
                if success:
                    st.success(message)
                    st.session_state.page = "login"
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
    
    st.write("Already have an account?")
    if st.button("Login here"):
        st.session_state.page = "login"
        st.rerun()

def show_dashboard():
    st.title(f"🎯 Welcome, {st.session_state.username}!")
    
    # User stats
    conn = get_db_connection()
    stats = conn.execute('''
        SELECT COUNT(*) as total_quizzes, 
               COALESCE(SUM(score), 0) as total_score,
               COALESCE(AVG(percentage), 0) as avg_percentage
        FROM quiz_results 
        WHERE user_id = ?
    ''', (st.session_state.user_id,)).fetchone()
    
    recent_results = conn.execute('''
        SELECT * FROM quiz_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    ''', (st.session_state.user_id,)).fetchall()
    conn.close()
    
    # Stats columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Quizzes", stats['total_quizzes'])
    with col2:
        st.metric("Average Score", f"{stats['avg_percentage']:.1f}%")
    with col3:
        st.metric("Total Points", stats['total_score'])
    
    # Actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎮 Start New Quiz", use_container_width=True):
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_start_time = time.time()
            st.rerun()
    
    with col2:
        if st.button("📊 View Results", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
    
    with col3:
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
    
    # Recent results
    if recent_results:
        st.subheader("Recent Quiz Results")
        for result in recent_results:
            with st.container():
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                with col1:
                    st.write(f"**{result['created_at'][:16]}**")
                with col2:
                    st.write(f"Score: {result['score']}/{result['total_questions']}")
                with col3:
                    st.write(f"Percentage: {result['percentage']:.1f}%")
                with col4:
                    st.write(f"Time: {result['time_taken']:.1f}s")
                st.divider()
    else:
        st.info("No quiz results yet. Start your first quiz!")
    
    # Logout
    st.sidebar.write("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.page = "login"
        st.rerun()

def show_quiz():
    st.title("📝 Quiz")
    
    if not st.session_state.quiz_started:
        st.info("Click the button below to start the quiz!")
        if st.button("Start Quiz"):
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_start_time = time.time()
            st.rerun()
        return
    
    # Timer
    elapsed_time = time.time() - st.session_state.quiz_start_time
    st.write(f"⏰ Time: {int(elapsed_time // 60)}m {int(elapsed_time % 60)}s")
    
    # Progress
    progress = (st.session_state.current_question + 1) / len(quiz_questions)
    st.progress(progress)
    st.write(f"Question {st.session_state.current_question + 1} of {len(quiz_questions)}")
    
    # Current question
    question = quiz_questions[st.session_state.current_question]
    
    st.subheader(f"Q{st.session_state.current_question + 1}: {question['question']}")
    
    # Options
    selected_option = st.radio(
        "Choose your answer:",
        question['options'],
        key=f"question_{question['id']}"
    )
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("⬅️ Previous"):
                st.session_state.user_answers[question['id']] = question['options'].index(selected_option) + 1
                st.session_state.current_question -= 1
                st.rerun()
    
    with col3:
        if st.session_state.current_question < len(quiz_questions) - 1:
            if st.button("Next ➡️"):
                st.session_state.user_answers[question['id']] = question['options'].index(selected_option) + 1
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("✅ Submit Quiz"):
                st.session_state.user_answers[question['id']] = question['options'].index(selected_option) + 1
                submit_quiz()
    
    # Back to dashboard
    if st.button("🏠 Back to Dashboard"):
        st.session_state.quiz_started = False
        st.session_state.page = "dashboard"
        st.rerun()

def submit_quiz():
    score = 0
    total_questions = len(quiz_questions)
    time_taken = time.time() - st.session_state.quiz_start_time
    
    for question in quiz_questions:
        if question['id'] in st.session_state.user_answers:
            if st.session_state.user_answers[question['id']] == question['answer']:
                score += 1
    
    percentage = (score / total_questions) * 100
    
    # Save result
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO quiz_results (user_id, score, total_questions, percentage, time_taken)
        VALUES (?, ?, ?, ?, ?)
    ''', (st.session_state.user_id, score, total_questions, percentage, time_taken))
    conn.commit()
    conn.close()
    
    # Show results
    st.session_state.quiz_started = False
    st.session_state.page = "quiz_results"
    st.session_state.quiz_score = score
    st.session_state.quiz_total = total_questions
    st.session_state.quiz_percentage = percentage
    st.session_state.quiz_time = time_taken
    st.rerun()

def show_quiz_results():
    st.title("🎉 Quiz Completed!")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Score", f"{st.session_state.quiz_score}/{st.session_state.quiz_total}")
    with col2:
        st.metric("Percentage", f"{st.session_state.quiz_percentage:.1f}%")
    with col3:
        st.metric("Time Taken", f"{st.session_state.quiz_time:.1f}s")
    with col4:
        if st.session_state.quiz_percentage >= 80:
            st.metric("Performance", "🎉 Excellent")
        elif st.session_state.quiz_percentage >= 60:
            st.metric("Performance", "👍 Good")
        else:
            st.metric("Performance", "💪 Keep Trying")
    
    st.balloons()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 View All Results", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
    with col2:
        if st.button("🎮 Take Another Quiz", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

def show_results():
    st.title("📊 My Results")
    
    conn = get_db_connection()
    results = conn.execute('''
        SELECT * FROM quiz_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (st.session_state.user_id,)).fetchall()
    conn.close()
    
    if results:
        for result in results:
            with st.container():
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                with col1:
                    st.write(f"**{result['created_at'][:16]}**")
                with col2:
                    st.write(f"Score: {result['score']}/{result['total_questions']}")
                with col3:
                    percentage = result['percentage']
                    color = "🟢" if percentage >= 80 else "🟡" if percentage >= 60 else "🔴"
                    st.write(f"{color} {percentage:.1f}%")
                with col4:
                    st.write(f"⏱️ {result['time_taken']:.1f}s")
                st.divider()
    else:
        st.info("No quiz results yet. Take your first quiz!")
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

def show_profile():
    st.title("👤 My Profile")
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?',
        (st.session_state.user_id,)
    ).fetchone()
    
    stats = conn.execute('''
        SELECT COUNT(*) as total_quizzes, 
               COALESCE(SUM(score), 0) as total_score,
               COALESCE(AVG(percentage), 0) as avg_percentage
        FROM quiz_results 
        WHERE user_id = ?
    ''', (st.session_state.user_id,)).fetchone()
    conn.close()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("User Information")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email'] or 'Not provided'}")
        st.write(f"**Member since:** {user['created_at'][:10]}")
        st.write(f"**User ID:** #{user['id']}")
    
    with col2:
        st.subheader("Quiz Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Quizzes", stats['total_quizzes'])
        with col2:
            st.metric("Average Score", f"{stats['avg_percentage']:.1f}%")
        with col3:
            st.metric("Total Points", stats['total_score'])
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

# Main app logic
def main():
    init_db()
    
    # Initialize page state
    if 'page' not in st.session_state:
        if st.session_state.user_id:
            st.session_state.page = "dashboard"
        else:
            st.session_state.page = "login"
    
    # Page routing
    if st.session_state.user_id is None:
        if st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "register":
            show_register()
    else:
        if st.session_state.page == "dashboard":
            show_dashboard()
        elif st.session_state.page == "quiz":
            show_quiz()
        elif st.session_state.page == "quiz_results":
            show_quiz_results()
        elif st.session_state.page == "results":
            show_results()
        elif st.session_state.page == "profile":
            show_profile()

if __name__ == "__main__":
    main()
