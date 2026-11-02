"""Regression: real AV reviewer rejected a water/village analogy for sky scattering."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gs_animation_studio"))
from planner import repair_sky_scattering, normalize_layout, validate_sky_scattering

def test_sky_scattering_replaces_unrelated_props():
    scenes = [{"role": role, "setting": "village", "objects": [
        {"kind": "water", "action": "flow", "label": "पानी"}
    ]} for role in ("hook", "challenge", "reveal", "explain", "transfer", "revision")]
    p = repair_sky_scattering({"scenes": scenes}, "आकाश नीला क्यों दिखाई देता है?")
    p, _ = normalize_layout(p)
    validate_sky_scattering(p, "आकाश नीला क्यों दिखाई देता है?")
    assert p["scenes"][0]["setting"] == "space"
    assert "नीला" not in " ".join(o["label"] for o in p["scenes"][0]["objects"])
    assert p["scenes"][4]["setting"] == "laboratory"
    assert all(o["kind"] != "water" for scene in (p["scenes"][3],p["scenes"][4]) for o in scene["objects"])
    blue = next(o for o in p["scenes"][4]["objects"] if "नीला" in o["label"])
    red = next(o for o in p["scenes"][4]["objects"] if "लाल" in o["label"])
    assert blue["color"] == "#2563eb"
    assert red["color"] == "#ef4444"
    assert blue["to"][2] > blue["pos"][2]
    assert red["to"][0] > red["pos"][0]

def test_other_subject_not_changed():
    p = {"scenes": [{"objects": [{"kind": "water"}]}]}
    assert repair_sky_scattering(p, "गंगा नदी कहाँ बहती है?") is p
