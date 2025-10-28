import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ===============================================================
# LOAD DATA
# ===============================================================
with open("study_plan.json", "r") as f:
    study_plan = json.load(f)

PROGRESS_FILE = Path("progress_tracker.json")

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"user_id": "student_001", "completed_weeks": [], "completed_videos": {}, "completed_books": {}, "last_updated": None}

def save_progress(progress):
    progress["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

progress = load_progress()

# ===============================================================
# HELPERS
# ===============================================================
def get_current_week_index():
    today = datetime.today()
    for i, week in enumerate(study_plan["weeks"]):
        start = datetime.strptime(week["calendar"]["start_date"], "%b %d, %Y")
        end = datetime.strptime(week["calendar"]["end_date"], "%b %d, %Y")
        if start <= today <= end:
            return i
    return 0  # fallback

def calc_progress(week):
    wk = str(week["week"])
    total_videos = len(week["youtube_links"])
    total_books = len(week["recommended_books"])
    done_videos = len(progress["completed_videos"].get(wk, []))
    done_books = len(progress["completed_books"].get(wk, []))
    week_done = 1 if week["week"] in progress["completed_weeks"] else 0
    total = total_videos + total_books + 1  # +1 for week completion
    completed = done_videos + done_books + week_done
    return int((completed / total) * 100) if total > 0 else 0

# ===============================================================
# GUI SETUP
# ===============================================================
root = tk.Tk()
root.title("SmartLearningAI - Study Dashboard")
root.geometry("950x720")
root.configure(bg="#f8fafc")

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10), background="#f8fafc")
style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), background="#f8fafc")

content_frame = ttk.Frame(root)
content_frame.pack(padx=15, pady=10, fill="both", expand=True)

# ===============================================================
# ANALYTICS POPUP WINDOW
# ===============================================================
def open_analytics_window():
    win = tk.Toplevel(root)
    win.title("📈 SmartLearningAI Analytics")
    win.geometry("800x600")
    win.configure(bg="#f9fafc")

    total_weeks = len(study_plan["weeks"])
    done_weeks = len(progress["completed_weeks"])
    total_videos = sum(len(v) for v in progress["completed_videos"].values())
    total_books = sum(len(v) for v in progress["completed_books"].values())

    # --- Calculate overall completion ---
    total_possible_videos = sum(len(w["youtube_links"]) for w in study_plan["weeks"])
    total_possible_books = sum(len(w["recommended_books"]) for w in study_plan["weeks"])
    overall = ( (total_videos + total_books + done_weeks)
                / (total_possible_videos + total_possible_books + total_weeks) ) * 100

    ttk.Label(win, text=f"Overall Course Completion: {overall:.1f}%", font=("Segoe UI", 12, "bold")).pack(pady=10)

    # --- Bar chart for weekly progress ---
    week_labels = [f"W{w['week']}" for w in study_plan["weeks"]]
    week_progress = [calc_progress(w) for w in study_plan["weeks"]]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(week_labels, week_progress, color="#3b82f6")
    ax.set_ylim(0, 100)
    ax.set_title("Weekly Progress Overview")
    ax.set_xlabel("Week")
    ax.set_ylabel("Completion (%)")

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10)

    # --- Books vs Videos Pie Chart ---
    fig2, ax2 = plt.subplots(figsize=(4, 4))
    data = [total_books, total_videos]
    labels = ["Books Read", "Videos Watched"]
    colors = ["#10b981", "#f59e0b"]
    ax2.pie(data, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax2.set_title("Learning Activity Breakdown")

    canvas2 = FigureCanvasTkAgg(fig2, master=win)
    canvas2.draw()
    canvas2.get_tk_widget().pack(pady=10)

    ttk.Label(win, text=f"Weeks Completed: {done_weeks}/{total_weeks}", font=("Segoe UI", 10)).pack(pady=5)
    ttk.Label(win, text=f"Books Read: {total_books} | Videos Watched: {total_videos}", font=("Segoe UI", 10)).pack()

# ===============================================================
# CORE CONTENT RENDERING
# ===============================================================
def render_week(week):
    for widget in content_frame.winfo_children():
        widget.destroy()

    progress_percent = calc_progress(week)
    wk_num = week["week"]

    ttk.Label(content_frame, text=f"📘 {study_plan['course_name']}", style="Header.TLabel").pack(anchor="center", pady=(0,5))
    ttk.Label(content_frame, text=f"Week {wk_num}: {week['topic']}", font=("Segoe UI", 11)).pack(anchor="center")
    ttk.Label(content_frame, text=f"{week['calendar']['start_date']} → {week['calendar']['end_date']}", font=("Segoe UI", 9)).pack(anchor="center", pady=(0,8))

    # Progress bar
    ttk.Label(content_frame, text=f"Progress: {progress_percent}%", font=("Segoe UI", 10, "bold")).pack(anchor="center")
    bar = ttk.Progressbar(content_frame, length=300, value=progress_percent, mode="determinate")
    bar.pack(pady=(0, 15))

    # Study Plan
    ttk.Label(content_frame, text="🧠 Study Plan:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(5,0))
    txt = tk.Text(content_frame, height=4, wrap="word", bg="#edf2f7", font=("Segoe UI", 10))
    txt.insert("1.0", week["study_plan"])
    txt.config(state="disabled")
    txt.pack(fill="x", pady=5)

    # Books
    ttk.Label(content_frame, text="📚 Books:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
    for book in week["recommended_books"]:
        frame_b = ttk.Frame(content_frame)
        frame_b.pack(anchor="w", pady=2, fill="x")
        ttk.Label(frame_b, text=f"• {book}").pack(side="left")
        def mark_book(b=book):
            wk = str(week["week"])
            progress["completed_books"].setdefault(wk, [])
            if b not in progress["completed_books"][wk]:
                progress["completed_books"][wk].append(b)
                save_progress(progress)
                messagebox.showinfo("✅", f"Book marked as read: {b}")
                render_week(week)
        ttk.Button(frame_b, text="Mark Read", command=mark_book).pack(side="right")

    # Videos
    ttk.Label(content_frame, text="\n🎥 Videos:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
    for video in week["youtube_links"]:
        frame_v = ttk.Frame(content_frame)
        frame_v.pack(anchor="w", pady=2, fill="x")
        link = ttk.Label(frame_v, text=f"• {video}", foreground="#0645AD", cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e, v=video: webbrowser.open(v))
        def mark_video(v=video):
            wk = str(week["week"])
            progress["completed_videos"].setdefault(wk, [])
            if v not in progress["completed_videos"][wk]:
                progress["completed_videos"][wk].append(v)
                save_progress(progress)
                messagebox.showinfo("✅", f"Video marked as watched: {v}")
                render_week(week)
        ttk.Button(frame_v, text="Mark Watched", command=mark_video).pack(side="right")

    # Mark Week Complete
    def mark_week_done():
        if wk_num not in progress["completed_weeks"]:
            progress["completed_weeks"].append(wk_num)
            save_progress(progress)
            messagebox.showinfo("🎉", f"Week {wk_num} marked as completed!")
            render_week(week)
        else:
            messagebox.showinfo("✔️", f"Week {wk_num} already completed.")
    ttk.Button(content_frame, text="✅ Mark Week Completed", command=mark_week_done).pack(pady=15)

# ===============================================================
# WEEK DROPDOWN
# ===============================================================
week_names = [f"Week {w['week']}: {w['topic'][:50]}..." for w in study_plan["weeks"]]
current_week_index = get_current_week_index()
selected_week = tk.StringVar(value=week_names[current_week_index])

def on_week_change(event=None):
    index = week_names.index(selected_week.get())
    render_week(study_plan["weeks"][index])

ttk.Label(root, text="Select Week:", font=("Segoe UI", 10)).pack(pady=(5, 0))
dropdown = ttk.Combobox(root, textvariable=selected_week, values=week_names, state="readonly", width=80)
dropdown.pack()
dropdown.bind("<<ComboboxSelected>>", on_week_change)

# ===============================================================
# ANALYTICS BUTTON
# ===============================================================
ttk.Button(root, text="📊 View Analytics", command=open_analytics_window).pack(pady=10)

# ===============================================================
# INITIAL RENDER
# ===============================================================
render_week(study_plan["weeks"][current_week_index])

root.mainloop()
