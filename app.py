import streamlit as st
import sqlite3
import uuid
import time
import random
from datetime import datetime

# Initialize database - FIXED VERSION
def init_database():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect('quiz_app.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Create quiz_results table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                percentage REAL NOT NULL,
                time_taken REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        st.success("✅ Database initialized successfully")
    except sqlite3.Error as e:
        st.error(f"❌ Database initialization error: {e}")

# Enhanced Database Manager Class
class QuizDatabase:
    def __init__(self, db_path='quiz_app.db'):
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the table exists before any operation"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    percentage REAL NOT NULL,
                    time_taken REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Table creation error: {e}")
    
    def save_quiz_result(self, user_id, category, difficulty, score, total_questions, percentage, time_taken):
        """Save quiz result to database"""
        try:
            # Ensure table exists before insert
            self._ensure_table_exists()
            
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quiz_results (user_id, category, difficulty, score, total_questions, percentage, time_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, category, difficulty, score, total_questions, percentage, time_taken))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            st.error(f"❌ Database save error: {e}")
            return False
    
    def get_user_results(self, user_id):
        """Get all quiz results for a user"""
        try:
            self._ensure_table_exists()
            
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
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
        except sqlite3.Error as e:
            st.error(f"❌ Database fetch error: {e}")
            return []
    
    def get_user_average_score(self, user_id):
        """Get average score for a user"""
        try:
            self._ensure_table_exists()
            
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT AVG(percentage) FROM quiz_results 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else 0.0
        except sqlite3.Error as e:
            st.error(f"❌ Database average error: {e}")
            return 0.0

# Initialize database instance
db = QuizDatabase()

# Quiz questions database (keep your existing questions here)
QUIZ_QUESTIONS = {
    "Mathematics": {
        "Easy": [
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4"
            },
            # ... keep your existing questions
        ],
        # ... other difficulties and categories
    }
    # ... other categories
}

def show_dashboard():
    """Display the main dashboard"""
    st.title("🎯 Your Learning Journey")
    
    # Initialize database on dashboard load
    init_database()
    
    # User stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Total Quizzes")
        user_results = db.get_user_results(st.session_state.user_id)
        total_quizzes = len(user_results)
        st.metric("Quizzes Taken", total_quizzes)
    
    with col2:
        st.subheader("Average Score")
        avg_score = db.get_user_average_score(st.session_state.user_id)
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
                st.session_state.selected_difficulty = "Medium"  # Default difficulty
                st.session_state.page = 'quiz'
                st.rerun()
    
    st.markdown("---")
    
    # Recent performance
    st.subheader("📈 Recent Performance")
    
    if user_results:
        # Display last 5 results
        recent_results = user_results[:5]
        for result in recent_results:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    category = result.get('category', 'Unknown Category')
                    difficulty = result.get('difficulty', 'Unknown Difficulty')
                    st.write(f"**{category}** - {difficulty}")
                
                with col2:
                    score = result.get('score', 0)
                    total = result.get('total_questions', 0)
                    percentage = result.get('percentage', 0)
                    st.write(f"Score: {score}/{total}")
                
                with col3:
                    # Performance indicator
                    if percentage >= 80:
                        st.success(f"{percentage:.1f}% 🎉")
                    elif percentage >= 60:
                        st.warning(f"{percentage:.1f}% 👍")
                    else:
                        st.error(f"{percentage:.1f}% 💪")
                
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
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = []
    
    # Category and difficulty selection at start
    if st.session_state.current_question == 0 and not st.session_state.user_answers:
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
            # Ensure database is initialized before starting quiz
            init_database()
            
            # Load questions for selected category and difficulty
            if category in QUIZ_QUESTIONS and difficulty in QUIZ_QUESTIONS[category]:
                st.session_state.quiz_questions = QUIZ_QUESTIONS[category][difficulty]
                st.session_state.current_question = 0
                st.session_state.user_answers = []
                st.session_state.start_time = time.time()
                st.rerun()
            else:
                st.error("❌ No questions available for this category and difficulty.")
        
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
        # All questions answered - show results
        submit_quiz()

def submit_quiz():
    """Calculate and display quiz results, save to database"""
    try:
        questions = st.session_state.quiz_questions
        user_answers = st.session_state.user_answers
        
        # Calculate score
        score = 0
        for i, question in enumerate(questions):
            if i < len(user_answers) and user_answers[i] == question['correct_answer']:
                score += 1
        
        total_questions = len(questions)
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0
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
        
        # Save to database with error handling
        success = db.save_quiz_result(
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
            st.error("❌ Failed to save results to database.")
        
        # Show review of answers
        st.markdown("---")
        st.subheader("📋 Review Your Answers")
        
        for i, question in enumerate(questions):
            with st.container():
                user_answer = user_answers[i] if i < len(user_answers) else "Not answered"
                correct = user_answer == question['correct_answer']
                
                st.write(f"**Q{i+1}: {question['question']}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"Your answer: {user_answer}")
                
                with col2:
                    if correct:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Correct answer: {question['correct_answer']}")
                
                st.divider()
        
        # Navigation buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Take Another Quiz", use_container_width=True):
                # Reset quiz state
                st.session_state.current_question = 0
                st.session_state.user_answers = []
                st.session_state.start_time = time.time()
                st.session_state.quiz_questions = []
                st.rerun()
        
        with col2:
            if st.button("📊 View Results", use_container_width=True):
                st.session_state.page = 'results'
                st.rerun()
        
        with col3:
            if st.button("🏠 Back to Dashboard", use_container_width=True):
                st.session_state.page = 'dashboard'
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ An error occurred while submitting the quiz: {e}")
        if st.button("🏠 Back to Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()

def show_results():
    """Display user's quiz results history"""
    st.title("📊 My Quiz Results")
    
    # Ensure database is initialized
    init_database()
    
    # Get user results
    results = db.get_user_results(st.session_state.user_id)
    
    if results:
        st.subheader("Your Quiz History")
        
        # Display results in an expandable format
        for i, result in enumerate(results):
            with st.expander(f"Quiz {i+1} - {result.get('category', 'General')} ({result.get('difficulty', 'Medium')})", expanded=i==0):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write("**Score**")
                    st.write(f"{result.get('score', 0)}/{result.get('total_questions', 0)}")
                
                with col2:
                    st.write("**Percentage**")
                    percentage = result.get('percentage', 0)
                    if percentage >= 80:
                        st.success(f"{percentage:.1f}%")
                    elif percentage >= 60:
                        st.warning(f"{percentage:.1f}%")
                    else:
                        st.error(f"{percentage:.1f}%")
                
                with col3:
                    st.write("**Time Taken**")
                    st.write(f"{result.get('time_taken', 0):.1f}s")
                
                with col4:
                    st.write("**Date**")
                    created_at = result.get('created_at', 'Unknown')
                    if created_at != 'Unknown':
                        st.write(created_at[:16] if len(created_at) >= 16 else created_at)
                    else:
                        st.write("N/A")
        
        # Statistics
        st.markdown("---")
        st.subheader("📈 Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_quizzes = len(results)
            st.metric("Total Quizzes", total_quizzes)
        
        with col2:
            avg_score = db.get_user_average_score(st.session_state.user_id)
            st.metric("Average Score", f"{avg_score:.1f}%" if avg_score else "0%")
        
        with col3:
            best_score = max([r.get('percentage', 0) for r in results]) if results else 0
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
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()

def main():
    """Main application function"""
    # Initialize database at app start
    init_database()
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Page navigation
    if st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'quiz':
        show_quiz()
    elif st.session_state.page == 'results':
        show_results()

if __name__ == "__main__":
    main()
