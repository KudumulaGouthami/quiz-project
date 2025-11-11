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
    conn = sqlite3.connect('quiz.db', check_same_thread=False)
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
    conn = sqlite3.connect('quiz.db', check_same_thread=False)
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
if 'page' not in st.session_state:
    st.session_state.page = "login"  # Default page
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
    st.title("🔐 Login to Quiz App")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if username and password:
                success, result = login_user(username, password)
                if success:
                    st.session_state.user_id = result['id']
                    st.session_state.username = result['username']
                    st.session_state.page = "dashboard"  # IMPORTANT: Set page to dashboard
                    st.success("✅ Login successful! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {result}")
            else:
                st.error("⚠️ Please fill in all fields")
    
    st.markdown("---")
    st.write("Don't have an account?")
    if st.button("Register here", use_container_width=True):
        st.session_state.page = "register"
        st.rerun()

def show_register():
    st.title("📝 Create Account")
    
    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email (optional)", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Enter password (min 4 characters)")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        submit = st.form_submit_button("Register", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("⚠️ Please fill in all required fields")
            elif password != confirm_password:
                st.error("❌ Passwords don't match!")
            elif len(password) < 4:
                st.error("❌ Password must be at least 4 characters!")
            else:
                success, message = register_user(username, password, email)
                if success:
                    st.success(f"✅ {message} Redirecting to login...")
                    st.session_state.page = "login"  # Go to login after registration
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    st.markdown("---")
    st.write("Already have an account?")
    if st.button("Login here", use_container_width=True):
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
    st.subheader("📊 Your Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Quizzes", stats['total_quizzes'])
    with col2:
        st.metric("Average Score", f"{stats['avg_percentage']:.1f}%")
    with col3:
        st.metric("Total Points", stats['total_score'])
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎮 Start Quiz", use_container_width=True):
            st.session_state.page = "quiz"
            st.rerun()
    
    with col2:
        if st.button("📊 View Results", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
    
    with col3:
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
    
    with col4:
        if st.button("💬 Feedback", use_container_width=True):
            st.session_state.page = "feedback"
            st.rerun()
    
    # Recent results
    st.subheader("📈 Recent Quiz Results")
    if recent_results:
        for result in recent_results:
            with st.container():
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                with col1:
                    st.write(f"**{result['created_at'][:16]}**")
                with col2:
                    st.write(f"Score: **{result['score']}/{result['total_questions']}**")
                with col3:
                    percentage = result['percentage']
                    if percentage >= 80:
                        emoji = "🎉"
                    elif percentage >= 60:
                        emoji = "👍"
                    else:
                        emoji = "💪"
                    st.write(f"{emoji} **{percentage:.1f}%**")
                with col4:
                    st.write(f"⏱️ **{result['time_taken']:.1f}s**")
                st.divider()
    else:
        st.info("No quiz results yet. Start your first quiz from the Quick Actions above!")
    
    # Logout in sidebar
    st.sidebar.markdown("---")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.page = "login"
        st.rerun()

def show_quiz():
    st.title("📝 Quiz Challenge")
    
    if not st.session_state.quiz_started:
        st.info("Ready to test your knowledge? Click the button below to start the quiz!")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🎯 Start Quiz", use_container_width=True):
                st.session_state.quiz_started = True
                st.session_state.current_question = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_start_time = time.time()
                st.rerun()
        with col2:
            if st.button("🏠 Back to Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
        return
    
    # Timer and progress
    elapsed_time = time.time() - st.session_state.quiz_start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"⏰ **Time Elapsed:** {minutes}m {seconds}s")
    with col2:
        progress = (st.session_state.current_question + 1) / len(quiz_questions)
        st.progress(progress)
        st.write(f"**Question {st.session_state.current_question + 1} of {len(quiz_questions)}**")
    
    # Current question
    question = quiz_questions[st.session_state.current_question]
    
    st.subheader(f"Q{st.session_state.current_question + 1}: {question['question']}")
    
    # Options
    selected_option = st.radio(
        "Select your answer:",
        question['options'],
        key=f"question_{question['id']}",
        index=None
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                if selected_option:
                    st.session_state.user_answers[question['id']] = question['options'].index(selected_option) + 1
                st.session_state.current_question -= 1
                st.rerun()
    
    with col3:
        if st.session_state.current_question < len(quiz_questions) - 1:
            if st.button("Next ➡️", use_container_width=True, disabled=selected_option is None):
                st.session_state.user_answers[question['id']] = question['options'].index(selected_option) + 1
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("✅ Submit Quiz", use_container_width=True, disabled=selected_option is None):
                st.session_state.user_answers[question['id']] = question['options'].index(selected_option) + 1
                submit_quiz()
    
    # Back to dashboard
    st.markdown("---")
    if st.button("🏠 Back to Dashboard", use_container_width=True):
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
    
    # Store results in session state
    st.session_state.quiz_started = False
    st.session_state.quiz_score = score
    st.session_state.quiz_total = total_questions
    st.session_state.quiz_percentage = percentage
    st.session_state.quiz_time = time_taken
    st.session_state.page = "quiz_results"
    st.rerun()

def show_quiz_results():
    st.title("🎉 Quiz Completed!")
    
    st.balloons()
    
    # Results cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Score", f"{st.session_state.quiz_score}/{st.session_state.quiz_total}")
    with col2:
        st.metric("Percentage", f"{st.session_state.quiz_percentage:.1f}%")
    with col3:
        st.metric("Time Taken", f"{st.session_state.quiz_time:.1f}s")
    with col4:
        if st.session_state.quiz_percentage >= 80:
            performance = "🎉 Excellent"
            st.metric("Performance", performance)
        elif st.session_state.quiz_percentage >= 60:
            performance = "👍 Good"
            st.metric("Performance", performance)
        else:
            performance = "💪 Keep Trying"
            st.metric("Performance", performance)
    
    # Performance message
    if st.session_state.quiz_percentage == 100:
        st.success("🏆 Perfect score! You're a quiz master!")
    elif st.session_state.quiz_percentage >= 80:
        st.success("🎯 Excellent work! You really know your stuff!")
    elif st.session_state.quiz_percentage >= 60:
        st.info("👍 Good job! Keep practicing to improve!")
    else:
        st.warning("💪 Don't give up! Practice makes perfect!")
    
    # Action buttons
    st.markdown("---")
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
    st.title("📊 My Quiz Results")
    
    conn = get_db_connection()
    results = conn.execute('''
        SELECT * FROM quiz_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (st.session_state.user_id,)).fetchall()
    conn.close()
    
    if results:
        st.write(f"**Total attempts:** {len(results)}")
        
        for i, result in enumerate(results):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
                with col1:
                    st.write(f"**Attempt #{i+1}** - {result['created_at'][:16]}")
                with col2:
                    st.write(f"**{result['score']}/{result['total_questions']}**")
                with col3:
                    percentage = result['percentage']
                    if percentage >= 80:
                        color = "🟢"
                    elif percentage >= 60:
                        color = "🟡"
                    else:
                        color = "🔴"
                    st.write(f"{color} **{percentage:.1f}%**")
                with col4:
                    st.write(f"⏱️ **{result['time_taken']:.1f}s**")
                with col5:
                    if percentage >= 80:
                        st.write("🎉 Excellent")
                    elif percentage >= 60:
                        st.write("👍 Good")
                    else:
                        st.write("💪 Practice")
                st.divider()
    else:
        st.info("No quiz results yet. Take your first quiz from the dashboard!")
    
    if st.button("🏠 Back to Dashboard", use_container_width=True):
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
        st.subheader("👤 User Information")
        st.info(f"""
        **Username:** {user['username']}  
        **Email:** {user['email'] or 'Not provided'}  
        **Member since:** {user['created_at'][:10]}  
        **User ID:** #{user['id']}
        """)
    
    with col2:
        st.subheader("📈 Quiz Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Quizzes", stats['total_quizzes'])
        with col2:
            st.metric("Average Score", f"{stats['avg_percentage']:.1f}%")
        with col3:
            st.metric("Total Points", stats['total_score'])
        
        # Performance indicator
        st.subheader("🎯 Performance Level")
        avg_score = stats['avg_percentage']
        if avg_score >= 80:
            st.success("🏆 Quiz Master - Excellent performance!")
        elif avg_score >= 60:
            st.info("🎯 Pro Learner - Good job!")
        elif avg_score > 0:
            st.warning("🚀 Rising Star - Keep practicing!")
        else:
            st.info("🌟 New Explorer - Start your first quiz!")
    
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

def show_feedback():
    st.title("💬 Feedback")
    
    st.info("We value your feedback! Please let us know how we can improve your quiz experience.")
    
    with st.form("feedback_form"):
        rating = st.slider("How would you rate our quiz application?", 1, 5, 3)
        comments = st.text_area("Your comments or suggestions:", placeholder="What did you like? What can we improve?")
        
        if st.form_submit_button("Submit Feedback", use_container_width=True):
            st.success("Thank you for your feedback! We appreciate your input.")
            time.sleep(2)
            st.session_state.page = "dashboard"
            st.rerun()
    
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

# Main app logic
def main():
    # Initialize database
    init_db()
    
    # Debug info (remove in production)
    st.sidebar.markdown("---")
    st.sidebar.write("**Debug Info:**")
    st.sidebar.write(f"Page: {st.session_state.page}")
    st.sidebar.write(f"User: {st.session_state.username}")
    
    # Page routing - FIXED: This ensures proper page display
    if st.session_state.user_id is None:
        # User not logged in
        if st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "register":
            show_register()
        else:
            # Default to login if somehow on wrong page
            st.session_state.page = "login"
            show_login()
    else:
        # User is logged in
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
        elif st.session_state.page == "feedback":
            show_feedback()
        else:
            # Default to dashboard if page not recognized
            st.session_state.page = "dashboard"
            show_dashboard()

if __name__ == "__main__":
    main()
