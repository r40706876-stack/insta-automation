"""Opt-in experiment selection. Never changes protected production inputs."""
import hashlib
import re
import unicodedata

WEAK = frozenset(("weak_polity","weak_biology","economics","chemistry","misc_gk","weekly_revision","weak_single_pyq"))
TESTS = ("question_selection","first_frame","voice_onset","duration","educational_animation","question_sequence")

def normalize(text):
    return re.sub(r"[^\w\u0900-\u097f]+", "", unicodedata.normalize("NFKC", str(text)).casefold())

def fingerprint(questions):
    return hashlib.sha256("\n".join(sorted(normalize(q["question"]) for q in questions)).encode()).hexdigest()

def select(cohort, questions, *, test, variant, seen=()):
    """Explicit weak cohort only. Returns unchanged input for every other cohort."""
    if cohort not in WEAK:
        return questions, {"enabled": False}
    if test not in TESTS or variant not in ("control","treatment"):
        raise ValueError("Unknown experiment or variant")
    if not questions or any(not normalize(q.get("question","")) for q in questions):
        raise ValueError("Missing question")
    ids = [normalize(q["question"]) for q in questions]
    if len(set(ids)) != len(ids) or fingerprint(questions) in seen:
        raise ValueError("Duplicate question or set")
    result = list(questions)
    config = {"enabled": True, "test":test,"variant":variant,"publish":False}
    if variant == "treatment":
        if test == "question_selection":
            # Human/source-reviewed familiarity is required; never infer it from length alone.
            if any("familiarity" not in q for q in result):
                raise ValueError("Reviewed familiarity score required")
            result.sort(key=lambda q: (-float(q["familiarity"]),len(q["question"].split())))
        elif test == "question_sequence":
            if any(not q.get("chapter") for q in result):
                raise ValueError("Source chapter required")
            if len({q["chapter"] for q in result}) != 1:
                raise ValueError("Treatment requires a single chapter")
        elif test == "first_frame":
            config["first_frame"] = "question_and_relevant_visual"
        elif test == "voice_onset":
            config["max_voice_onset_seconds"] = 0.25
        elif test == "duration":
            config["target_seconds"] = [20,25]
        elif test == "educational_animation":
            config["visual_mode"] = "source_grounded_educational"
    config["fingerprint"] = fingerprint(result)
    return result, config
