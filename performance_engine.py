import json
import numpy as np
from datetime import datetime
from pathlib import Path

def load_readiness_scores(file_path="readiness_scores.json"):
    path = Path(file_path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # ✅ Extract only week_scores if present
        if isinstance(data, dict) and "week_scores" in data:
            return data["week_scores"]
        return data
    except Exception:
        return {}

def calculate_metrics(readiness):
    if not readiness:
        return {
            "average_score": 0,
            "best_week": None,
            "worst_week": None,
            "exam_readiness": 0,
            "week_trend": {}
        }

    # Convert keys to str/int and values to float
    scores = {str(k): float(v) for k, v in readiness.items() if isinstance(v, (int, float, str))}

    weeks = list(scores.keys())
    values = np.array(list(scores.values()), dtype=float)

    avg_score = float(np.mean(values))
    max_score = float(np.max(values))
    min_score = float(np.min(values))
    trend = scores

    # Simple readiness metric
    exam_readiness = round((avg_score + (0.1 * max_score)) / 1.1, 2)

    best_week = weeks[np.argmax(values)]
    worst_week = weeks[np.argmin(values)]

    metrics = {
        "average_score": round(avg_score, 2),
        "best_week": best_week,
        "worst_week": worst_week,
        "exam_readiness": exam_readiness,
        "week_trend": trend
    }
    return metrics


def analyze_performance(file_path="readiness_scores.json"):
    readiness = load_readiness_scores(file_path)
    metrics = calculate_metrics(readiness)

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_weeks": len(readiness),
        "metrics": metrics,
        "raw_data": readiness
    }

    print("\n=== PERFORMANCE REPORT ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")
    print("==========================")

    Path("performance_report.json").write_text(json.dumps(report, indent=4))
    return report


if __name__ == "__main__":
    analyze_performance()
