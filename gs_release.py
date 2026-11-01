"""Fail closed on missing rendered QA; subjective checks require explicit review."""
import hashlib
import json
from pathlib import Path
from gs_scene_policy import is_revision_card,validate_revision_duration
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
    seconds=audio.get('seconds') or []
    scenes=script.get('scenes',[])
    revision=checks.get('static_revision_checks') or {}
    if len(seconds)!=len(scenes) or any(not isinstance(s,(int,float)) or s<2 for s in seconds):errors.append('scene reading/listening time missing or below 2 seconds')
    for index,scene in enumerate(scenes):
        key='scene_'+str(index+1)
        if is_revision_card(scene,index,len(scenes)):
            try:
                validate_revision_duration(seconds[index])
                receipt=revision.get(key,{})
                if receipt.get('bounded_revision_card') is not True or receipt.get('seconds')!=seconds[index]:errors.append('revision duration receipt missing')
            except (ValueError,IndexError):errors.append('revision card exceeds measured duration limit')
        elif motion.get(key+'_teaching_motion',{}).get('changed_fraction',0)<=.001:
            # Historic single-scene test fixtures also use the same indexed prefix.
            if motion.get(key,{}).get('changed_fraction',0)<=.001:errors.append('rendered scene motion evidence incomplete: '+key)
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
