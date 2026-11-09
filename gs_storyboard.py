"""Source-locked Hindi narration; the visual planner cannot invent spoken facts."""
import re
ROLES=('hook','challenge','reveal','explain','transfer','revision')
HEADINGS=('सवाल देखिए','अपना जवाब चुनिए','सही उत्तर','तथ्य समझिए','खुद को जाँचिए','रिवीजन कार्ड')
def grounded_facts(explanation):
    return [s.strip()+'।' for s in re.split(r'[।!?]|(?<!\d)\.(?!\d)',str(explanation)) if 3<=len(s.split())<=25]

def grounded_storyboard(reference,format_name=None):
    question=re.sub(r'^[a-z0-9_-]+:\s*','',str(reference.get('question','')).strip())
    options=reference.get('options') or {};key=reference.get('answer')
    if not question or key not in options:raise ValueError('Grounded question and answer required')
    answer=str(options[key]).strip().rstrip('।.')
    facts=grounded_facts(reference.get('explanation',''))
    if not facts:raise ValueError('A complete concise source explanation is required')
    other=next((str(v).strip().rstrip('।.') for k,v in options.items() if k!=key),None)
    # Keep one coherent question: no second generic spoken hook before the answer.
    # Comment pause: ask for A/B in the comments before the reveal (comments were ~0).
    choices='दो सेकंड सोचिए: A या B?' if other else 'दो सेकंड सोचिए।'
    displayed=[answer,other] if other else [answer]
    if other and sum(question.encode())%2:displayed.reverse()
    if other:displayed=['A: '+displayed[0],'B: '+displayed[1]]
    # Lead with the question itself, then vary the short challenge by experiment.
    # Format diversity matters for controlled A/B testing without generic preambles.
    prompt_tail={'exam_trap':' जाल पहचानिए।',
                 'visual_mystery':' दृश्य देखिए।',
                 'map_pyq_challenge':' नक्शा देखिए।'}.get(format_name,'')
    # 4 Nov: studio reels ran 32-35 s while top reels were 21-25 s (watched 12-15 s).
    # Keep every role but speak less: question only, one short fact, a quick recall line.
    opening=question+prompt_tail if len((question+prompt_tail).split())<=25 else question
    # Short explanation (<=12 words) keeps the reel ~25 s and subtitles whole.
    short=[f for f in facts if len(f.split())<=12]
    explain=short[0] if short else min(facts,key=lambda f:len(f.split()))
    rest=[f for f in facts if f!=explain]
    transfer=rest[0] if rest and len(rest[0].split())<=6 else 'यही परीक्षा की आम गलती है।'
    # Avoid repeating the full answer in the final scene; add new value or finish early.
    recall='याद रखने की ट्रिक: '+answer+'।' if rest else 'अगली बार यह गलती मत कीजिए।'
    speech=[opening,choices,'सही उत्तर है: '+answer+'।',explain,transfer,recall]
    if any(len(line.split())>25 for line in speech):raise ValueError('Question/options exceed readable scene limits')
    result=[{'role':role,'heading':heading,'speech':line,'explanation':(' '.join(line.split()[:6]))} for role,heading,line in zip(ROLES,HEADINGS,speech)]
    # Top reels (Map Test 01, हथौड़ा, समुद्री हवा) showed the FULL question and both options
    # in frame 0. The hook now carries them; the compositor draws them large.
    result[0]['heading']='पहले अपना जवाब चुनिए'
    result[0]['explanation']='A या B — सोचिए' if other else 'पहले खुद सोचिए'
    result[0]['hook_question']=question
    if other:result[0]['quiz_options']=displayed
    result[1]['heading']='कमेंट में लिखिए: A या B?' if other else result[1]['heading']
    result[1]['quiz_options']=displayed
    # Duration is driven by spoken words, not an arbitrary fixed scene length.
    # Downstream TTS/renderer still owns the final measured duration.
    result[0]['content_group']='single_topic'
    return result
