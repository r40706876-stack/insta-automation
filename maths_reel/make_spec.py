"""Roz ki Maths reel ka spec: NTPC Maths PYQ bank se ek naya sawal (har din alag topic) -> steps.html wala spec.
Sab kuch bank ke sawal, options, book ki vyakhya (explanation) aur tip se banta hai - koi AI likha hal nahi.

Usage: python maths_reel/make_spec.py OUT.json [YYYY-MM-DD] [question_id]
"""
import json, os, re, sys, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = os.path.join(ROOT, "pyq_banks", "ntpc_maths.json")
POSTED = os.path.join(HERE, "posted.json")

# topic -> (screen name, hook symbol, orbit symbols, hashtag)
TOPICS = [
    ("प्रतिशत (Percentage)", "प्रतिशत", "%", ["%", "×", "100", "="], "Percentage"),
    ("लाभ एवं हानि (Profit & Loss)", "लाभ-हानि", "₹", ["₹", "%", "+", "−"], "ProfitAndLoss"),
    ("औसत (Average)", "औसत", "x̄", ["Σ", "÷", "+", "="], "Average"),
    ("अनुपात एवं समानुपात (Ratio & Proportion)", "अनुपात", "a:b", [":", "×", "÷", "="], "Ratio"),
    ("साधारण ब्याज (Simple Interest)", "साधारण ब्याज", "SI", ["₹", "%", "×", "÷"], "SimpleInterest"),
    ("आयु संबंधी प्रश्न (Problems on Age)", "आयु", "x+6", ["x", "+", "=", "−"], "AgeProblems"),
    ("बट्टा / छूट (Discount)", "छूट", "−%", ["₹", "%", "−", "="], "Discount"),
    ("समय एवं कार्य (Time & Work)", "समय और कार्य", "1/x", ["÷", "+", "×", "="], "TimeAndWork"),
    ("क्षेत्रमिति (Mensuration)", "क्षेत्रमिति", "π", ["r²", "×", "√", "="], "Mensuration"),
    ("सरलीकरण (Simplification)", "सरलीकरण", "÷×", ["+", "−", "×", "÷"], "Simplification"),
    ("चक्रवृद्धि ब्याज (Compound Interest)", "चक्रवृद्धि ब्याज", "CI", ["₹", "%", "²", "="], "CompoundInterest"),
    ("समय, चाल एवं दूरी (Time, Speed & Distance)", "चाल-दूरी", "km/h", ["÷", "×", "=", "→"], "SpeedDistance"),
    ("ज्यामिति (Geometry)", "ज्यामिति", "△", ["°", "+", "=", "∠"], "Geometry"),
    ("बीजगणित (Algebra)", "बीजगणित", "x²", ["x", "y", "+", "="], "Algebra"),
    ("सांख्यिकी (Statistics)", "सांख्यिकी", "Σ", ["÷", "+", "n", "="], "Statistics"),
    ("साझेदारी (Partnership)", "साझेदारी", "₹:₹", [":", "×", "₹", "="], "Partnership"),
    ("संख्या पद्धति (Number System)", "संख्या पद्धति", "123", ["÷", "×", "+", "="], "NumberSystem"),
]
HOOKS = [
    "ये ट्रिक नहीं पता तो सवाल गया!",
    "10 सेकंड में हल करो!",
    "NTPC में आया, फिर आएगा!",
    "ज़्यादातर यहीं गलती करते हैं!",
    "सबसे छोटा तरीका देखो!",
]
WARN = ["अटक जाते हैं!", "गलती करते हैं!", "समय गँवाते हैं!"]


def parts_of(exp):
    """Book ki vyakhya ' / ' se steps; har step '→' par chhoti lines me."""
    steps = []
    for p in re.split(r"\s+/\s+", (exp or "").strip()):
        p = p.strip().rstrip(".।").strip()
        if not p:
            continue
        lines = [x.strip() for x in re.split(r"\s*→\s*|,\s*तो\s+|।\s+", p) if x.strip()]
        steps.append({"lines": lines})
    return steps


def usable(q):
    o = list(q["options"].values())
    st = parts_of(q.get("explanation"))
    if not (len(q["question"]) <= 200 and all(len(x) <= 14 for x in o) and 2 <= len(st) <= 5 and q.get("tip")):
        return False
    if any(len(l) > 80 for s in st for l in s["lines"]) or sum(len(s["lines"]) for s in st) > 8:
        return False
    if re.search(r"_{3,}|निम्न|कथन|चित्र|आकृति|ग्राफ|तालिका", q["question"]):
        return False
    # safety: the answer's number must actually come out of the book's working
    ans = q["options"].get(q["answer"], "")
    num = re.sub(r"[,\s]", "", re.sub(r"[^\d.,/:]", " ", ans)).strip(".")
    work = re.sub(r"[,\s]", "", q.get("explanation", ""))
    return bool(num) and num in work


def speak(t):
    """Gemini/Edge ko hisaab ki line bolne layak banana."""
    sup = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
    t = re.sub(r"([A-Za-z0-9)])²", r"\1 का वर्ग", t)
    t = re.sub(r"([A-Za-z0-9)])³", r"\1 का घन", t)
    t = re.sub(r"([A-Za-z0-9)])([⁰¹⁴⁵⁶⁷⁸⁹⁻⁺]+)", lambda m: m.group(1) + " की घात " + m.group(2).translate(sup), t)
    t = re.sub(r"(\d)\s*%", r"\1 प्रतिशत", t)
    t = re.sub(r"₹\s*([\d,.]+)", r"\1 रुपये", t)
    reps = [("→", ", यानी "), ("⇒", ", यानी "), ("∴", "इसलिए "), ("=", " बराबर "), ("×", " गुणा "), ("÷", " भाग "),
            ("√", " वर्गमूल "), ("π", " पाई "), ("−", " माइनस "), ("+", " प्लस "), ("∠", " कोण "), ("°", " डिग्री"),
            ("Σ", " योग "), ("x̄", " औसत ")]
    for a, b in reps:
        t = t.replace(a, b)
    t = re.sub(r"(\d)\s*/\s*(\d)", r"\1 बटा \2", t)
    t = re.sub(r"\s+/\s+", " भाग ", t)
    t = re.sub(r"(?<=[\w)])\s+-\s+(?=[\w(])", " माइनस ", t)
    t = re.sub(r"(?<=[\d.])\s*\((?=[\d.]+\))", " गुणा (", t)
    t = re.sub(r"(?<=\d)\s*:\s*(?=\d)", " अनुपात ", t)
    t = t.replace(":", ",")
    return " ".join(t.replace("(", " ").replace(")", " ").split())


def posted():
    try:
        return set(json.load(open(POSTED)))
    except Exception:
        return set()


def build(q, topic, day):
    L = "ABCD"
    keys = ["a", "b", "c", "d"]
    opts = [q["options"][k] for k in keys]
    ai = keys.index(q["answer"])
    steps = parts_of(q["explanation"])
    name, sym, sats, tag = topic[1], topic[2], topic[3], topic[4]
    h = int(hashlib.md5(q["id"].encode()).hexdigest(), 16)
    hook2 = HOOKS[h % len(HOOKS)]
    tip = q["tip"].strip().rstrip(".।")
    exam = (q.get("exams") or ["RRB NTPC 2025-26"])[0].split(" (")[0]
    voice = [
        f"{name} का ये सवाल RRB NTPC में आया था... {hook2}",
        "सवाल ध्यान से सुनो। " + speak(q["question"]) + " ऑप्शन हैं: "
        + ", ".join(f"{L[i]}, {speak(o)}" for i, o in enumerate(opts)) + "। पहले खुद सोचो!",
    ]
    for i, s in enumerate(steps):
        lead = ["पहले", "अब", "फिर", "अब", "आखिर में"][i] if i < len(steps) - 1 else "तो"
        voice.append(lead + ", " + speak(", ".join(s["lines"])) + "।")
    voice.append(f"सही जवाब है, ऑप्शन {L[ai]}... {speak(opts[ai])}!")
    voice.append("याद रखो, " + speak(tip) + "। सही जवाब मिला? कमेंट करो, और ऐसी ही ट्रिक्स के लिए फॉलो करो Minute Me GS!")
    return {
        "template": "steps.html", "brand": "MinuteMe_GS", "exam": exam, "subject": "Maths",
        "bank_id": q["id"], "chapter": q["chapter"], "topic": name, "date": day,
        "symbol": sym, "symbols": sats, "emoji": "🧮", "tags": ["#" + tag, "#MathsTricks"],
        "title": f"{name} PYQ: " + (q["question"][:70].rsplit(" ", 1)[0] + "…" if len(q["question"]) > 70 else q["question"]) + " 🧮 | RRB NTPC",
        "hook": [name + " का PYQ", hook2], "hook_sub": f"{exam} का सवाल · स्टेप-बाय-स्टेप हल",
        "warn": WARN[h % len(WARN)],
        "question_hi": q["question"], "question_en": q.get("question_en", ""),
        "options": opts, "answer": L[ai], "steps": steps, "result": opts[ai],
        "trick": [tip], "cta": "रोज़ 1 Maths PYQ + शॉर्टकट", "voice": voice,
    }


def main():
    out = sys.argv[1]
    day = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat()
    want = sys.argv[3] if len(sys.argv) > 3 else ""
    qs = json.load(open(BANK, encoding="utf-8"))["questions"]
    done = posted()
    if want:
        q = next(x for x in qs if x["id"] == want)
        topic = next((t for t in TOPICS if t[0] == q["chapter"]), (q["chapter"], q["chapter"].split(" (")[0], "?", ["+", "−", "×", "="], "Maths"))
    else:
        n = (datetime.date.fromisoformat(day) - datetime.date(2026, 11, 14)).days
        for k in range(len(TOPICS)):              # day's topic; if it has nothing left, the next one
            topic = TOPICS[(n + k) % len(TOPICS)]
            cand = [x for x in qs if x["chapter"] == topic[0] and x["id"] not in done and usable(x)]
            if cand:
                cand.sort(key=lambda x: (-int(x.get("times_asked") or 1), x.get("seq", 0)))
                q = cand[0]
                break
        else:
            sys.exit("koi naya sawal nahi bacha")
    spec = build(q, topic, day)
    json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("SPEC", q["id"], topic[1], "|", q["question"][:70])


if __name__ == "__main__":
    main()
