import json
from datetime import datetime, timedelta
from pathlib import Path

# ===============================================================
# 1️⃣ Load study plan
# ===============================================================
with open("study_plan.json", "r") as f:
    study_plan = json.load(f)

# ===============================================================
# 2️⃣ Progress Tracker Utilities
# ===============================================================
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
# 3️⃣ Core Delivery Logic
# ===============================================================
def get_current_week_plan(study_plan, current_date=None):
    if current_date is None:
        current_date = datetime.today()
    for week in study_plan["weeks"]:
        start = datetime.strptime(week["calendar"]["start_date"], "%b %d, %Y")
        end = datetime.strptime(week["calendar"]["end_date"], "%b %d, %Y")
        if start <= current_date <= end:
            return week
    return None

today = datetime.today()
current_week = get_current_week_plan(study_plan, today)

# ===============================================================
# 4️⃣ Display and Interact
# ===============================================================
if current_week:
    print(f"\n📚 WEEK {current_week['week']}: {current_week['topic']}")
    print(f"🗓️ {current_week['calendar']['start_date']} - {current_week['calendar']['end_date']}")
    print(f"\n🧠 {current_week['study_plan']}\n")

    print("📘 Books:")
    for i, book in enumerate(current_week["recommended_books"], 1):
        print(f"  [{i}] {book}")

    print("\n🎥 Videos:")
    for i, video in enumerate(current_week["youtube_links"], 1):
        print(f"  [{i}] {video}")

    # --- Progress Interactions ---
    print("\n✅ Progress Options:")
    print("1. Mark week as completed")
    print("2. Mark a video as watched")
    print("3. Mark a book as read")
    print("4. View progress summary")
    print("5. Exit")

    choice = input("\nChoose an option: ")

    if choice == "1":
        if current_week["week"] not in progress["completed_weeks"]:
            progress["completed_weeks"].append(current_week["week"])
            print(f"🎉 Week {current_week['week']} marked as completed!")
        else:
            print("✔️ Already completed.")
        save_progress(progress)

    elif choice == "2":
        vid_num = int(input("Enter video number: "))
        link = current_week["youtube_links"][vid_num - 1]
        week_key = str(current_week["week"])
        progress["completed_videos"].setdefault(week_key, [])
        if link not in progress["completed_videos"][week_key]:
            progress["completed_videos"][week_key].append(link)
            print("🎥 Video marked as watched!")
        else:
            print("✔️ Already watched.")
        save_progress(progress)

    elif choice == "3":
        book_num = int(input("Enter book number: "))
        book = current_week["recommended_books"][book_num - 1]
        week_key = str(current_week["week"])
        progress["completed_books"].setdefault(week_key, [])
        if book not in progress["completed_books"][week_key]:
            progress["completed_books"][week_key].append(book)
            print("📗 Book marked as read!")
        else:
            print("✔️ Already read.")
        save_progress(progress)

    elif choice == "4":
        print("\n📊 PROGRESS SUMMARY:")
        print(f"Weeks completed: {len(progress['completed_weeks'])}/{len(study_plan['weeks'])}")
        print("Videos watched:", sum(len(v) for v in progress['completed_videos'].values()))
        print("Books read:", sum(len(v) for v in progress['completed_books'].values()))

    elif choice == "5":
        print("👋 Exiting... Progress saved.")

else:
    print("⚠️ No active week found for today's date.")
