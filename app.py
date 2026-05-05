import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from ai_detection_service import compute_ai_probability
from database import (
    count_submissions,
    count_submissions_recent_days,
    fetch_all_submissions,
    fetch_recent_submissions,
    init_db,
    insert_submission,
)
from similarity import code_similarity, text_similarity
from storage import try_save_upload

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")
app.config.setdefault("STORE_UPLOAD_FILES", True)

init_db()

UPLOAD_ROOT = Path(__file__).resolve().parent / "uploads"

# Dashboard statistics
stats = {
    "submissions": 0,
    "plagiarism": 0,
    "checked": 0
}


def _disk_enabled():
    return bool(app.config.get("STORE_UPLOAD_FILES", True))


def _persist_submission(filename: str, content: str):
    sid = insert_submission(filename, content)
    try_save_upload(UPLOAD_ROOT, sid, filename, content, _disk_enabled())
    return sid


# Home page
@app.route("/")
def home():
    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():
    recent_activity = fetch_recent_submissions(10)
    return render_template(
        "dashboard.html",
        stats=stats,
        db_total=count_submissions(),
        recent_week_count=count_submissions_recent_days(7),
        recent_activity=recent_activity,
    )


@app.route("/results")
def results():
    report = session.get("last_report")
    return render_template("results.html", report=report)


@app.route("/history")
def history():
    rows = fetch_recent_submissions(200)
    return render_template("history.html", rows=rows)


@app.route("/dataset/upload", methods=["POST"])
def dataset_upload():
    files = request.files.getlist("files")
    stored = 0
    failed = []

    for f in files:
        if not f or not (f.filename and f.filename.strip()):
            continue
        text = f.read().decode("utf-8", errors="ignore")
        fn = f.filename.strip()
        try:
            _persist_submission(fn, text)
            stored += 1
        except Exception:
            app.logger.exception("Bulk upload failed for %s", fn)
            failed.append(fn)

    if stored:
        stats["submissions"] += stored
        flash(f"Added {stored} file(s) to the dataset.", "success")
    if failed:
        flash(f"Could not store: {', '.join(failed)}", "danger")
    if not stored and not failed:
        flash("No files selected.", "warning")

    return redirect(url_for("dashboard"))


# Similarity comparison
@app.route("/compare", methods=["POST"])
def compare():

    upload = request.files["file"]

    text = upload.read().decode("utf-8", errors="ignore")
    fn = (upload.filename or "").strip() or "unnamed"

    ai_probability = compute_ai_probability(text)

    rows = fetch_all_submissions()
    matches = []
    for row in rows:
        stored = row["content"]
        t_pct = text_similarity(text, stored) * 100
        c_pct = code_similarity(text, stored) * 100
        matches.append(
            {
                "filename": row["filename"],
                "timestamp": row["timestamp"],
                "text_score": round(t_pct, 2),
                "code_score": round(c_pct, 2),
                "rank_score": max(t_pct, c_pct),
            }
        )

    matches.sort(key=lambda m: (m["rank_score"], m["text_score"], m["code_score"]), reverse=True)
    top5 = matches[:5]
    for m in top5:
        m.pop("rank_score", None)

    try:
        _persist_submission(fn, text)
    except Exception:
        app.logger.exception("Failed to store submission in database.db")

    stats["submissions"] += 1
    stats["checked"] += 1

    best_max = max(max(m["text_score"], m["code_score"]) for m in top5) if top5 else 0.0
    if top5 and (best_max > 60):
        stats["plagiarism"] += 1

    if not top5:
        risk = "No prior submissions"
        color = "secondary"
    elif best_max < 30:
        risk = "Low Risk"
        color = "success"
    elif best_max < 60:
        risk = "Medium Risk"
        color = "warning"
    else:
        risk = "High Risk"
        color = "danger"

    session["last_report"] = {
        "uploaded_filename": fn,
        "matches": top5,
        "risk": risk,
        "color": color,
        "ai_probability": ai_probability,
    }
    session.modified = True

    return render_template(
        "result.html",
        uploaded_filename=fn,
        matches=top5,
        risk=risk,
        color=color,
        ai_probability=ai_probability,
    )


if __name__ == "__main__":
    app.run(debug=True)
