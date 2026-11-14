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
    # " / " separates steps in the book, but "5406 / (1.5 × 0.68)" is division: keep those (digit or ")" before, digit or "(" after; brackets open)
    exp, chunks, cur, depth = (exp or "").strip(), [], "", 0
    for i, ch in enumerate(exp):
        depth += (ch == "(") - (ch == ")")
        if exp[i:i + 3] == " / " and depth == 0 and (re.match(r"[\d.]+%\s*=", exp[i + 3:]) or not (re.search(r"[\d)]$", exp[:i]) and re.match(r"[\d(]", exp[i + 3:]))):
            chunks.append(cur); cur = ""; continue
        if chunks and cur == "" and exp[i - 2:i + 1] == " / ":
            continue
        cur += ch
    chunks.append(cur)
    for p in [c.lstrip("/ ") for c in chunks]:
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
    t = re.sub(r"₹\s*([\d,.]+)", r"\1 रुपये", t).replace("(₹ में)", "रुपये में").replace("₹", "रुपये")
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


NUM = re.compile(r"\d+(?:\.\d+)?")


def teach(q, steps):
    """Gemini se 'teacher' wali samjhaish: har step KYUN kar rahe hain. Hisaab book ka hi rehta hai;
    Gemini koi naya number nahi la sakta (check), warna None -> purana tarika (sirf padhna)."""
    sys.path.insert(0, ROOT)
    try:
        import auto_poster as ap
    except Exception as exc:
        print("teach: auto_poster import nahi hua", exc); return None
    book = "\n".join(f"स्टेप {i + 1}: " + " → ".join(st["lines"]) for i, st in enumerate(steps))
    opts = ", ".join(f"{k.upper()}) {v}" for k, v in q["options"].items())
    prompt = f"""तुम एक बहुत अच्छे Maths टीचर हो जो Railway/SSC के कमज़ोर बच्चों को समझाते हो।
सवाल: {q["question"]}
ऑप्शन: {opts}   सही जवाब: {q["answer"].upper()}) {q["options"][q["answer"]]}
किताब का हल ({len(steps)} स्टेप):
{book}
किताब की टिप: {q.get("tip", "")}

काम: बच्चे को ऐसे समझाओ कि अगली बार ऐसा सवाल वो खुद कर ले। हर स्टेप में बताओ कि ये स्टेप हम क्यों कर रहे हैं (सोच/तर्क),
और जो भी नया नंबर आए वो कहाँ से आया (जैसे "50% लाभ मतलब 100 का 150, यानी 1.5 गुना")। सिर्फ़ हिसाब पढ़ो मत।
नियम:
- स्टेप ठीक {len(steps)} ही रहें, उसी क्रम में; हिसाब और नंबर किताब वाले ही; कोई नया नंबर/हिसाब मत बनाओ।
- सरल बोलचाल की हिंदी (देवनागरी), जैसे टीचर बोर्ड पर समझाता है। गणित के चिन्ह शब्दों में: बराबर, गुणा, भाग, प्लस, माइनस, प्रतिशत।
- "approach": 1 वाक्य - ये किस तरह का सवाल है और इसकी चाबी क्या है (≤ 20 शब्द)।
- हर स्टेप में "why": स्क्रीन के लिए छोटी लाइन (≤ 45 अक्षर) - ये स्टेप क्यों / नंबर कहाँ से; "say": बोलने के लिए 2-3 छोटे वाक्य (≤ 50 शब्द) - क्यों + नंबर कहाँ से आया + क्या हिसाब।
- नंबर हमेशा अंकों में लिखो (50, 1.5), शब्दों में नहीं।
- "rule": ≤ 60 अक्षर - ऐसे सवाल आएँ तो पहले क्या करें (याद रखने लायक नियम)।
सिर्फ़ JSON: {{"approach": "...", "steps": [{{"why": "...", "say": "..."}}], "rule": "..."}}"""
    import signal
    class _Late(BaseException): pass          # BaseException: Gemini helpers ke "except Exception" ise nahi pakadte
    def _late(*_): raise _Late("teach > 180s")
    signal.signal(signal.SIGALRM, _late); signal.alarm(180)      # Gemini kabhi latak jaata hai: max 3 min
    try:
        js = ap._gemini_call(prompt)
    except _Late as exc:
        print("teach:", exc); js = None
    finally:
        signal.alarm(0)
    if not js or len(js.get("steps") or []) != len(steps) or not js.get("approach") or not js.get("rule"):
        print("teach: Gemini ka jawab theek nahi"); return None
    allowed = set(NUM.findall(" ".join([q["question"], *q["options"].values(), q.get("explanation", ""), q.get("tip", "")])))
    allowed |= {str(i) for i in range(0, 11)} | {"100"}
    text = " ".join([js["approach"], js["rule"]] + [x.get("why", "") + " " + x.get("say", "") for x in js["steps"]])
    new = [n for n in NUM.findall(text) if n not in allowed and n.rstrip("0").rstrip(".") not in allowed]
    if new:
        print("teach: Gemini ne naye number likhe", new[:5], "-> purana tarika"); return None
    if any(len(x.get("why", "")) > 70 or not x.get("say") for x in js["steps"]) or len(js["rule"]) > 90:
        print("teach: lines bahut lambi"); return None
    return js


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
    T = teach(q, steps)
    if T:   # samjhao: har step ka "kyun" screen par bhi, awaaz me bhi
        for i, s in enumerate(steps):
            s["why"] = T["steps"][i]["why"].strip()
            voice.append(("समझो, " + T["approach"].strip() + " " if i == 0 else "") + speak(T["steps"][i]["say"].strip()))
        rule = T["rule"].strip().rstrip("।")
        trick = [rule, tip] if rule != tip else [tip]
        voice.append(f"सही जवाब है, ऑप्शन {L[ai]}... {speak(opts[ai])}!")
        voice.append("ऐसे सवाल आएँ तो याद रखो, " + speak(rule) + "। सही जवाब मिला? कमेंट करो, और ऐसी ही ट्रिक्स के लिए फॉलो करो Minute Me GS!")
    else:
        for i, s in enumerate(steps):
            lead = ["पहले", "अब", "फिर", "अब", "आखिर में"][i] if i < len(steps) - 1 else "तो"
            voice.append(lead + ", " + speak(", ".join(s["lines"])) + "।")
        trick = [tip]
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
        "trick": trick, "approach": (T or {}).get("approach", ""), "cta": "रोज़ 1 Maths PYQ + शॉर्टकट", "voice": voice,
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
