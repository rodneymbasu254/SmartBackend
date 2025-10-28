"""
research_assistant.py

SmartLearningAI - AI Research Assistant
Helps students research assignment or CAT questions.
Fetches, summarizes, and highlights key educational content
from multiple sources, returning a structured result.
"""

import requests, re, random
from bs4 import BeautifulSoup
from datetime import datetime

# Optional summarizer (use OpenAI if available)
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception:
    summarizer = None


# ----------------------------------------------------------
# 🔹 Utility functions
# ----------------------------------------------------------

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def summarize_text(text, max_sentences=3):
    """Uses transformer summarizer if available, else truncates text."""
    if not text:
        return ""
    if summarizer:
        summary = summarizer(text, max_length=120, min_length=40, do_sample=False)
        return summary[0]["summary_text"]
    # fallback simple heuristic
    sentences = text.split(". ")
    return ". ".join(sentences[:max_sentences]) + "..."


# ----------------------------------------------------------
# 🔹 Wikipedia fetch
# ----------------------------------------------------------
def fetch_wikipedia(query):
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


# ----------------------------------------------------------
# 🔹 GeeksforGeeks fetch
# ----------------------------------------------------------
def fetch_gfg(query):
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


# ----------------------------------------------------------
# 🔹 Coursera fetch (course title only)
# ----------------------------------------------------------
def fetch_coursera(query):
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


# ----------------------------------------------------------
# 🔹 Google Books API
# ----------------------------------------------------------
def fetch_books(query):
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


# ----------------------------------------------------------
# 🔹 YouTube API (requires API key)
# ----------------------------------------------------------
def fetch_youtube(query, api_key=None):
    if not api_key:
        return []
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": query, "key": api_key, "maxResults": 3, "type": "video"}
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


# ----------------------------------------------------------
# 🔹 Main Research Function
# ----------------------------------------------------------
def research_topic(query, youtube_key=None):
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


# ----------------------------------------------------------
# 🔹 Example run
# ----------------------------------------------------------
if __name__ == "__main__":
    topic = input("Enter your assignment or CAT question: ")
    output = research_topic(topic)
    print("\n=== RESEARCH RESULT ===")
    print(output)
