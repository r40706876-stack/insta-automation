"""Source-locked Hindi narration; the visual planner cannot invent spoken facts."""
import re
ROLES=('hook','challenge','reveal','explain','transfer','revision')
HEADINGS=('सवाल देखिए','अपना जवाब चुनिए','सही उत्तर','तथ्य समझिए','खुद को जाँचिए','रिवीजन कार्ड')
def grounded_storyboard(reference):
    question=re.sub(r'^[a-z0-9_-]+:\s*','',str(reference.get('question','')).strip())
    options=reference.get('options') or {};key=reference.get('answer')
    if not question or key not in options:raise ValueError('Grounded question and answer required')
    answer=str(options[key]).strip().rstrip('।.')
    facts=[s.strip()+'।' for s in re.split(r'[।!?]|(?<!\d)\.(?!\d)',str(reference.get('explanation',''))) if 3<=len(s.split())<=25]
    if not facts:raise ValueError('A complete concise source explanation is required')
    other=next((str(v).strip().rstrip('।.') for k,v in options.items() if k!=key),None)
    choices=(f'एक विकल्प है {answer}। दूसरा विकल्प है {other}। पहले अपना जवाब सोचिए।' if other else 'अपना जवाब मन में तय कीजिए। अगले दृश्य में सही उत्तर से मिलाइए।')
    # Alternate source order prevents answer-position bias across repeated question banks.
    if other and sum(question.encode())%2:choices=f'एक विकल्प है {other}। दूसरा विकल्प है {answer}। पहले अपना जवाब सोचिए।'
    speech=[question,choices,'सही उत्तर है: '+answer+'।',facts[0],facts[1] if len(facts)>1 else 'अब बिना देखे जवाब दीजिए: '+question,'याद रखें: '+answer+'।']
    if any(len(line.split())>25 for line in speech):raise ValueError('Question/options exceed readable scene limits')
    return [{'role':role,'heading':heading,'speech':line,'explanation':(' '.join(line.split()[:6]))} for role,heading,line in zip(ROLES,HEADINGS,speech)]
