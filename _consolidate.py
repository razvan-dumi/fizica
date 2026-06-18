import json, re, unicodedata

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()

def valid(q):
    ch = q.get("choices") or []
    ci = q.get("correctIndex", -1)
    return len(ch) >= 2 and isinstance(ci, int) and 0 <= ci < len(ch)

exams = [
    ("Acustica & Iluminat (ATE)", ["_raw/a1.json", "_raw/a2.json"], "number"),
    ("Fizica Constructiilor",       ["_raw/b3.json", "_raw/b4.json"], "content"),
    ("Acustica & Termotehnica",     ["_raw/c5.json", "_raw/c6.json"], "content"),
]

out = []
gidx = 1
for exam_name, files, mode in exams:
    seen = set()
    for fp in files:
        for q in load(fp):
            if not valid(q):
                continue
            if mode == "number":
                key = q["index"]
            else:
                key = norm(q["question"]) + "||" + norm(q["choices"][0])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "id": gidx,
                "exam": exam_name,
                "question": q["question"].strip(),
                "choices": [c.strip() for c in q["choices"]],
                "correctIndex": q["correctIndex"],
            })
            gidx += 1

# Final guard: drop any cross-exam exact duplicate (same stem+first choice)
final, seen_all = [], set()
for q in out:
    k = norm(q["question"]) + "||" + norm(q["choices"][0])
    if k in seen_all:
        continue
    seen_all.add(k)
    q["id"] = len(final) + 1
    final.append(q)

with open("questions.json", "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)

from collections import Counter
by_exam = Counter(q["exam"] for q in final)
print(f"TOTAL questions: {len(final)}")
for e, n in by_exam.items():
    print(f"  {e}: {n}")
print("choices distribution:", Counter(len(q['choices']) for q in final))
