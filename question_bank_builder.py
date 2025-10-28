import json
from pathlib import Path
from datetime import datetime
from edu_content_api import fetch_questions_for_topic

# ===============================================================
# FILE PATHS
# ===============================================================
STUDY_PLAN_PATH = Path("study_plan.json")
QUESTION_BANK_PATH = Path("question_bank.json")

# ===============================================================
# MAIN BUILDER FUNCTION
# ===============================================================
def build_question_bank():
    # Load study plan
    if not STUDY_PLAN_PATH.exists():
        print("[ERROR] study_plan.json not found.")
        return
    
    with open(STUDY_PLAN_PATH, "r") as f:
        study_plan = json.load(f)

    print(f"[INFO] Building Question Bank for course: {study_plan['course_name']}")

    # Prepare structure
    question_bank = {
        "course_name": study_plan["course_name"],
        "course_code": study_plan["course_code"],
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "weeks": []
    }

    # Iterate through all weeks
    for week in study_plan["weeks"]:
        topic = week["topic"]
        week_num = week["week"]

        print(f"\n[INFO] Fetching questions for Week {week_num}: {topic}")
        questions = fetch_questions_for_topic(topic)

        week_entry = {
            "week": week_num,
            "topic": topic,
            "questions": questions
        }
        question_bank["weeks"].append(week_entry)

    # Save the result
    with open(QUESTION_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(question_bank, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Question bank generated successfully → {QUESTION_BANK_PATH}")
    print(f"Total weeks processed: {len(question_bank['weeks'])}")

# ===============================================================
# RUN DIRECTLY
# ===============================================================
if __name__ == "__main__":
    build_question_bank()
