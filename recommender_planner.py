import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# ===============================================================
# 1️⃣ Load environment variables
# ===============================================================
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_BOOKS_API = os.getenv("GOOGLE_BOOKS_API", "https://www.googleapis.com/books/v1/volumes?q=")
GOOGLE_SEARCH_API = os.getenv("GOOGLE_SEARCH_API", "https://www.googleapis.com/customsearch/v1")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

# ===============================================================
# 2️⃣ Helper functions
# ===============================================================
def load_parsed_outline():
    """Safely load output.json (course outline) if available."""
    path = Path("output.json")
    if not path.exists():
        raise FileNotFoundError("Missing 'output.json'. Please upload or generate it first.")
    return json.loads(path.read_text(encoding="utf-8"))


def get_youtube_videos(query):
    """Fetch 3 educational YouTube videos related to the topic."""
    if not YOUTUBE_API_KEY:
        return []
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "maxResults": 3,
            "type": "video",
            "key": YOUTUBE_API_KEY,
        }
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        return [
            f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            for item in data.get("items", [])
        ]
    except Exception:
        return []


def get_books(query):
    """Fetch 3 recommended book titles from Google Books."""
    try:
        r = requests.get(GOOGLE_BOOKS_API + query, timeout=8)
        r.raise_for_status()
        data = r.json()
        return [
            item["volumeInfo"]["title"]
            for item in data.get("items", [])[:3]
            if "volumeInfo" in item
        ]
    except Exception:
        return []


def get_articles(query):
    """Fetch 3 educational article links from Google Custom Search."""
    if not GOOGLE_API_KEY or not CUSTOM_SEARCH_ENGINE_ID:
        return []
    try:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": CUSTOM_SEARCH_ENGINE_ID,
            "q": query,
        }
        r = requests.get(GOOGLE_SEARCH_API, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        return [item["link"] for item in data.get("items", [])[:3]]
    except Exception:
        return []


# ===============================================================
# 3️⃣ Study plan generator
# ===============================================================
def generate_study_plan():
    """Generate study plan JSON from parsed course outline."""
    parsed_data = load_parsed_outline()

    start_date = datetime.today()
    calendar = [
        {
            "week": i + 1,
            "start_date": (start_date + timedelta(weeks=i)).strftime("%b %d, %Y"),
            "end_date": (start_date + timedelta(weeks=i + 1) - timedelta(days=1)).strftime("%b %d, %Y"),
        }
        for i in range(len(parsed_data["weekly_topics"]))
    ]

    weeks_plan = []
    for i, topic in enumerate(parsed_data["weekly_topics"]):
        query = topic.split(":")[-1].strip()
        books = get_books(query)
        videos = get_youtube_videos(query)
        articles = get_articles(query)

        plan = {
            "week": i + 1,
            "topic": topic,
            "calendar": calendar[i],
            "study_plan": (
                f"Focus on understanding and practicing {query}. "
                f"Review examples, read at least one recommended book, "
                f"and watch the videos to reinforce key concepts."
            ),
            "recommended_books": books,
            "youtube_links": videos,
            "articles": articles,
        }
        weeks_plan.append(plan)

    final_plan = {
        "course_code": parsed_data.get("course_code"),
        "course_name": parsed_data.get("course_name"),
        "weeks": weeks_plan,
    }

    Path("study_plan.json").write_text(json.dumps(final_plan, indent=4), encoding="utf-8")
    print("✅ Study plan created successfully → study_plan.json")
    return final_plan


# ===============================================================
# 4️⃣ Optional: Run manually
# ===============================================================
if __name__ == "__main__":
    try:
        plan = generate_study_plan()
        print(json.dumps(plan, indent=2))
    except Exception as e:
        print(f"❌ Failed to generate study plan: {e}")
