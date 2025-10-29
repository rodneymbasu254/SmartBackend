"""
research_assistant.py

SmartLearningAI - AI Research Assistant
Helps students research assignment or CAT questions.
Fetches, summarizes, and highlights key educational content
from multiple sources, returning a structured result.

Optimized for Render: lightweight summarization via Hugging Face API.
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ==========================================================
# 🔹 Hugging Face API Configuration
# ==========================================================
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_SUMMARY_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"


# ==========================================================
# 🔹 Utility Functions
# ==========================================================
def clean_text(text: str) -> str:
    """Clean up whitespace and extra characters."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """Summarize text using Hugging Face API or fallback method."""
    if not text:
        return ""

    # --- Hugging Face Summarization ---
    if HF_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            payload = {"inputs": text, "parameters": {"max_length": 120, "min_length": 40}}
            res = requests.post(HF_SUMMARY_URL, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and "summary_text" in data[0]:
                    return clean_text(data[0]["summary_text"])
        except Exception as e:
            print(f"[WARN] Summarizer failed: {e}")

    # --- Fallback: simple heuristic ---
    sentences = text.split(". ")
    return ". ".join(sentences[:max_sentences]) + "..."


# ==========================================================
# 🔹 Wikipedia Fetch
# ==========================================================
def fetch_wikipedia(query: str):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            summary = data.get("extract", "")
            return {
                "source": "Wikipedia",
                "title": data.get("title", query),
                "summary": summarize_text(summary),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except Exception:
        pass
    return None


# ==========================================================
# 🔹 GeeksforGeeks Fetch
# ==========================================================
def fetch_gfg(query: str):
    try:
        search = "+".join(query.split())
        url = f"https://www.geeksforgeeks.org/search/?q={search}"
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("div", class_="head")
        if article:
            title = article.text.strip()
            link = article.find_parent("a")["href"]
            return {
                "source": "GeeksforGeeks",
                "title": title,
                "summary": f"GeeksforGeeks has an article explaining {query}.",
                "url": link
            }
    except Exception:
        pass
    return None


# ==========================================================
# 🔹 Coursera Fetch
# ==========================================================
def fetch_coursera(query: str):
    try:
        search = "+".join(query.split())
        url = f"https://www.coursera.org/search?query={search}"
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h2.card-title")
        if title:
            return {
                "source": "Coursera",
                "title": title.text.strip(),
                "summary": f"Coursera offers a course titled '{title.text.strip()}' related to {query}.",
                "url": url
            }
    except Exception:
        pass
    return None


# ==========================================================
# 🔹 Google Books API
# ==========================================================
def fetch_books(query: str):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
        data = requests.get(url, timeout=5).json()
        books = []
        for item in data.get("items", [])[:3]:
            vol = item.get("volumeInfo", {})
            books.append({
                "title": vol.get("title"),
                "authors": vol.get("authors", []),
                "preview_link": vol.get("previewLink")
            })
        return books
    except Exception:
        return []


# ==========================================================
# 🔹 YouTube Fetch (requires API key)
# ==========================================================
def fetch_youtube(query: str, api_key: str = None):
    if not api_key:
        api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("[WARN] No YouTube API key found.")
        return []
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": api_key,
            "maxResults": 3,
            "type": "video"
        }
        res = requests.get(url, params=params, timeout=5).json()
        results = []
        for item in res.get("items", []):
            results.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return results
    except Exception:
        return []


# ==========================================================
# 🔹 Main Research Function
# ==========================================================
def research_topic(query: str, youtube_key: str = None):
    """Collects, summarizes, and compiles information from multiple educational sources."""
    print(f"[INFO] Researching: {query}")

    results = []
    for fetcher in [fetch_wikipedia, fetch_gfg, fetch_coursera]:
        res = fetcher(query)
        if res:
            results.append(res)

    books = fetch_books(query)
    videos = fetch_youtube(query, api_key=youtube_key)

    combined_summary = " ".join([r["summary"] for r in results if r.get("summary")])
    highlight = summarize_text(combined_summary, max_sentences=3)

    return {
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": highlight,
        "sources": results,
        "recommended_books": books,
        "recommended_videos": videos
    }


# ==========================================================
# 🔹 Example Run (Local)
# ==========================================================
if __name__ == "__main__":
    topic = input("Enter your assignment or CAT question: ")
    output = research_topic(topic)
    print("\n=== RESEARCH RESULT ===")
    print(output)
