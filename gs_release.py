"""Fail closed on missing rendered QA; subjective checks require explicit review."""
import hashlib
import json
from pathlib import Path
REVIEW_CHECKS=('answer_correct','visual_relevance','hindi_readable','pronunciation_correct','audio_visual_match','answer_reveal_timing','revision_card_readable')

def evaluate_release(root,script):
    root=Path(root);errors=[]
    video=root/'reel.mp4'
    digest=hashlib.sha256(video.read_bytes()).hexdigest() if video.exists() else None
    def read(name):
        try:return json.loads((root/name).read_text())
        except (OSError,ValueError):return {}
    checks=read('file_checks.json');review=read('release_review.json');audio=read('audio.json')
    if not digest or checks.get('sha256')!=digest:errors.append('missing or stale rendered QA')
    if checks.get('decoded_without_errors') is not True or checks.get('black_intervals')!=0:errors.append('decode/black-frame QA missing or failed')
    if checks.get('dimensions') not in ([720,1280],[1080,1920]):errors.append('unsupported portrait dimensions')
    motion=checks.get('actual_rendered_motion_checks') or {}
    if len(motion)<len(script.get('scenes',[])) or any(v.get('changed_fraction',0)<=.001 for v in motion.values()):errors.append('rendered scene motion evidence incomplete')
    seconds=audio.get('seconds') or []
    if len(seconds)!=len(script.get('scenes',[])) or any(s<2 for s in seconds):errors.append('scene reading/listening time missing or below 2 seconds')
    if not isinstance(checks.get('audio_mean_db'),(float,int)) or checks['audio_mean_db']<=-35:errors.append('audio missing or too quiet')
    if audio.get('speech')!=[s.get('speech') for s in script.get('scenes',[])]:errors.append('rendered narration differs from script')
    if script.get('experiment_format') and tuple(s.get('role') for s in script.get('scenes',[]))!=('hook','challenge','reveal','explain','transfer','revision'):errors.append('experiment scene roles invalid')
    if review.get('sha256')!=digest or not review.get('reviewer') or not review.get('reviewed_at'):errors.append('rendered review missing or stale')
    for key in REVIEW_CHECKS:
        if review.get(key) is not True:errors.append('unverified '+key)
    return {'safe_to_publish':not errors,'blocking_reasons':errors,'sha256':digest,'version':'rendered_release_v1'}

def compact_caption(script):
    from gs_growth_quality import caption_addendum
    from gs_growth_quality import evaluate
    title=str(script.get('title','')).strip()
    return title+caption_addendum(script,evaluate(script))+'\n\n#MinuteMeGS #GS #StudyHindi #SSC #RailwayExam'
