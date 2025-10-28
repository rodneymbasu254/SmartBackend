"""
edu_content_api.py
Unified Educational Content Fetcher for SmartLearningAI
Scrapes / queries multiple education sources to get topic-related
questions and resources. Falls back to local generation if all fail.
"""

import requests, random, re
from bs4 import BeautifulSoup

# ----------------------------------------------------------
# HELPER: clean topic string
# ----------------------------------------------------------
def normalize_topic(topic):
    t = re.sub(r'[^A-Za-z0-9\s]', '', topic)
    return t.strip().lower().replace(" ", "-")

# ----------------------------------------------------------
# 1️⃣ Khan Academy API
# ----------------------------------------------------------
def fetch_from_khan(topic):
    try:
        key = normalize_topic(topic)
        url = f"https://www.khanacademy.org/api/v1/topic/{key}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return [{
                "type": "practice",
                "source": "Khan Academy",
                "question": data.get("title", topic),
                "options": [],
                "answer": None,
                "reference_url": f"https://www.khanacademy.org/{data.get('slug','computing')}"
            }]
    except Exception:
        pass
    return []

# ----------------------------------------------------------
# 2️⃣ Wikipedia definitions
# ----------------------------------------------------------
def fetch_from_wikipedia(topic):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{normalize_topic(topic)}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            summary = data.get("extract", "")
            return [{
                "type": "short",
                "source": "Wikipedia",
                "question": f"Define or explain: {topic}",
                "options": [],
                "answer": summary[:300] + "..." if summary else None,
                "reference_url": data.get("content_urls", {}).get("desktop", {}).get("page")
            }]
    except Exception:
        pass
    return []

# ----------------------------------------------------------
# 3️⃣ GeeksforGeeks scraping
# ----------------------------------------------------------
def fetch_from_gfg(topic):
    try:
        q = "+".join(topic.split())
        url = f"https://www.geeksforgeeks.org/search/?q={q}"
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        links = [a["href"] for a in soup.select("a") if a.get("href","").startswith("https://www.geeksforgeeks.org/")]
        if links:
            sample = random.choice(links)
            return [{
                "type": "practice",
                "source": "GeeksforGeeks",
                "question": f"Read and practice: {topic}",
                "options": [],
                "answer": None,
                "reference_url": sample
            }]
    except Exception:
        pass
    return []

# ----------------------------------------------------------
# 4️⃣ Coursera / edX search (HTML titles only)
# ----------------------------------------------------------
def fetch_from_coursera(topic):
    try:
        q = "+".join(topic.split())
        url = f"https://www.coursera.org/search?query={q}"
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        titles = [c.text for c in soup.select("h2.card-title")][:3]
        if titles:
            return [{
                "type": "reference",
                "source": "Coursera",
                "question": f"Explore the Coursera course: {titles[0]}",
                "options": [],
                "answer": None,
                "reference_url": url
            }]
    except Exception:
        pass
    return []

# ----------------------------------------------------------
# 5️⃣ Google Custom Search API (optional, needs key)
# ----------------------------------------------------------
def fetch_from_google(topic, api_key=None, cx=None):
    if not api_key or not cx:
        return []
    try:
        params = {"key": api_key, "cx": cx, "q": topic}
        res = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=5)
        data = res.json()
        items = data.get("items", [])
        results = []
        for item in items[:3]:
            results.append({
                "type": "article",
                "source": "GoogleSearch",
                "question": item.get("title"),
                "options": [],
                "answer": None,
                "reference_url": item.get("link")
            })
        return results
    except Exception:
        return []

# ----------------------------------------------------------
# 6️⃣ Local fallback generator
# ----------------------------------------------------------
def local_generator(topic):
    return [
        {
            "type": "mcq",
            "source": "Local Template",
            "question": f"What is the main concept behind {topic}?",
            "options": ["Definition", "Algorithm", "Formula", "None of the above"],
            "answer": "Definition"
        },
        {
            "type": "short",
            "source": "Local Template",
            "question": f"Explain in your own words: {topic}",
            "options": [],
            "answer": None
        }
    ]

# ----------------------------------------------------------
# 🔁 Unified fetcher
# ----------------------------------------------------------
def fetch_questions_for_topic(topic, google_api=None, google_cx=None):
    all_results = []
    for fetcher in [fetch_from_khan, fetch_from_wikipedia, fetch_from_gfg, fetch_from_coursera]:
        res = fetcher(topic)
        if res:
            all_results.extend(res)
    if not all_results and google_api and google_cx:
        all_results.extend(fetch_from_google(topic, google_api, google_cx))
    if not all_results:
        all_results.extend(local_generator(topic))
    return all_results
