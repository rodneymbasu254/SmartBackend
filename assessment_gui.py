"""
assessment_gui.py — Updated with inline performance analytics
"""

import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import threading

from performance_engine import analyze_performance

# Optional imports
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except Exception:
    SPEECH_AVAILABLE = False

try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except Exception:
    SYMPY_AVAILABLE = False

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# File paths
QUESTION_BANK_PATH = Path("question_bank.json")
PROGRESS_PATH = Path("progress_tracker.json")
ANSWERS_PATH = Path("answers_tracker.json")
READINESS_PATH = Path("readiness_scores.json")

# Helpers
def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")

# Load data
study_questions = load_json(QUESTION_BANK_PATH, None)
progress = load_json(PROGRESS_PATH, {"user_id":"student_001","completed_weeks":[],"completed_videos":{},"completed_books":{}})
answers_tracker = load_json(ANSWERS_PATH, {"user_id":"student_001","answers":[]})
readiness_scores = load_json(READINESS_PATH, {"user_id":"student_001","week_scores":{}, "overall": None})

# === fallback question creation (same as before) ===
# ... (keep your fallback block here unchanged)

# === Helper functions (grading, readiness, etc.) ===
def grade_answer(q, user_answer):
    correct = None
    expected = q.get("answer")
    if expected is None:
        return None, "manual_review"
    try:
        if isinstance(expected, (int, float)):
            ua = float(user_answer)
            correct = abs(ua - float(expected)) < 1e-6
        else:
            if SYMPY_AVAILABLE:
                try:
                    e_exp = sp.sympify(expected)
                    e_ans = sp.sympify(user_answer)
                    correct = sp.simplify(e_exp - e_ans) == 0
                except Exception:
                    correct = str(user_answer).strip().lower() == str(expected).strip().lower()
            else:
                correct = str(user_answer).strip().lower() == str(expected).strip().lower()
    except Exception:
        correct = str(user_answer).strip().lower() == str(expected).strip().lower()

    return bool(correct), "auto" if expected is not None else "manual_review"

def calculate_week_readiness(week_num):
    a = [ans for ans in answers_tracker.get("answers", []) if ans.get("week") == week_num]
    if not a:
        return None
    auto_gradable = [x for x in a if x.get("grading") == "auto"]
    correct = sum(1 for x in auto_gradable if x.get("correct"))
    total = len(a)
    score = (correct / total) * 100
    return round(score, 2)

# === GUI ===
root = tk.Tk()
root.title("SmartLearningAI — Assessment")
root.geometry("950x720")
root.configure(bg="#f8fafc")

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10), background="#f8fafc")
style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), background="#f8fafc")

course_title = study_questions.get("course_name", "Course")
ttk.Label(root, text=f"{course_title} — Assessments", style="Header.TLabel").pack(pady=8)

weeks = study_questions.get("weeks", [])
week_names = [f"Week {w['week']}: {w['topic'][:60]}..." for w in weeks]
selected_week_var = tk.StringVar(value=week_names[0] if week_names else "No weeks available")

def get_selected_week():
    sel = selected_week_var.get()
    if sel == "No weeks available":
        return None
    idx = week_names.index(sel)
    return weeks[idx]

ttk.Label(root, text="Select Week:", font=("Segoe UI", 10)).pack()
week_dropdown = ttk.Combobox(root, textvariable=selected_week_var, values=week_names, state="readonly", width=100)
week_dropdown.pack(pady=6)

q_frame = ttk.Frame(root)
q_frame.pack(fill="both", expand=True, padx=12, pady=8)

current_question_index = 0
current_questions = []
q_text = tk.Text(q_frame, height=4, wrap="word", bg="#eef2ff", font=("Segoe UI", 10))
q_text.pack(fill="x", pady=(4,8))

options_vars = []
mcq_var = tk.StringVar(value="")
sa_entry = None

# === Core logic ===
def load_week_questions(week):
    global current_question_index, current_questions
    current_question_index = 0
    current_questions = week.get("questions", [])
    if not current_questions:
        q_text.config(state="normal")
        q_text.delete("1.0", tk.END)
        q_text.insert("1.0", "No questions available for this week.")
        q_text.config(state="disabled")
        return
    render_question(0)

def render_question(idx):
    global current_question_index, options_vars, mcq_var, sa_entry
    current_question_index = idx
    q = current_questions[idx]
    q_text.config(state="normal")
    q_text.delete("1.0", tk.END)
    q_text.insert("1.0", f"Q{idx+1}: {q.get('question')}")
    q_text.config(state="disabled")

    for w in q_frame.pack_slaves():
        if getattr(w, "is_option", False):
            w.destroy()

    options_vars = []
    mcq_var.set("")
    sa_entry = None

    if q.get("type") == "mcq":
        for opt in q.get("options", []):
            f = ttk.Frame(q_frame)
            f.pack(anchor="w", pady=2)
            f.is_option = True
            ttk.Radiobutton(f, text=opt, value=opt, variable=mcq_var).pack(side="left")
    else:
        f = ttk.Frame(q_frame)
        f.pack(fill="x", pady=4)
        f.is_option = True
        sa_entry = ttk.Entry(f, width=80)
        sa_entry.pack(side="left", padx=(0,6))

    nav = ttk.Frame(q_frame)
    nav.pack(fill="x", pady=8)
    nav.is_option = True
    ttk.Button(nav, text="◀ Prev", command=prev_question).pack(side="left", padx=4)
    ttk.Button(nav, text="Next ▶", command=next_question).pack(side="left", padx=4)
    ttk.Button(nav, text="Submit Answer", command=submit_answer).pack(side="right", padx=4)

def prev_question():
    if current_question_index > 0:
        render_question(current_question_index - 1)

def next_question():
    if current_question_index + 1 < len(current_questions):
        render_question(current_question_index + 1)

# === PERFORMANCE INTEGRATION ===
def show_performance_popup():
    """Run performance analysis and show results inline."""
    report = analyze_performance()
    metrics = report.get("metrics", {})

    perf_window = tk.Toplevel(root)
    perf_window.title("Performance Summary")
    perf_window.geometry("520x420")
    perf_window.configure(bg="#F3F6FB")

    tk.Label(perf_window, text="📊 PERFORMANCE SUMMARY", font=("Poppins", 16, "bold"), bg="#F3F6FB").pack(pady=10)

    # Inline trend chart
    scores = [v for v in metrics.get("week_trend", {}).values()]
    weeks = list(metrics.get("week_trend", {}).keys())
    if weeks and scores:
        fig, ax = plt.subplots(figsize=(4.5,2))
        ax.plot(weeks, scores, marker="o")
        ax.set_ylim(0, 100)
        ax.set_title("Readiness Trend")
        ax.set_ylabel("Score (%)")
        canvas = FigureCanvasTkAgg(fig, master=perf_window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=5)

    # List metrics
    for key, value in metrics.items():
        if key != "week_trend":
            text = f"{key.replace('_',' ').capitalize()}: {value}"
            tk.Label(perf_window, text=text, font=("Roboto", 11), bg="#F3F6FB", anchor="w").pack(pady=2)

    readiness = metrics.get("exam_readiness", 0)
    if readiness >= 75:
        msg = "Excellent! You’re ready for exams! 💪"
    elif readiness >= 60:
        msg = "Good progress! Keep revising weak topics. 📚"
    else:
        msg = "Needs improvement — focus on weak areas 🔍"

    tk.Label(perf_window, text=msg, font=("Roboto", 10, "italic"), bg="#F3F6FB").pack(pady=10)
    ttk.Button(perf_window, text="Close", command=perf_window.destroy).pack(pady=8)

def on_assessment_complete():
    threading.Thread(target=show_performance_popup).start()

def submit_answer():
    q = current_questions[current_question_index]
    if q.get("type") == "mcq":
        user_ans = mcq_var.get()
        if not user_ans:
            messagebox.showwarning("No Answer", "Please select an option before submitting.")
            return
    else:
        user_ans = sa_entry.get().strip() if sa_entry else ""
        if not user_ans and not messagebox.askyesno("Empty Answer", "Submit empty answer?"):
            return

    graded, grading_type = grade_answer(q, user_ans)
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "week": get_selected_week().get("week"),
        "question_index": current_question_index,
        "question": q.get("question"),
        "user_answer": user_ans,
        "correct": graded if graded is not None else None,
        "grading": grading_type,
        "source": q.get("source")
    }
    answers_tracker.setdefault("answers", []).append(entry)
    save_json(ANSWERS_PATH, answers_tracker)

    messagebox.showinfo("Answer Submitted", f"Answer saved. Grading: {grading_type}. Correct: {graded}")
    week_num = get_selected_week().get("week")
    score = calculate_week_readiness(week_num)
    if score is not None:
        readiness_scores.setdefault("week_scores", {})[str(week_num)] = score
        vals = list(readiness_scores.get("week_scores", {}).values())
        readiness_scores["overall"] = round(sum(vals)/len(vals), 2)
        save_json(READINESS_PATH, readiness_scores)

    # ✅ Trigger performance analysis
    on_assessment_complete()

# === Analytics button ===
def open_readiness_analytics():
    win = tk.Toplevel(root)
    win.title("Readiness Analytics")
    win.geometry("800x600")
    win.configure(bg="#fbfdff")

    ttk.Label(win, text="Readiness Scores", font=("Segoe UI", 12, "bold")).pack(pady=6)
    week_labels = [f"W{w['week']}" for w in study_questions.get("weeks", [])]
    scores = [readiness_scores.get("week_scores", {}).get(str(w.get("week")), 0) for w in study_questions.get("weeks", [])]

    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(week_labels, scores, marker='o')
    ax.set_ylim(0, 100)
    ax.set_ylabel("Score (%)")
    ax.set_xlabel("Week")
    ax.set_title("Week-by-week Readiness Trend")

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10)

    overall = readiness_scores.get("overall", 0)
    ttk.Label(win, text=f"Overall readiness: {overall}%", font=("Segoe UI", 10)).pack(pady=6)

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=8)
ttk.Button(btn_frame, text="📈 View Readiness Analytics", command=open_readiness_analytics).pack(side="left", padx=6)
ttk.Button(btn_frame, text="🔄 Refresh Questions", command=lambda: load_week_questions(get_selected_week())).pack(side="left", padx=6)
ttk.Button(btn_frame, text="🔎 Open Question Bank File", command=lambda: webbrowser.open(str(QUESTION_BANK_PATH.absolute()))).pack(side="left", padx=6)

if weeks:
    load_week_questions(weeks[0])

root.mainloop()
