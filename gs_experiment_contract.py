"""Six-scene experiment contract; measured timing remains an export check."""
ROLES=('hook','challenge','reveal','explain','transfer','revision')
def validate(plan,format_name):
    if not format_name:return
    from gs_learning import FORMATS
    if format_name not in FORMATS:raise ValueError('Unknown experiment format')
    scenes=plan.get('scenes',[])
    if len(scenes)!=6 or tuple(s.get('role') for s in scenes)!=ROLES:raise ValueError('Use hook/challenge/reveal/explain/transfer/revision scene roles')
    if any(not s.get('teaches') for s in scenes):raise ValueError('Every scene must state its teaching purpose')
    if not plan.get('recall'):raise ValueError('Missing revision takeaway')
    if format_name=='map_pyq_challenge' and not any(o.get('kind')=='map' for s in scenes for o in s.get('objects',[])):
        # PYQ challenge can use a topic-specific diagram instead of a fictional map.
        if not plan.get('pyq_challenge'):raise ValueError('Map or explicit PYQ challenge required')
PROMPT=''' For the selected GS_EXPERIMENT_FORMAT, use exactly six scenes with role fields hook, challenge, reveal, explain, transfer, revision in that order. Every scene narration MUST have 8-25 conversational Hindi words, including hook and challenge. Do not add any dates, quantities or numbered factual claims absent from EVIDENCE. Every moving object must have a nonzero supported path; use only implemented models. Hook poses one short Hindi question without its answer. Challenge shows two plausible options without revealing which is correct, allowing at least two seconds to think. Reveal gives the correct grounded answer; explain shows its mechanism; transfer gives a comparison; revision provides a short recall card. Only the final revision may use revision_card:true and all objects action:none, with 8-12 narration words fitting 2-6 seconds; all other scenes need causal motion. Target 20-35 seconds when the material fits; never rush speech to fit. Use quiz_card only when it does not leak the answer early. Include pyq_challenge:true for a non-map PYQ challenge. Each teaches field must describe the scene's learning purpose. Do not promise a next episode unless it is scheduled. Use one primary save objective. Exam trap contrasts a plausible misconception; visual mystery reveals a mechanism; map/PYQ challenge asks for direction/location or a sourced exam answer. '''
