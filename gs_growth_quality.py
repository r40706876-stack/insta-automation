"""Growth-focused, deterministic pre-publication QA for GS Studio reels.

No fabricated analytics or promises of follower growth. Reports are stored beside
each reel. The gate blocks only missing teaching content, not subjective scores.
"""
import re

GENERIC_PROPS = ('cylinder', 'gear', 'sphere', 'cube', 'गियर', 'सिलेंडर', 'गोला')
QUESTION_MARKS = ('?', '？', 'कौन', 'क्यों', 'कैसे', 'क्या', 'किस', 'कहाँ')

def evaluate(script):
    scenes = script.get('scenes') or []
    speech = [str(s.get('speech') or '').strip() for s in scenes if isinstance(s, dict)]
    first = speech[0] if speech else ''
    question = (script.get('reference') or {}).get('question', '')
    cta = (script.get('share_card') or {}).get('cta', '')
    visual_warnings = []
    for i, scene in enumerate(scenes, 1):
        animation = scene.get('animation') or {}
        action = str(animation.get('visible_action') or '').lower()
        if any(word in action for word in GENERIC_PROPS):
            visual_warnings.append('Scene %d: check if moving shapes teach the actual topic' % i)
    blocking = []
    if not script.get('title'):
        blocking.append('missing title')
    if not speech or any(not x for x in speech):
        blocking.append('missing scene narration')
    if not question and not any(m in first for m in QUESTION_MARKS):
        blocking.append('no identifiable learning question')
    warnings = list(visual_warnings)
    if first and len(first) > 115:
        warnings.append('opening narration may be too long')
    if not cta:
        warnings.append('no explicit audience challenge')
    if not (script.get('recall') or script.get('reference', {}).get('explanation')):
        warnings.append('no revision takeaway')
    if not (script.get('share_reason') or (script.get('share_card') or {}).get('benefit')):
        warnings.append('no shareable benefit defined')
    return {
        'version': 'growth_qa_v1',
        'safe_to_publish': not blocking,
        'blocking_reasons': blocking,
        'warnings': warnings,
        'first_hook': first,
        'question': question,
        'revision_value': bool(script.get('recall') or script.get('reference', {}).get('explanation')),
        'share_value': bool(script.get('share_reason') or (script.get('share_card') or {}).get('benefit')),
        'follow_value': bool(script.get('series_next_topic')),
        'manual_visual_review_required': bool(visual_warnings),
        'note': 'This checks script metadata, not real viewer retention or visual accuracy.'
    }

def caption_addendum(script, report):
    card = script.get('share_card') or {}
    challenge = str(card.get('cta') or '').strip()
    recall = str(script.get('recall') or '').strip()
    parts = []
    if challenge:
        parts.append('💬 '+challenge)
    if recall:
        parts.append('📌 रिवीजन: '+recall)
    if report['share_value']:
        parts.append('📤 अपने स्टडी पार्टनर से यही सवाल पूछो।')
    next_topic = str(script.get('series_next_topic') or '').strip()
    if next_topic:
        parts.append('📅 अगला सवाल: '+next_topic+' — मिस न करने के लिए Follow करें।')
    return '\\n\\n'+'\\n'.join(parts) if parts else ''
