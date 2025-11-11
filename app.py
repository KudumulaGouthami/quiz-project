import streamlit as st
import sqlite3
import hashlib
import random
import time
from datetime import datetime
import base64

# Page configuration
st.set_page_config(
    page_title="QuizMaster Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Background image function
def set_background():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .main-header {
            text-align: center;
            color: white;
            padding: 2rem;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            margin-bottom: 2rem;
        }
        .quiz-card {
            background: rgba(255,255,255,0.95);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        .category-card {
            background: rgba(255,255,255,0.9);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.3s;
            border: 2px solid transparent;
        }
        .category-card:hover {
            transform: translateY(-5px);
            border-color: #667eea;
        }
        .result-correct {
            background: rgba(40, 167, 69, 0.1);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            margin: 0.5rem 0;
        }
        .result-wrong {
            background: rgba(220, 53, 69, 0.1);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #dc3545;
            margin: 0.5rem 0;
        }
        .animated-header {
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        </style>
        """,
        unsafe_allow_html=True
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
            category TEXT,
            difficulty TEXT,
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

# Enhanced quiz questions with categories and difficulties
quiz_data = {
    "Mathematics": {
        "Easy": [
            {
                "id": 1,
                "question": "What is 15 + 27?",
                "options": ["40", "42", "32", "38"],
                "answer": 2,
                "explanation": "15 + 27 = 42"
            },
            {
                "id": 2,
                "question": "What is 8 × 7?",
                "options": ["54", "56", "64", "48"],
                "answer": 2,
                "explanation": "8 × 7 = 56"
            },
            {
                "id": 3,
                "question": "What is 144 ÷ 12?",
                "options": ["10", "11", "12", "13"],
                "answer": 3,
                "explanation": "144 ÷ 12 = 12"
            }
        ],
        "Medium": [
            {
                "id": 4,
                "question": "Solve: 3² + 4² = ?",
                "options": ["12", "25", "7", "49"],
                "answer": 2,
                "explanation": "3² = 9, 4² = 16, 9 + 16 = 25"
            },
            {
                "id": 5,
                "question": "What is 15% of 200?",
                "options": ["15", "30", "25", "20"],
                "answer": 2,
                "explanation": "15% of 200 = 0.15 × 200 = 30"
            },
            {
                "id": 6,
                "question": "If x + 5 = 12, what is x?",
                "options": ["5", "6", "7", "8"],
                "answer": 3,
                "explanation": "x + 5 = 12 → x = 12 - 5 = 7"
            }
        ],
        "Hard": [
            {
                "id": 7,
                "question": "What is the value of π (pi) to two decimal places?",
                "options": ["3.14", "3.16", "3.12", "3.18"],
                "answer": 1,
                "explanation": "π ≈ 3.14159, so to two decimal places it's 3.14"
            },
            {
                "id": 8,
                "question": "Solve: 2x² - 8 = 0",
                "options": ["x = ±1", "x = ±2", "x = ±3", "x = ±4"],
                "answer": 2,
                "explanation": "2x² - 8 = 0 → 2x² = 8 → x² = 4 → x = ±2"
            },
            {
                "id": 9,
                "question": "What is the area of a circle with radius 7?",
                "options": ["49π", "14π", "28π", "7π"],
                "answer": 1,
                "explanation": "Area = πr² = π × 7² = 49π"
            }
        ]
    },
    "Science": {
        "Easy": [
            {
                "id": 10,
                "question": "What planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "answer": 2,
                "explanation": "Mars is called the Red Planet due to its reddish appearance"
            },
            {
                "id": 11,
                "question": "What gas do plants absorb from the atmosphere?",
                "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
                "answer": 2,
                "explanation": "Plants absorb CO₂ for photosynthesis"
            },
            {
                "id": 12,
                "question": "What is H₂O commonly known as?",
                "options": ["Oxygen", "Hydrogen", "Water", "Salt"],
                "answer": 3,
                "explanation": "H₂O is the chemical formula for water"
            }
        ],
        "Medium": [
            {
                "id": 13,
                "question": "What is the chemical symbol for gold?",
                "options": ["Go", "Gd", "Au", "Ag"],
                "answer": 3,
                "explanation": "Au is the chemical symbol for gold (from Latin 'aurum')"
            },
            {
                "id": 14,
                "question": "How many bones are in the human body?",
                "options": ["196", "206", "216", "226"],
                "answer": 2,
                "explanation": "An adult human has 206 bones"
            },
            {
                "id": 15,
                "question": "What is the speed of light in vacuum?",
                "options": ["299,792,458 m/s", "300,000,000 m/s", "299,792,459 m/s", "299,792,457 m/s"],
                "answer": 1,
                "explanation": "The speed of light in vacuum is exactly 299,792,458 m/s"
            }
        ],
        "Hard": [
            {
                "id": 16,
                "question": "What is the atomic number of carbon?",
                "options": ["4", "6", "8", "10"],
                "answer": 2,
                "explanation": "Carbon has atomic number 6"
            },
            {
                "id": 17,
                "question": "Which scientist proposed the theory of relativity?",
                "options": ["Newton", "Einstein", "Galileo", "Hawking"],
                "answer": 2,
                "explanation": "Albert Einstein proposed the theory of relativity"
            },
            {
                "id": 18,
                "question": "What is the main gas found in the Sun?",
                "options": ["Oxygen", "Hydrogen", "Helium", "Nitrogen"],
                "answer": 2,
                "explanation": "The Sun is primarily composed of hydrogen (about 74%)"
            }
        ]
    },
    "English": {
        "Easy": [
            {
                "id": 19,
                "question": "Which word is a noun?",
                "options": ["Run", "Beautiful", "Computer", "Quickly"],
                "answer": 3,
                "explanation": "'Computer' is a noun (a person, place, or thing)"
            },
            {
                "id": 20,
                "question": "What is the past tense of 'go'?",
                "options": ["Goed", "Went", "Gone", "Going"],
                "answer": 2,
                "explanation": "The past tense of 'go' is 'went'"
            },
            {
                "id": 21,
                "question": "Which sentence is correct?",
                "options": ["She don't like apples", "She doesn't likes apples", "She doesn't like apples", "She don't likes apples"],
                "answer": 3,
                "explanation": "'She doesn't like apples' is grammatically correct"
            }
        ],
        "Medium": [
            {
                "id": 22,
                "question": "What is a synonym for 'happy'?",
                "options": ["Sad", "Joyful", "Angry", "Tired"],
                "answer": 2,
                "explanation": "'Joyful' is a synonym for 'happy'"
            },
            {
                "id": 23,
                "question": "Identify the metaphor:",
                "options": ["She sings like a bird", "He is a lion in battle", "The wind howled", "I'm as hungry as a bear"],
                "answer": 2,
                "explanation": "'He is a lion in battle' is a metaphor (direct comparison)"
            },
            {
                "id": 24,
                "question": "What is the plural of 'child'?",
                "options": ["Childs", "Children", "Childes", "Childern"],
                "answer": 2,
                "explanation": "The plural of 'child' is 'children'"
            }
        ],
        "Hard": [
            {
                "id": 25,
                "question": "What literary device is: 'The stars danced playfully in the moonlit sky'?",
                "options": ["Simile", "Metaphor", "Personification", "Hyperbole"],
                "answer": 3,
                "explanation": "This is personification - giving human qualities to stars"
            },
            {
                "id": 26,
                "question": "Which word means 'fear of heights'?",
                "options": ["Claustrophobia", "Arachnophobia", "Acrophobia", "Agoraphobia"],
                "answer": 3,
                "explanation": "Acrophobia is the fear of heights"
            },
            {
                "id": 27,
                "question": "What is the Oxford comma?",
                "options": ["A comma after Oxford", "A comma before 'and' in a list", "A comma at sentence end", "A comma in dates"],
                "answer": 2,
                "explanation": "The Oxford comma is used before 'and' in a list (e.g., red, white, and blue)"
            }
        ]
    },
    "General Knowledge": {
        "Easy": [
            {
                "id": 28,
                "question": "What is the capital of Japan?",
                "options": ["Seoul", "Beijing", "Tokyo", "Bangkok"],
                "answer": 3,
                "explanation": "Tokyo is the capital of Japan"
            },
            {
                "id": 29,
                "question": "How many continents are there?",
                "options": ["5", "6", "7", "8"],
                "answer": 3,
                "explanation": "There are 7 continents: Asia, Africa, North America, South America, Antarctica, Europe, Australia"
            },
            {
                "id": 30,
                "question": "Who painted the Mona Lisa?",
                "options": ["Van Gogh", "Picasso", "Da Vinci", "Monet"],
                "answer": 3,
                "explanation": "Leonardo da Vinci painted the Mona Lisa"
            }
        ],
        "Medium": [
            {
                "id": 31,
                "question": "What year did World War II end?",
                "options": ["1944", "1945", "1946", "1947"],
                "answer": 2,
                "explanation": "World War II ended in 1945"
            },
            {
                "id": 32,
                "question": "Which planet has the most moons?",
                "options": ["Jupiter", "Saturn", "Uranus", "Neptune"],
                "answer": 2,
                "explanation": "Saturn has the most moons (over 140 confirmed)"
            },
            {
                "id": 33,
                "question": "What is the largest ocean on Earth?",
                "options": ["Atlantic", "Indian", "Arctic", "Pacific"],
                "answer": 4,
                "explanation": "The Pacific Ocean is the largest ocean"
            }
        ],
        "Hard": [
            {
                "id": 34,
                "question": "Who wrote '1984'?",
                "options": ["George Orwell", "Aldous Huxley", "Ray Bradbury", "H.G. Wells"],
                "answer": 1,
                "explanation": "George Orwell wrote '1984'"
            },
            {
                "id": 35,
                "question": "What is the chemical formula for table salt?",
                "options": ["NaCl", "HCl", "H2O", "CO2"],
                "answer": 1,
                "explanation": "Table salt is sodium chloride (NaCl)"
            },
            {
                "id": 36,
                "question": "Which element has the highest melting point?",
                "options": ["Tungsten", "Iron", "Gold", "Carbon"],
                "answer": 4,
                "explanation": "Carbon (as graphite) has the highest melting point at about 3,700°C"
            }
        ]
    }
}

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'quiz_start_time' not in st.session_state:
    st.session_state.quiz_start_time = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'selected_difficulty' not in st.session_state:
    st.session_state.selected_difficulty = None
if 'current_questions' not in st.session_state:
    st.session_state.current_questions = []

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
    set_background()
    st.markdown('<div class="main-header"><h1 class="animated-header">🎯 QuizMaster Pro</h1><p>Test your knowledge across multiple categories!</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
            st.subheader("🔐 Login")
            
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if submit:
                    if username and password:
                        success, result = login_user(username, password)
                        if success:
                            st.session_state.user_id = result['id']
                            st.session_state.username = result['username']
                            st.session_state.page = "dashboard"
                            st.success("✅ Login successful! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                    else:
                        st.error("⚠️ Please fill in all fields")
            
            st.markdown("---")
            st.write("Don't have an account?")
            if st.button("📝 Register here", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def show_register():
    set_background()
    st.markdown('<div class="main-header"><h1>🎯 QuizMaster Pro</h1><p>Join our learning community!</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
            st.subheader("📝 Create Account")
            
            with st.form("register_form"):
                username = st.text_input("👤 Username", placeholder="Choose a username")
                email = st.text_input("📧 Email (optional)", placeholder="your@email.com")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter password (min 4 characters)")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
                submit = st.form_submit_button("🎉 Register", use_container_width=True)
                
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
                            st.session_state.page = "login"
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            st.markdown("---")
            st.write("Already have an account?")
            if st.button("🔐 Login here", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    set_background()
    st.markdown(f'<div class="main-header"><h1>🎯 Welcome, {st.session_state.username}!</h1><p>Ready to challenge yourself?</p></div>', unsafe_allow_html=True)
    
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
    st.subheader("📊 Your Learning Journey")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Quizzes", stats['total_quizzes'])
    with col2:
        st.metric("Average Score", f"{stats['avg_percentage']:.1f}%")
    with col3:
        st.metric("Total Points", stats['total_score'])
    
    # Quick Actions
    st.subheader("🚀 Start New Quiz")
    
    # Category selection
    st.write("### 🎯 Choose Your Challenge")
    categories = list(quiz_data.keys())
    cols = st.columns(len(categories))
    
    for i, category in enumerate(categories):
        with cols[i]:
            emoji = {"Mathematics": "🔢", "Science": "🔬", "English": "📚", "General Knowledge": "🌍"}[category]
            if st.button(f"{emoji}\n\n**{category}**", use_container_width=True, key=f"cat_{category}"):
                st.session_state.selected_category = category
                st.session_state.page = "select_difficulty"
                st.rerun()
    
    # Recent results
    st.subheader("📈 Recent Performance")
    if recent_results:
        for result in recent_results:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
                with col1:
                    st.write(f"**{result['category']}** - {result['difficulty']}")
                    st.write(f"*{result['created_at'][:16]}*")
                with col2:
                    st.write(f"**{result['score']}/{result['total_questions']}**")
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
                with col5:
                    if st.button("📊 Details", key=f"details_{result['id']}"):
                        st.session_state.view_result_id = result['id']
                        st.session_state.page = "detailed_results"
                        st.rerun()
                st.divider()
    else:
        st.info("🌟 No quiz results yet. Start your first quiz above!")
    
    # Logout
    st.sidebar.markdown("---")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.page = "login"
        st.rerun()

def show_difficulty_selection():
    set_background()
    st.markdown(f'<div class="main-header"><h1>🎯 {st.session_state.selected_category}</h1><p>Choose your difficulty level!</p></div>', unsafe_allow_html=True)
    
    difficulties = ["Easy", "Medium", "Hard"]
    cols = st.columns(3)
    
    difficulty_info = {
        "Easy": {"emoji": "😊", "desc": "Great for beginners!"},
        "Medium": {"emoji": "😎", "desc": "Perfect challenge!"},
        "Hard": {"emoji": "🔥", "desc": "Expert level!"}
    }
    
    for i, difficulty in enumerate(difficulties):
        with cols[i]:
            info = difficulty_info[difficulty]
            if st.button(f"{info['emoji']}\n\n**{difficulty}**\n\n{info['desc']}", use_container_width=True, key=f"diff_{difficulty}"):
                st.session_state.selected_difficulty = difficulty
                st.session_state.quiz_started = True
                st.session_state.current_question = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_start_time = time.time()
                st.session_state.current_questions = quiz_data[st.session_state.selected_category][difficulty]
                st.session_state.page = "quiz"
                st.rerun()
    
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

def show_quiz():
    set_background()
    
    if not st.session_state.quiz_started:
        st.session_state.page = "dashboard"
        st.rerun()
        return
    
    # Header
    st.markdown(f'''
    <div class="main-header">
        <h1>🎯 {st.session_state.selected_category} - {st.session_state.selected_difficulty}</h1>
        <p>Test your knowledge!</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Timer and progress
    elapsed_time = time.time() - st.session_state.quiz_start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"⏰ **Time Elapsed:** {minutes}m {seconds}s")
    with col2:
        progress = (st.session_state.current_question + 1) / len(st.session_state.current_questions)
        st.progress(progress)
        st.write(f"**Question {st.session_state.current_question + 1} of {len(st.session_state.current_questions)}**")
    
    # Current question
    question = st.session_state.current_questions[st.session_state.current_question]
    
    with st.container():
        st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
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
                        st.session_state.user_answers[question['id']] = {
                            'selected': question['options'].index(selected_option) + 1,
                            'correct': question['answer']
                        }
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col3:
            if st.session_state.current_question < len(st.session_state.current_questions) - 1:
                if st.button("Next ➡️", use_container_width=True, disabled=selected_option is None):
                    st.session_state.user_answers[question['id']] = {
                        'selected': question['options'].index(selected_option) + 1,
                        'correct': question['answer']
                    }
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("✅ Submit Quiz", use_container_width=True, disabled=selected_option is None):
                    st.session_state.user_answers[question['id']] = {
                        'selected': question['options'].index(selected_option) + 1,
                        'correct': question['answer']
                    }
                    submit_quiz()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Back to dashboard
    st.markdown("---")
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.session_state.quiz_started = False
        st.session_state.page = "dashboard"
        st.rerun()

def submit_quiz():
    score = 0
    total_questions = len(st.session_state.current_questions)
    time_taken = time.time() - st.session_state.quiz_start_time
    
    # Calculate score and prepare detailed results
    detailed_results = []
    for question in st.session_state.current_questions:
        q_id = question['id']
        if q_id in st.session_state.user_answers:
            user_answer = st.session_state.user_answers[q_id]
            is_correct = user_answer['selected'] == question['answer']
            if is_correct:
                score += 1
            
            detailed_results.append({
                'question': question['question'],
                'options': question['options'],
                'user_answer': user_answer['selected'],
                'correct_answer': question['answer'],
                'explanation': question['explanation'],
                'is_correct': is_correct
            })
    
    percentage = (score / total_questions) * 100
    
    # Save result
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO quiz_results (user_id, category, difficulty, score, total_questions, percentage, time_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (st.session_state.user_id, st.session_state.selected_category, st.session_state.selected_difficulty, 
          score, total_questions, percentage, time_taken))
    
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Store results in session state
    st.session_state.quiz_started = False
    st.session_state.quiz_score = score
    st.session_state.quiz_total = total_questions
    st.session_state.quiz_percentage = percentage
    st.session_state.quiz_time = time_taken
    st.session_state.detailed_results = detailed_results
    st.session_state.result_id = result_id
    st.session_state.page = "quiz_results"
    st.rerun()

def show_quiz_results():
    set_background()
    st.markdown('<div class="main-header"><h1>🎉 Quiz Completed!</h1><p>Great job completing the challenge!</p></div>', unsafe_allow_html=True)
    
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
        elif st.session_state.quiz_percentage >= 60:
            performance = "👍 Good"
        else:
            performance = "💪 Keep Trying"
        st.metric("Performance", performance)
    
    # Performance message with animation
    if st.session_state.quiz_percentage == 100:
        st.success("🏆 Perfect score! You're a quiz master! 🌟")
    elif st.session_state.quiz_percentage >= 80:
        st.success("🎯 Excellent work! You really know your stuff! 💫")
    elif st.session_state.quiz_percentage >= 60:
        st.info("👍 Good job! Keep practicing to improve! 📈")
    else:
        st.warning("💪 Don't give up! Practice makes perfect! 🚀")
    
    # Detailed results
    st.subheader("📋 Detailed Results")
    
    for i, result in enumerate(st.session_state.detailed_results):
        with st.container():
            if result['is_correct']:
                st.markdown(f'''
                <div class="result-correct">
                    <h4>✅ Question {i+1}: {result['question']}</h4>
                    <p><strong>Your answer:</strong> {result['options'][result['user_answer']-1]}</p>
                    <p><strong>Explanation:</strong> {result['explanation']}</p>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="result-wrong">
                    <h4>❌ Question {i+1}: {result['question']}</h4>
                    <p><strong>Your answer:</strong> {result['options'][result['user_answer']-1]}</p>
                    <p><strong>Correct answer:</strong> {result['options'][result['correct_answer']-1]}</p>
                    <p><strong>Explanation:</strong> {result['explanation']}</p>
                </div>
                ''', unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 View All Results", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
    with col2:
        if st.button("🔄 Same Quiz Again", use_container_width=True):
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_start_time = time.time()
            st.session_state.page = "quiz"
            st.rerun()
    with col3:
        if st.button("🎮 New Quiz", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

def show_results():
    set_background()
    st.title("📊 My Quiz History")
    
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
                col1, col2, col3, col4, col5, col6 = st.columns([2,1,1,1,1,1])
                with col1:
                    st.write(f"**{result['category']}** - {result['difficulty']}")
                    st.write(f"*{result['created_at'][:16]}*")
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
                with col6:
                    if st.button("📋 Details", key=f"view_{result['id']}"):
                        # For now, just show a message
                        st.session_state.page = "dashboard"
                        st.info(f"Detailed view for {result['category']} quiz coming soon!")
                        st.rerun()
                st.divider()
    else:
        st.info("No quiz results yet. Take your first quiz from the dashboard!")
    
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

def show_profile():
    set_background()
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
            st.success("🏆 Quiz Master - Excellent performance! 🌟")
        elif avg_score >= 60:
            st.info("🎯 Pro Learner - Good job! 💫")
        elif avg_score > 0:
            st.warning("🚀 Rising Star - Keep practicing! 📈")
        else:
            st.info("🌟 New Explorer - Start your first quiz! 🎮")
    
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

# Main app logic
def main():
    # Initialize database
    init_db()
    set_background()
    
    # Debug info (remove in production)
    st.sidebar.markdown("---")
    st.sidebar.write("**Debug Info:**")
    st.sidebar.write(f"Page: {st.session_state.page}")
    st.sidebar.write(f"User: {st.session_state.username}")
    
    # Page routing
    if st.session_state.user_id is None:
        if st.session_state.page == "login":
            show_login()
        elif st.session_state.page == "register":
            show_register()
        else:
            st.session_state.page = "login"
            show_login()
    else:
        if st.session_state.page == "dashboard":
            show_dashboard()
        elif st.session_state.page == "select_difficulty":
            show_difficulty_selection()
        elif st.session_state.page == "quiz":
            show_quiz()
        elif st.session_state.page == "quiz_results":
            show_quiz_results()
        elif st.session_state.page == "results":
            show_results()
        elif st.session_state.page == "profile":
            show_profile()
        else:
            st.session_state.page = "dashboard"
            show_dashboard()

if __name__ == "__main__":
    main()
