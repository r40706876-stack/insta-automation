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
    reference=script.get('reference') or {}
    if reference.get('answer') not in (reference.get('options') or {}):
        blocking.append('reference answer is not a valid option')
    if not reference.get('explanation'):
        blocking.append('missing grounded answer explanation')
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
    """Every visual reel asks for a comment, a share and a follow (data: 7 comments and
    32 shares on 23,631 views; captions without these lines got ~0)."""
    recall = str(script.get('recall') or '').strip()
    options = [o for s in (script.get('scenes') or []) for o in (s.get('quiz_options') or [])]
    parts = []
    if len(set(options)) >= 2:
        parts.append('💬 पहले बिना देखे जवाब कमेंट करो: A या B?')
    parts.append('📤 उस दोस्त को भेजो जो कहता है "मुझे GS आता है" — देखो वो सही बताता है या नहीं!')
    if recall:
        parts.append('📌 रिवीजन: '+recall)
    next_topic = str(script.get('series_next_topic') or '').strip()
    if next_topic:
        parts.append('📅 अगला सवाल: '+next_topic+' — Follow करो ताकि छूटे नहीं।')
    else:
        parts.append('⏱ रोज़ 1 चौंकाने वाला GS सवाल — Follow करो @MinuteMe_GS')
    return '\n\n'+'\n'.join(parts)
