"""
SCORA Exam Platform — Unified Server
Includes Login, Exam, Results, and the full Examiner Insights engine.
"""
import os, json, math, random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, send_file

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

app = Flask(__name__, static_folder=None)
random.seed(42)

# --- EXAM DATA ---
EXAM_QUESTIONS = [
    {"id": 1, "question": "What does FIR stand for?", "options": ["First Information Report", "Final Investigation Record", "Federal Incident Report", "First Interrogation Report"], "answer": 0},
    {"id": 2, "question": "Define a cognizable offence.", "options": ["An offence where police can arrest without a warrant", "An offence only triable by a magistrate", "A minor traffic violation", "An offence that requires a court order to investigate"], "answer": 0},
    {"id": 3, "question": "Name one non-lethal crowd-control method.", "options": ["Water cannon", "Tear gas", "Rubber bullets", "All of the above"], "answer": 3},
    {"id": 4, "question": "What is meant by chain of custody?", "options": ["The process of arresting a suspect", "The chronological documentation of evidence", "A type of prison transport", "The sequence of court hearings"], "answer": 1},
    {"id": 5, "question": "Which agency is India’s nodal body for counter-terror investigations?", "options": ["CBI", "NIA", "RAW", "IB"], "answer": 1}
]

# --- INSIGHTS DATA GENERATION (Thursday Version) ---
FIRST = ["Aparna","Rohan","Meera","Kabir","Ishita","Arjun","Nandini","Vikram","Sana","Devansh","Priya","Harsh","Tanvi","Yash","Anjali","Imran","Kavya","Nikhil","Ritu","Sameer","Diya","Manav","Pooja","Aditya","Farah","Gaurav","Lakshmi","Omkar","Sneha","Tarun"]
LAST  = ["Suresh","Patel","Iyer","Khan","Sharma","Nair","Desai","Reddy","Singh","Joshi","Menon","Gupta","Rao","Chauhan","Pillai"]
def _name(): return f"{random.choice(FIRST)} {random.choice(LAST)}"

TESTS = [
    {"id": 1, "name": "RRU Exam 09 Apr 2026", "sections": [
        {"id": 11, "name": "Section A - Single line answers", "max": 2,  "q_count": 9},
        {"id": 12, "name": "Section B - Short answers",       "max": 5,  "q_count": 5},
        {"id": 13, "name": "Section C Long Answers (Any 3)", "max": 10, "q_count": 4},
        {"id": 14, "name": "Section D - Define the term",    "max": 1,  "q_count": 24},
    ]},
    {"id": 2, "name": "RRU Mid-Term 22 Aug 2026", "sections": [
        {"id": 21, "name": "Section A - Short answers", "max": 5,  "q_count": 4},
        {"id": 22, "name": "Section B - Essays",        "max": 20, "q_count": 2},
    ]},
]

STEMMAP = {}
for t in TESTS:
    for s in t["sections"]:
        s["questions"] = []
        for i in range(s["q_count"]):
            qid = t["id"] * 10000 + s["id"] * 100 + i
            if s["id"] == 14:
                stem = f"Define the term: term {i+1}."
            elif s["id"] == 13 and i == 1:
                stem = ("Read the situation and answer. Ahead of a major public event, a state police force "
                        "receives fragmented warnings from three central agencies. Each agency uses a different "
                        "threat-grading scale, none shares its raw inputs, and the state control room has no "
                        "officer cleared to read two of the three reports. Critically assess the role of "
                        "intelligence sharing in India's internal security architecture, identify where "
                        "coordination is most likely to fail in this situation, and recommend two institutional "
                        "reforms, justifying each with a suitable example from the last two decades.")
            else:
                stem = f"Question {i+1} of {s['name']} — sample stem text for the demo."
            q = {"id": qid, "label": f"Q{i+1}", "stem": stem, "max_marks": s["max"]}
            s["questions"].append(q)
            STEMMAP[qid] = q

def _status_for(t):
    return {"graded": random.randint(40, 120), "pending": random.randint(10, 60),
            "on_hold": random.randint(0, 4), "terminated": random.randint(0, 8), "flagged": random.randint(0, 6)}

def build_tests_payload():
    return {"tests": [{"id": t["id"], "name": t["name"], "sections": [{"id": s["id"], "name": s["name"]} for s in t["sections"]]} for t in TESTS]}

def build_progress_payload(test_id, section_id):
    t = next((x for x in TESTS if x["id"] == test_id), TESTS[0])
    secs = t["sections"]
    if section_id: secs = [s for s in secs if s["id"] == section_id] or t["sections"]
    st = _status_for(t)
    total = st["graded"] + st["pending"] + st["on_hold"] + st["terminated"]
    bars = []
    for s in secs:
        for q in s["questions"]:
            bars.append({"label": q["label"], "question_id": q["id"], "graded": random.randint(2, 20), "pending": random.randint(0, 15), "on_hold": 0, "terminated": 0, "flagged": 0})
    return {
        "scope": "section" if section_id else "test", "test_id": t["id"], "test_name": t["name"],
        "total": total, "status": st, "flagged": st["flagged"],
        "sections": [{"id": s["id"], "name": s["name"], "questions": [{"id": q["id"], "label": q["label"], "stem": q["stem"], "max_marks": q["max_marks"]} for q in s["questions"]]} for s in secs],
        "bars": bars,
    }

def build_question_payload(question_id):
    q = STEMMAP.get(question_id) or next(iter(STEMMAP.values()))
    max_marks = q["max_marks"]
    n = random.randint(15, 60)
    raw = [max(0.0, min(max_marks, random.gauss(0.6 * max_marks, 0.18 * max_marks))) for _ in range(n)]
    raw.sort()
    scores = [round(x * 2) / 2 for x in raw]
    mean_v = sum(scores) / len(scores)
    med = scores[len(scores)//2] if len(scores) % 2 else (scores[len(scores)//2 - 1] + scores[len(scores)//2]) / 2
    var = sum((x - mean_v) ** 2 for x in scores) / len(scores)
    sd = math.sqrt(var)
    slabs = [{"low": round(max_marks * 0.2 * i, 2), "high": round(max_marks * 0.2 * (i + 1), 2), "count": 0, "pct": 0.0} for i in range(5)]
    for s in scores:
        idx = min(4, max(0, int(s / (max_marks * 0.2 + 1e-9))))
        slabs[idx]["count"] += 1
    for s in slabs: s["pct"] = s["count"] / n * 100
    middle_pct = (slabs[1]["count"] + slabs[2]["count"] + slabs[3]["count"]) / n * 100
    bias = "STRONG_BIAS" if middle_pct > 85 else "MILD_BIAS" if middle_pct > 70 else "NO_BIAS"
    t3 = n // 3
    early = sum(scores[:t3]) / t3
    mid = sum(scores[t3:2*t3]) / t3
    late = sum(scores[2*t3:]) / (n - 2*t3)
    dval = round(late - early, 1)
    state = "CRITICAL" if abs(dval) >= 2.0 else "WARNING" if abs(dval) >= 1.0 else "STABLE"
    out_rows = []
    for i, s in enumerate(scores):
        if mean_v - s >= 4.0:
            out_rows.append({"response_id": 80000 + i, "participant": _name(), "marks": s, "gap": round(mean_v - s, 2), "graded_at": (datetime(2026, 4, 12, 11, 0) + timedelta(minutes=7 * i)).strftime("%Y-%m-%d %H:%M")})
    out_rows.sort(key=lambda r: -r["gap"])
    section_averages = [{"label": qq["label"], "question_id": qq["id"], "avg_pct": round(random.uniform(45, 85), 1), "graded": random.randint(5, 40), "stem": qq["stem"], "max_marks": qq["max_marks"]} for t in TESTS for s in t["sections"] if any(qq["id"] == q["id"] for qq in s["questions"]) for qq in s["questions"]]
    return {
        "question_id": q["id"], "max_marks": max_marks, "graded_count": n, "mean": round(mean_v, 2), "median": round(med, 2), "sd": round(sd, 2), "highest": max(scores), "lowest": min(scores),
        "slabs": slabs, "middle_pct": round(middle_pct, 1), "bias": bias, "section_averages": section_averages,
        "drift": {"state": state, "early_avg": round(early, 2), "mid_avg": round(mid, 2), "late_avg": round(late, 2), "value": dval, "third_size": t3, "late_size": n - 2 * t3},
        "outliers": {"active": len(out_rows) > 0 or (max_marks > 4 and n >= 5), "session_avg": round(mean_v, 2), "rows": out_rows},
        "last_graded_at": (datetime(2026, 4, 12, 11, 40) + timedelta(minutes=n)).strftime("%Y-%m-%d %H:%M"),
    }

# --- API ROUTES ---
@app.route("/api/health")
def health(): return jsonify({"status": "ok", "mode": "DEMO"})

@app.route("/api/examiner/insights/tests")
def api_tests(): return jsonify(build_tests_payload())

@app.route("/api/examiner/insights/progress")
def api_progress():
    test_id = int(request.args.get("test_id", 1))
    section_id = request.args.get("section_id")
    return jsonify(build_progress_payload(test_id, int(section_id) if section_id else None))

@app.route("/api/examiner/insights/question")
def api_question(): return jsonify(build_question_payload(int(request.args.get("question_id", 0))))

# --- LOGIN & EXAM API ---
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    if data.get("username") == "admin" and data.get("password") == "password":
        return jsonify({"success": True, "token": "dummy-token-12345"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/api/exam/questions")
def get_exam_questions():
    safe_qs = [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in EXAM_QUESTIONS]
    return jsonify(safe_qs)

@app.route("/api/exam/submit", methods=["POST"])
def submit_exam():
    answers = request.json.get("answers", {})
    score = 0
    total = len(EXAM_QUESTIONS)
    
    review = []
    for q in EXAM_QUESTIONS:
        user_ans = answers.get(str(q["id"]), -1)
        is_correct = (user_ans == q["answer"])
        if is_correct: score += 1
        
        review.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "user_answer": user_ans,
            "correct_answer": q["answer"],
            "is_correct": is_correct
        })
        
    return jsonify({"score": score, "total": total, "passed": score >= (total * 0.6), "review": review})

@app.route("/")
@app.route("/index.html")
def index(): return send_file(os.path.join(PUBLIC_DIR, "index.html"), mimetype="text/html")

@app.route("/<path:filename>")
def static_files(filename): return send_from_directory(PUBLIC_DIR, filename)

if __name__ == "__main__":
    print(f"Server running at http://127.0.0.1:8000/")
    app.run(host="127.0.0.1", port=8000, debug=False)
