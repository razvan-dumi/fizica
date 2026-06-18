"""Extract questions from mock.docx -> questions.json.

Real text, no OCR. Numbering/list formatting is inconsistent across the three exam
sections, but two rules hold throughout:
  - A STEM is a paragraph whose (cleaned) text ends in ':', '?' or '...'.
  - Choices are the lines after a stem, up to the next stem.
The correct choice is shaded blue (fill 9EC4E7); other fills are stray noise.
Open-ended/bullet blocks (Avantaje/Dezavantaje/Explicați/Date generale/Exerciții) and
image captions are skipped. Section C repeats questions, so we dedupe by content.
"""
import re, json, zipfile, unicodedata
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CORRECT_FILL = "9EC4E7"

with zipfile.ZipFile("mock.docx") as z:
    body = ET.fromstring(z.read("word/document.xml")).find(W + "body")

def ptext(p):
    return "".join(t.text or "" for t in p.iter(W + "t")).strip()

def fills(p):
    return [shd.get(W + "fill") for shd in p.iter(W + "shd")
            if shd.get(W + "fill") and shd.get(W + "fill") != "auto"]

SECTIONS = {0: "Acustica & Iluminat (ATE)", 492: "Fizica Constructiilor 2", 896: "Teste Fizica Constructiilor"}
def exam_for(i, _k=sorted(SECTIONS)):
    name = SECTIONS[_k[0]]
    for k in _k:
        if i >= k:
            name = SECTIONS[k]
    return name

LETTER = re.compile(r"^[a-eA-E][\)\.]\s*")
# Single-line junk (captions, page markers, section titles) — ignored, no run started.
LINE_NOISE = re.compile(r"(^(Pagina\s*\d+|SUBIECT|TEXT EXTRAS|GRILE ACUSTICA|Teste Fizica|POZA\b|Not[ăa]\b))"
                        r"|(\.(jpe?g|png)$)", re.I)
# Headers that introduce a run of non-question bullets — skip until the next real stem.
BULLET_NOISE = re.compile(r"^(Avantaje|Dezavantaje|❌|✅|Ex?plica|Date generale|Exerci|Instruc|I+\.\s)", re.I)

def clean_stem(t):
    t = re.split(r"\s+/\s+", t)[0]            # drop "/ ANNOTATION" tails
    t = re.sub(r"^\d+[\.\)]\s*", "", t)        # drop leading "3. "
    return t.strip()

def clean_choice(t):
    return LETTER.sub("", t).strip()           # drop leading "a) "

def stem_text(t):
    c = clean_stem(t)
    if c.endswith(":") or c.endswith("?") or c.endswith("…") or c.endswith("..."):
        return c
    return None

# Some paragraphs glue a stem to its (often shaded) first choice, e.g.
# "Metoda statica Glaser...vaporilor:ofera doar o indicatie". Split those so the
# stem isn't misread as a choice of the previous question.
GLUED = re.compile(r"^([A-ZȘȚĂÂÎ].{10,}?[:?])\s*(\S.+)$")
def glued_split(t):
    if stem_text(t):                      # a clean stem (nothing after the colon)
        return None
    m = GLUED.match(t)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()

paras = list(body.iter(W + "p"))
questions = []
cur = None
skipping = False

merged_dropped = []

def flush():
    global cur
    if cur and len(cur["choices"]) >= 2:
        # More than one blue choice = two questions merged by a missing-':' stem typo.
        # These are un-splittable; drop them (the content recurs elsewhere in the doc).
        if sum(1 for c in cur["choices"] if CORRECT_FILL in c["fills"]) > 1:
            merged_dropped.append(cur["stem"])
            cur = None
            return
        ci = next((i for i, c in enumerate(cur["choices"]) if CORRECT_FILL in c["fills"]), None)
        if ci is None:
            ci = next((i for i, c in enumerate(cur["choices"]) if c["fills"]), None)
        cur["correctIndex"] = ci
        questions.append(cur)
    cur = None

for i, p in enumerate(paras):
    t = ptext(p)
    if not t or LINE_NOISE.search(t):
        continue
    g = glued_split(t)
    if g is not None:
        skipping = False
        flush()
        cur = {"exam": exam_for(i), "stem": g[0], "choices": [{"text": clean_choice(g[1]), "fills": fills(p)}]}
        continue
    st = stem_text(t)
    if st is not None:
        skipping = False
        flush()
        cur = {"exam": exam_for(i), "stem": st, "choices": []}
    elif BULLET_NOISE.match(t):
        flush(); cur = None; skipping = True
    elif not skipping and cur is not None:
        cur["choices"].append({"text": clean_choice(t), "fills": fills(p)})
flush()

# --- dedupe + drop unanswered, assign global ids ---
def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

final, seen, no_answer = [], set(), []
for q in questions:
    if q["correctIndex"] is None:
        no_answer.append(q["stem"]); continue
    key = norm(q["stem"]) + "||" + norm(q["choices"][0]["text"])
    if key in seen:
        continue
    seen.add(key)
    final.append({
        "id": len(final) + 1,
        "exam": q["exam"],
        "question": q["stem"],
        "choices": [c["text"] for c in q["choices"]],
        "correctIndex": q["correctIndex"],
    })

with open("questions.json", "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)

from collections import Counter
print("questions written:", len(final))
print("by exam:", dict(Counter(q["exam"] for q in final)))
print("choices distribution:", dict(sorted(Counter(len(q["choices"]) for q in final).items())))
print("dropped (no shaded answer):", len(no_answer), [s[:40] for s in no_answer])
print("dropped (merged multi-answer):", len(merged_dropped), [s[:40] for s in merged_dropped])
