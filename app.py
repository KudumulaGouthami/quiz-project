# app.py -- Advanced Quiz Application (single-file)
# Requirements: streamlit, sqlite3 (builtin), pandas (optional)
# Run: pip install streamlit pandas
# Then: streamlit run app.py

import streamlit as st
import sqlite3
import hashlib
import time
import random
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Advanced Quiz App", layout="wide", initial_sidebar_state="expanded")

# -------------------------
# Styles and animated background
# -------------------------
page_bg_css = """
<style>
/* Full page gradient background */
[data-testid="stAppViewContainer"] > .main {
  background: linear-gradient(120deg, #f6d365 0%, #fda085 50%, #fbc2eb 100%);
  background-attachment: fixed;
}

/* Card styling */
.quiz-card {
  background: rgba(255,255,255,0.85);
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.12);
}

/* Fancy headings */
.h1 {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  color: #3b185f;
  text-shadow: 0 1px 0 rgba(255,255,255,0.6);
}

/* Button hover */
.stButton>button:hover { transform: translateY(-2px); }

/* Make sidebar semi-translucent */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(255,255,255,0.75), rgba(255,255,255,0.55));
  border-radius: 12px;
  padding: 12px;
}

/* Question box */
.question-box {
  background: linear-gradient(90deg, rgba(255,255,255,0.98), rgba(255,255,255,0.9));
  border-left: 6px solid #ff7eb3;
  padding: 16px;
  border-radius: 8px;
}
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# Small header
st.markdown("<h1 class='h1'>🌟 Advanced Quiz Application</h1>", unsafe_allow_html=True)
st.markdown("A fun, colorful quiz app with registration, login, categories, difficulty, timer & leaderboard.")

# -------------------------
# Database helpers
# -------------------------
DB_PATH = "quiz_app.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TEXT
        )
    ''')
    # questions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            category TEXT,
            difficulty TEXT,
            question TEXT,
            choices TEXT,    -- stored as JSON-like '|' separated options
            answer TEXT
        )
    ''')
    # results table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            subject TEXT,
            category TEXT,
            difficulty TEXT,
            score INTEGER,
            total_questions INTEGER,
            percentage REAL,
            time_taken REAL,
            taken_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------------
# Utility functions
# -------------------------
def hash_password(password: str, salt: str = "quiz_salt_v1"):
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def register_user(username, email, password):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (username, email, hash_password(password), datetime.utcnow().isoformat()))
        conn.commit()
        return True, "Registered successfully!"
    except sqlite3.IntegrityError as e:
        return False, f"Registration error: {e}"
    finally:
        conn.close()

def login_user(username_or_email, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?",
                (username_or_email, username_or_email))
    row = cur.fetchone()
    conn.close()
    if row:
        _id, uname, email, pw_hash = row
        if pw_hash == hash_password(password):
            return True, {"id": _id, "username": uname, "email": email}
    return False, "Invalid credentials."

# Seed some sample questions if questions table empty
def seed_questions_once():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    count = cur.fetchone()[0]
    if count == 0:
        sample = [
            ("Mathematics","Algebra","Easy","What is 2 + 2?","4|3|5|22","4"),
            ("Mathematics","Algebra","Medium","Solve for x: 2x+3=11","4|3|2|8","4"),
            ("Science","Physics","Easy","What force keeps us on the ground?","Magnetism|Gravity|Friction|Tension","Gravity"),
            ("Science","Biology","Hard","Which organelle is the powerhouse of the cell?","Nucleus|Mitochondria|Ribosome|Golgi apparatus","Mitochondria"),
            ("Computers","Programming","Medium","Which language is primarily used for web pages?","Python|C|JavaScript|Fortran","JavaScript"),
            ("General Knowledge","History","Easy","Who was the first President of the United States?","Abraham Lincoln|George Washington|Thomas Jefferson|John Adams","George Washington"),
            ("Anime","Characters","Easy","Which anime features a character named Naruto?","One Piece|Naruto|Bleach|Dragon Ball","Naruto"),
            ("Anime","Trivia","Medium","In 'My Neighbor Totoro', who are the main child characters?","Satsuki & Mei|Ash & Pikachu|Chihiro & Haku|Edward & Alphonse","Satsuki & Mei"),
        ]
        for subj, cat, diff, q, choices, ans in sample:
            cur.execute("INSERT INTO questions (subject, category, difficulty, question, choices, answer) VALUES (?,?,?,?,?,?)",
                        (subj, cat, diff, q, choices, ans))
        conn.commit()
    conn.close()

seed_questions_once()

# -------------------------
# Session state initialization
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "quiz" not in st.session_state:
    st.session_state.quiz = {}
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# -------------------------
# Sidebar: Login / Register / Profile / Anime clips
# -------------------------
with st.sidebar:
    st.image("https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif", caption="Let's get quizzical!", use_column_width=True)
    st.markdown("---")
    if st.session_state.user is None:
        auth_tab = st.radio("Choose", ["Login", "Register"], index=0)
        if auth_tab == "Register":
            st.markdown("### Create account")
            r_user = st.text_input("Username", key="r_user")
            r_email = st.text_input("Email", key="r_email")
            r_pw = st.text_input("Password", type="password", key="r_pw")
            r_pw2 = st.text_input("Confirm Password", type="password", key="r_pw2")
            if st.button("Register"):
                if not r_user or not r_email or not r_pw:
                    st.warning("Fill all fields.")
                elif r_pw != r_pw2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(r_user.strip(), r_email.strip(), r_pw)
                    if ok:
                        st.success(msg + " Please login now.")
                    else:
                        st.error(msg)
        else:
            st.markdown("### Login")
            l_user = st.text_input("Username or Email", key="l_user")
            l_pw = st.text_input("Password", type="password", key="l_pw")
            if st.button("Login"):
                ok, info = login_user(l_user.strip(), l_pw)
                if ok:
                    st.session_state.user = info
                    st.success(f"Welcome, {info['username']}!")
                else:
                    st.error(info)
    else:
        st.markdown(f"### Logged in as: **{st.session_state.user['username']}**")
        if st.button("Logout"):
            st.session_state.user = None
            st.success("Logged out.")
    st.markdown("---")
    st.markdown("### Anime Clip")
    # A gentle, safe sample video link (public YouTube). You can replace with any YouTube link.
    st.video("https://www.youtube.com/watch?v=ysz5S6PUM-U")
    st.markdown("---")
    st.markdown("Created for fun ✨")

# -------------------------
# Main app UI: choose subject/category/difficulty & take quiz
# -------------------------
conn = get_conn()
cur = conn.cursor()

# fetch subjects, categories, difficulties from database
cur.execute("SELECT DISTINCT subject FROM questions")
subjects = [r[0] for r in cur.fetchall()] or ["General"]
cur.execute("SELECT DISTINCT category FROM questions")
categories = [r[0] for r in cur.fetchall()] or ["General"]
cur.execute("SELECT DISTINCT difficulty FROM questions")
difficulties = [r[0] for r in cur.fetchall()] or ["Easy", "Medium", "Hard"]

conn.close()

st.markdown("<div class='quiz-card'>", unsafe_allow_html=True)

col1, col2 = st.columns([3,1])
with col1:
    st.header("Choose your quiz ⚙️")
    selected_subject = st.selectbox("Subject", ["Any"] + subjects, key="selected_subject")
    selected_category = st.selectbox("Category", ["Any"] + categories, key="selected_category")
    selected_difficulty = st.selectbox("Difficulty", ["Any"] + difficulties, key="selected_difficulty")
    num_questions = st.slider("Number of questions", 3, 15, 7)
    time_limit_min = st.number_input("Time limit (minutes)", min_value=1, max_value=60, value=5)
    st.markdown("")

    if st.button("Start Quiz"):
        # fetch questions according to filters
        conn = get_conn()
        cur = conn.cursor()
        query = "SELECT id, subject, category, difficulty, question, choices, answer FROM questions WHERE 1=1"
        params = []
        if selected_subject != "Any":
            query += " AND subject = ?"; params.append(selected_subject)
        if selected_category != "Any":
            query += " AND category = ?"; params.append(selected_category)
        if selected_difficulty != "Any":
            query += " AND difficulty = ?"; params.append(selected_difficulty)
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            st.warning("No questions match your filters. Try 'Any' or seed more questions.")
        else:
            # randomly pick questions
            rows = random.sample(rows, min(num_questions, len(rows)))
            # store quiz in session
            st.session_state.quiz = {
                "questions": rows,
                "total": len(rows),
                "subject": selected_subject,
                "category": selected_category,
                "difficulty": selected_difficulty,
                "time_limit": int(time_limit_min * 60)  # seconds
            }
            st.session_state.answers = {}
            st.session_state.start_time = time.time()
            st.experimental_rerun()

with col2:
    st.header("Quick Info")
    st.markdown(f"- **Logged in:** {'Yes' if st.session_state.user else 'No'}")
    st.markdown(f"- **Subject:** {selected_subject}")
    st.markdown(f"- **Category:** {selected_category}")
    st.markdown(f"- **Difficulty:** {selected_difficulty}")
    st.markdown(f"- **Num Qs:** {num_questions}")
    st.markdown(f"- **Time limit:** {time_limit_min} min")
    st.markdown("---")
    st.markdown("Tip: register to save scores on the leaderboard!")

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Quiz runner
# -------------------------
def run_quiz():
    quiz = st.session_state.get("quiz", None)
    if not quiz or "questions" not in quiz:
        st.info("Start a quiz from the options above.")
        return

    elapsed = int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0
    remaining = quiz["time_limit"] - elapsed
    if remaining < 0:
        remaining = 0

    minutes = remaining // 60
    seconds = remaining % 60

    st.markdown(f"**Time remaining:** ⏱️ {minutes:02d}:{seconds:02d}")

    if remaining == 0:
        st.warning("Time is up! Submitting automatically...")
        submit_answers(auto=True)
        return

    # show questions one by one or all questions
    qcols = st.columns(1)
    with qcols[0]:
        for idx, row in enumerate(quiz["questions"], start=1):
            qid, subject, category, difficulty, question, choices, answer = row
            st.markdown(f"<div class='question-box'><b>Q{idx}.</b> {question}  <small>({subject} | {category} | {difficulty})</small></div>", unsafe_allow_html=True)
            opts = choices.split("|")
            key = f"q_{qid}"
            default = st.session_state.answers.get(key, None)
            choice = st.radio("", opts, index=opts.index(default) if default in opts else 0, key=key, horizontal=False)
            st.session_state.answers[key] = choice
            st.markdown("---")

    # action buttons
    col_a, col_b = st.columns([1,1])
    with col_a:
        if st.button("Submit Quiz"):
            submit_answers(auto=False)
    with col_b:
        if st.button("Reset Answers"):
            st.session_state.answers = {}
            st.experimental_rerun()

def submit_answers(auto=False):
    quiz = st.session_state.get("quiz", None)
    if not quiz:
        st.info("No active quiz.")
        return
    total = quiz["total"]
    score = 0
    correct_details = []
    for row in quiz["questions"]:
        qid = row[0]
        correct = row[6]
        key = f"q_{qid}"
        user_ans = st.session_state.answers.get(key, "")
        if user_ans == correct:
            score += 1
            correct_details.append((qid, True))
        else:
            correct_details.append((qid, False))
    percentage = round((score / total) * 100, 2)
    time_taken = time.time() - st.session_state.start_time if st.session_state.start_time else 0

    # Save result if user logged in
    if st.session_state.user:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO quiz_results (user_id, username, subject, category, difficulty, score, total_questions, percentage, time_taken, taken_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (st.session_state.user['id'], st.session_state.user['username'],
              quiz['subject'], quiz['category'], quiz['difficulty'],
              score, total, percentage, time_taken, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        st.success(f"Quiz submitted! Score saved. {score}/{total} ({percentage}%). Time: {int(time_taken)}s")
    else:
        st.info(f"Quiz submitted! Score: {score}/{total} ({percentage}%). Time: {int(time_taken)}s — Register or login to save results.")
    # show breakdown
    st.markdown("### Results")
    st.markdown(f"- Score: **{score} / {total}**")
    st.markdown(f"- Percentage: **{percentage}%**")
    st.markdown(f"- Time taken: **{int(time_taken)} seconds**")
    # Reset quiz session (so they can start again)
    st.session_state.quiz = {}
    st.session_state.answers = {}
    st.session_state.start_time = None

# If quiz active, show runner
if st.session_state.quiz and st.session_state.quiz.get("questions"):
    st.markdown("<div class='quiz-card'>", unsafe_allow_html=True)
    st.header("Take the Quiz")
    run_quiz()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Admin: Add question (simple UI) & Leaderboard
# -------------------------
st.markdown("---")
st.header("Extras")

exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    st.subheader("Add a Question (quick)")
    q_subject = st.text_input("Subject", key="q_subject")
    q_category = st.text_input("Category", key="q_category")
    q_difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard"], key="q_diff")
    q_text = st.text_area("Question text", key="q_text")
    q_choices = st.text_input("Choices (separate by | )", key="q_choices", help="e.g. A|B|C|D")
    q_answer = st.text_input("Correct answer (must match one choice)", key="q_answer")
    if st.button("Add Question"):
        if not q_subject or not q_text or not q_choices or not q_answer:
            st.warning("Fill all fields.")
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO questions (subject, category, difficulty, question, choices, answer) VALUES (?,?,?,?,?,?)",
                        (q_subject, q_category or "General", q_difficulty, q_text, q_choices, q_answer))
            conn.commit()
            conn.close()
            st.success("Question added!")

with exp_col2:
    st.subheader("Leaderboard")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, subject, category, difficulty, score, total_questions, percentage, time_taken, taken_at FROM quiz_results ORDER BY percentage DESC, score DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if rows:
        df = pd.DataFrame(rows, columns=["User","Subject","Category","Difficulty","Score","Total","%","TimeTaken(s)","Taken At"])
        st.dataframe(df)
    else:
        st.info("No results yet — take a quiz to appear here!")

st.markdown("---")
st.caption("Made with ❤️ — customize questions, styles, and embed your favorite anime clips!")

# End of file

