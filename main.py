"""
main.py
========
SmartLearningAI Backend — Unified API Gateway
---------------------------------------------
Central FastAPI entry point connecting all AI-driven modules:
- Course Parser (PDF/DOCX)
- Study Plan Generator
- Question Bank Builder
- Research Assistant
- Performance Analytics
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, json, tempfile
from pathlib import Path

# Import local modules
from parser_engine import parse_docx_file, parse_pdf_file
from recommender_planner import generate_study_plan
from question_bank_builder import build_question_bank
from research_assistant import research_topic
from performance_engine import analyze_performance

# ✅ Import the logger
from db_logger import log_json

# Load environment variables
load_dotenv()

# ===============================================================
# Initialize FastAPI App
# ===============================================================
app = FastAPI(
    title="SmartLearningAI Backend",
    version="2.0",
    description="Unified AI backend for SmartLearningAI Android App",
)

# Allow all origins for dev (restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================================================
# Root & Health
# ===============================================================
@app.get("/")
async def root():
    return {"message": "Welcome to SmartLearningAI Backend", "version": "2.0"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "SmartLearningAI", "version": "2.0"}


# ===============================================================
# 1️⃣ PARSER ENDPOINT (DOCX/PDF)
# ===============================================================
@app.post("/api/parse")
async def parse_outline(file: UploadFile = File(...)):
    """Uploads a course outline (.docx or .pdf) and returns structured JSON."""
    ext = Path(file.filename).suffix.lower()
    if ext not in [".docx", ".pdf"]:
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files supported")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp.flush()
            temp_path = tmp.name

        parsed_data = parse_docx_file(temp_path) if ext == ".docx" else parse_pdf_file(temp_path)
        Path("output.json").write_text(json.dumps(parsed_data, indent=4), encoding="utf-8")

        # ✅ Log the JSON output
        log_json("parse_outline", parsed_data)

        return JSONResponse(content={"status": "ok", "data": parsed_data})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {e}")
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass


# ===============================================================
# 2️⃣ STUDY PLAN ENDPOINT
# ===============================================================
@app.post("/api/plan")
async def generate_plan():
    """
    Generates a weekly study plan using parsed course data.
    Requires 'output.json' (from parser) to exist.
    """
    try:
        plan = generate_study_plan()

        # ✅ Log the JSON output
        log_json("generate_study_plan", plan)

        return JSONResponse(content={"status": "ok", "data": plan})
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Please parse a course outline first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate study plan: {e}")


# ===============================================================
# 3️⃣ QUESTION BANK ENDPOINT
# ===============================================================
@app.post("/api/questions")
async def build_questions():
    """Builds a question bank based on study_plan.json."""
    try:
        build_question_bank()
        data = json.loads(Path("question_bank.json").read_text(encoding="utf-8"))

        # ✅ Log the JSON output
        log_json("build_question_bank", data)

        return JSONResponse(content={"status": "ok", "data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build question bank: {e}")


# ===============================================================
# 4️⃣ RESEARCH ASSISTANT ENDPOINT
# ===============================================================
@app.post("/api/research")
async def research(query: str = Form(...)):
    """
    AI-powered research endpoint for assignment or CAT questions.
    Example: {"query": "Define artificial intelligence"}
    """
    try:
        result = research_topic(query)

        # ✅ Log the JSON output
        log_json("research_assistant", result)

        return JSONResponse(content={"status": "ok", "data": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {e}")


# ===============================================================
# 5️⃣ PERFORMANCE ANALYTICS ENDPOINT
# ===============================================================
@app.get("/api/performance")
async def performance():
    """Analyzes readiness_scores.json and returns performance metrics."""
    try:
        report = analyze_performance()

        # ✅ Log the JSON output
        log_json("performance_analytics", report)

        return JSONResponse(content={"status": "ok", "data": report})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {e}")


# ===============================================================
# 🚀 ENTRY POINT
# ===============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
