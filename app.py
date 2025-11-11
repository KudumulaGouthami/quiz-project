import streamlit as st
import sqlite3
import uuid
import time
import json
from datetime import datetime

# Set page config first
st.set_page_config(
    page_title="Quiz Application",
    page_icon="🧠",
    layout="wide"
)

# SIMPLE DATABASE SOLUTION
def get_db_connection():
    """Get database connection with automatic table creation"""
    conn = sqlite3.connect('quiz_app.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist - SIMPLIFIED
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
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
    return conn

def save_quiz_result(user_id, category, difficulty, score, total_questions, percentage, time_taken):
    """Save quiz result - SIMPLIFIED"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quiz_results 
            (user_id, category, difficulty, score, total_questions, percentage, time_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, category, difficulty, score, total_questions, percentage, time_taken))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving result: {e}")
        return False

def get_user_results(user_id):
    """Get user results - SIMPLIFIED"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quiz_results 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        columns = ['id', 'user_id', 'category', 'difficulty', 'score', 
                  'total_questions', 'percentage', 'time_taken', 'created_at']
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        st.error(f"Error getting results: {e}")
        return []

def get_user_average_score(user_id):
    """Get average score - SIMPLIFIED"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT AVG(percentage) FROM quiz_results WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else 0.0
    except Exception as e:
        return 0.0

# Quiz questions database
QUIZ_QUESTIONS = {
    "Mathematics": {
        "Easy": [
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4"
            },
            {
                "question": "What is 5 × 3?",
                "options": ["10", "15", "20", "25"],
                "correct_answer": "15"
            },
            {
                "question": "What is 10 ÷ 2?",
                "options": ["2", "5", "10", "20"],
                "correct_answer": "5"
            }
        ],
        "Medium": [
            {
                "question": "What is 12 × 12?",
                "options": ["121", "144", "132", "156"],
                "correct_answer": "144"
            },
            {
                "question": "What is 45 ÷ 9?",
                "options": ["4", "5", "6", "7"],
                "correct_answer": "5"
            }
        ],
        "Hard": [
            {
                "question": "What is 15% of 200?",
                "options": ["15", "20", "25", "30"],
                "correct_answer": "30"
            },
            {
                "question": "What is the square root of 169?",
                "options": ["11", "12", "13", "14"],
                "correct_answer": "13"
            }
        ]
    },
    "Science": {
        "Easy": [
            {
                "question": "What planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "correct_answer": "Mars"
            },
            {
                "question": "What is H₂O?",
                "options": ["Oxygen", "Hydrogen", "Water", "Carbon Dioxide"],
                "correct_answer": "Water"
            }
        ],
        "Medium": [
            {
                "question": "What is the chemical symbol for gold?",
                "options": ["Go", "Gd", "Au", "Ag"],
                "correct_answer": "Au"
            }
        ],
        "Hard": [
            {
                "question": "What is the atomic number of carbon?",
                "options": ["6", "8", "12", "14"],
                "correct_answer": "6"
            }
        ]
    },
    "English": {
        "Easy": [
            {
                "question": "Which word is a noun?",
                "options": ["run", "beautiful", "quickly", "cat"],
                "correct_answer": "cat"
            }
        ],
        "Medium": [
            {
                "question": "What is a synonym for 'happy'?",
                "options": ["sad", "joyful", "angry", "tired"],
                "correct_answer": "joyful"
            }
        ],
        "Hard": [
            {
                "question": "What is an oxymoron?",
                "options": [
                    "A figure of speech with contradictory terms",
                    "A type of poem", 
                    "A grammatical error",
                    "A spelling mistake"
                ],
                "correct_answer": "A figure of speech with contradictory terms"
            }
        ]
    },
    "General Knowledge": {
        "Easy": [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct_answer": "Paris"
            }
        ],
        "Medium": [
            {
                "question": "Who wrote 'Romeo and Juliet'?",
                "options": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
                "correct_answer": "William Shakespeare"
            }
        ],
        "Hard": [
            {
                "question": "Who discovered penicillin?",
                "options": ["Marie Curie", "Alexander Fleming", "Louis Pasteur", "Robert Koch"],
                "correct_answer": "Alexander Fleming"
            }
        ]
    }
}

def show_dashboard():
    """Display the main dashboard"""
    st.title("🎯 Your Learning Journey")
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    # User stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Total Quizzes")
        user_results = get_user_results(st.session_state.user_id)
        total_quizzes = len(user_results)
        st.metric("Quizzes Taken", total_quizzes)
    
    with col2:
        st.subheader("Average Score")
        avg_score = get_user_average_score(st.session_state.user_id)
        st.metric("Performance", f"{avg_score:.1f}%" if avg_score else "0%")
    
    st.markdown("---")
    
    # Start new quiz section
    st.subheader("🚀 Start New Quiz")
    st.write("Choose Your Challenge")
    
    # Category selection
    cols = st.columns(4)
    categories = ["Mathematics", "Science", "English", "General Knowledge"]
    icons = ["🔢", "🔬", "📚", "🌍"]
    
    for i, (col, category, icon) in enumerate(zip(cols, categories, icons)):
        with col:
            if st.button(f"{icon}\n{category}", use_container_width=True, key=f"cat_{i}"):
                st.session_state.selected_category = category
                st.session_state.page = 'quiz'
                st.rerun()
    
    st.markdown("---")
    
    # Recent performance
    st.subheader("📈 Recent Performance")
    
    if user_results:
        for result in user_results[:3]:  # Show last 3 results
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    category = result.get('category', 'General')
                    difficulty = result.get('difficulty', 'Medium')
                    st.write(f"**{category}** - {difficulty}")
                
                with col2:
                    score = result.get('score', 0)
                    total = result.get('total_questions', 0)
                    st.write(f"Score: {score}/{total}")
                
                with col3:
                    percentage = result.get('percentage', 0)
                    if percentage >= 80:
                        st.success(f"{percentage:.1f}%")
                    elif percentage >= 60:
                        st.warning(f"{percentage:.1f}%")
                    else:
                        st.error(f"{percentage:.1f}%")
                
                st.divider()
    else:
        st.info("No quiz results yet. Take your first quiz to see your performance here!")

def show_quiz():
    """Display and manage the quiz"""
    st.title("🧠 Quiz Time!")
    
    # Initialize quiz state
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    if 'selected_difficulty' not in st.session_state:
        st.session_state.selected_difficulty = "Medium"
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = "Mathematics"
    
    # Category and difficulty selection at start
    if st.session_state.current_question == 0 and len(st.session_state.user_answers) == 0:
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Select Category",
                ["Mathematics", "Science", "English", "General Knowledge"],
                key="category_select"
            )
            st.session_state.selected_category = category
        
        with col2:
            difficulty = st.selectbox(
                "Select Difficulty",
                ["Easy", "Medium", "Hard"],
                key="difficulty_select"
            )
            st.session_state.selected_difficulty = difficulty
        
        if st.button("Start Quiz", type="primary"):
            # Load questions
            category = st.session_state.selected_category
            difficulty = st.session_state.selected_difficulty
            
            if category in QUIZ_QUESTIONS and difficulty in QUIZ_QUESTIONS[category]:
                st.session_state.quiz_questions = QUIZ_QUESTIONS[category][difficulty]
                st.rerun()
            else:
                st.error("No questions available for this selection.")
        
        if st.button("← Back to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        
        return
    
    # Display current question
    current_q = st.session_state.current_question
    questions = st.session_state.quiz_questions
    
    if current_q < len(questions):
        question_data = questions[current_q]
        
        st.subheader(f"Question {current_q + 1} of {len(questions)}")
        st.write(f"**{question_data['question']}**")
        
        # Display options
        user_answer = st.radio(
            "Select your answer:",
            question_data['options'],
            key=f"q_{current_q}"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("Next Question", type="primary"):
                st.session_state.user_answers.append(user_answer)
                st.session_state.current_question += 1
                st.rerun()
        
        with col2:
            if st.button("← Back to Dashboard"):
                st.session_state.page = 'dashboard'
                st.rerun()
    
    else:
        # All questions answered - submit quiz
        submit_quiz()

def submit_quiz():
    """Calculate and display quiz results"""
    try:
        questions = st.session_state.quiz_questions
        user_answers = st.session_state.user_answers
        
        # Calculate score
        score = 0
        for i, question in enumerate(questions):
            if i < len(user_answers) and user_answers[i] == question['correct_answer']:
                score += 1
        
        total_questions = len(questions)
        percentage = (score / total_questions) * 100
        time_taken = time.time() - st.session_state.start_time
        
        # Display results
        st.subheader("🎊 Quiz Completed!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Score", f"{score}/{total_questions}")
        
        with col2:
            st.metric("Percentage", f"{percentage:.1f}%")
        
        with col3:
            st.metric("Time Taken", f"{time_taken:.1f}s")
        
        # Performance message
        if percentage >= 80:
            st.success("🎉 Excellent work! You're a star!")
        elif percentage >= 60:
            st.warning("👍 Good job! Keep practicing!")
        else:
            st.info("💪 Keep trying! You'll get better!")
        
        # Save to database
        success = save_quiz_result(
            st.session_state.user_id,
            st.session_state.selected_category,
            st.session_state.selected_difficulty,
            score,
            total_questions,
            percentage,
            time_taken
        )
        
        if success:
            st.success("✅ Results saved successfully!")
        else:
            st.warning("⚠️ Results not saved, but you can still see your score.")
        
        # Show review
        st.markdown("---")
        st.subheader("📋 Review Your Answers")
        
        for i, question in enumerate(questions):
            user_answer = user_answers[i] if i < len(user_answers) else "Not answered"
            correct = user_answer == question['correct_answer']
            
            st.write(f"**Q{i+1}: {question['question']}**")
            st.write(f"Your answer: {user_answer}")
            if correct:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Correct answer: {question['correct_answer']}")
            st.divider()
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Take Another Quiz", use_container_width=True):
                reset_quiz_state()
                st.rerun()
        
        with col2:
            if st.button("📊 View Results", use_container_width=True):
                st.session_state.page = 'results'
                st.rerun()
        
        with col3:
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.page = 'dashboard'
                st.rerun()
                
    except Exception as e:
        st.error(f"Error in quiz submission: {e}")
        if st.button("🏠 Back to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()

def reset_quiz_state():
    """Reset quiz state"""
    st.session_state.current_question = 0
    st.session_state.user_answers = []
    st.session_state.start_time = time.time()
    if 'quiz_questions' in st.session_state:
        del st.session_state.quiz_questions

def show_results():
    """Display user's quiz results history"""
    st.title("📊 My Quiz Results")
    
    # Get user results
    results = get_user_results(st.session_state.user_id)
    
    if results:
        st.subheader("Your Quiz History")
        
        for i, result in enumerate(results):
            with st.expander(f"Quiz {i+1} - {result.get('category', 'General')} ({result.get('difficulty', 'Medium')})", expanded=i==0):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write("**Score**")
                    st.write(f"{result.get('score', 0)}/{result.get('total_questions', 0)}")
                
                with col2:
                    st.write("**Percentage**")
                    percentage = result.get('percentage', 0)
                    st.write(f"{percentage:.1f}%")
                
                with col3:
                    st.write("**Time Taken**")
                    st.write(f"{result.get('time_taken', 0):.1f}s")
                
                with col4:
                    st.write("**Date**")
                    created_at = result.get('created_at', '')
                    st.write(created_at[:16] if created_at else 'N/A')
        
        # Statistics
        st.markdown("---")
        st.subheader("📈 Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Quizzes", len(results))
        
        with col2:
            avg_score = get_user_average_score(st.session_state.user_id)
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col3:
            best_score = max([r.get('percentage', 0) for r in results])
            st.metric("Best Score", f"{best_score:.1f}%")
    
    else:
        st.info("No quiz results yet. Take a quiz to see your results here!")
        
        if st.button("Start Your First Quiz", type="primary"):
            st.session_state.page = 'quiz'
            st.rerun()
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Take Another Quiz", use_container_width=True):
            st.session_state.page = 'quiz'
            st.rerun()
    
    with col2:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()

def main():
    """Main application function"""
    # Initialize page
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    # Page navigation
    if st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'quiz':
        show_quiz()
    elif st.session_state.page == 'results':
        show_results()

if __name__ == "__main__":
    main()
