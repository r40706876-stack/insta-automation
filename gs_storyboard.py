"""Source-locked Hindi narration; the visual planner cannot invent spoken facts."""
import re
ROLES=('hook','challenge','reveal','explain','transfer','revision')
HEADINGS=('सवाल देखिए','अपना जवाब चुनिए','सही उत्तर','तथ्य समझिए','खुद को जाँचिए','रिवीजन कार्ड')
def grounded_storyboard(reference,format_name=None):
    question=re.sub(r'^[a-z0-9_-]+:\s*','',str(reference.get('question','')).strip())
    options=reference.get('options') or {};key=reference.get('answer')
    if not question or key not in options:raise ValueError('Grounded question and answer required')
    answer=str(options[key]).strip().rstrip('।.')
    facts=[s.strip()+'।' for s in re.split(r'[।!?]|(?<!\d)\.(?!\d)',str(reference.get('explanation',''))) if 3<=len(s.split())<=25]
    if not facts:raise ValueError('A complete concise source explanation is required')
    other=next((str(v).strip().rstrip('।.') for k,v in options.items() if k!=key),None)
    choices='दोनों विकल्पों में सही कौन-सा है? दो सेकंड सोचिए।' if other else 'दो सेकंड सोचिए, फिर जवाब मिलाइए।'
    displayed=[answer,other] if other else [answer]
    if other and sum(question.encode())%2:displayed.reverse()
    # Lead with the question itself, then vary the short challenge by experiment.
    # Format diversity matters for controlled A/B testing without generic preambles.
    prompt_tail={'exam_trap':' गलत विकल्प पहचानिए।',
                 'visual_mystery':' दृश्य देखकर जवाब खोजिए।',
                 'map_pyq_challenge':' नक्शे पर दिशा पहचानिए।'}.get(format_name,'')
    opening=question+prompt_tail if len((question+prompt_tail).split())<=25 else question
    speech=[opening,choices,'सही उत्तर है: '+answer+'।',facts[0],facts[1] if len(facts)>1 else 'अब बिना देखे जवाब दीजिए: '+question,'याद रखें: '+answer+'।']
    if any(len(line.split())>25 for line in speech):raise ValueError('Question/options exceed readable scene limits')
    result=[{'role':role,'heading':heading,'speech':line,'explanation':(' '.join(line.split()[:6]))} for role,heading,line in zip(ROLES,HEADINGS,speech)]
    result[0]['heading']={'exam_trap':'परीक्षा का जाल','visual_mystery':'दृश्य से जवाब','map_pyq_challenge':'नक्शा टेस्ट'}.get(format_name,result[0]['heading'])
    result[1]['quiz_options']=displayed
    return result
