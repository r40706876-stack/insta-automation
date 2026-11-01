"""Constrain generated plans to complete six-scene data before semantic QA."""
def plan_schema(kinds,actions):
    string={'type':'string'}
    # Constrain structure, not every renderer parameter: a combinatorial schema
    # exceeds provider state limits. Local renderer validators enforce asset details.
    obj={'type':'object','properties':{'id':string,'kind':string,'action':string,'label':string,'map_region':string},'required':['kind','action']}
    scene={'type':'object','properties':{
        'role':{'type':'string','enum':['hook','challenge','reveal','explain','transfer','revision']},
        'heading':string,'explanation':string,'speech':string,'teaches':string,'visual_action':string,
        'setting':{'type':'string','description':'neutral, coast, space, institution, laboratory or village'},
        'revision_card':{'type':'boolean'},'objects':{'type':'array','items':obj,'minItems':2,'maxItems':4}},
        'required':['role','heading','explanation','speech','teaches','visual_action','setting','objects']}
    return {'type':'object','properties':{
        'title':string,'subject':string,'topic_key':string,'share_reason':string,'recall':string,
        'pyq_challenge':{'type':'boolean'},'share_card':{'type':'object','properties':{k:string for k in ('kind','recipient','benefit','cta')},'required':['kind','recipient','benefit','cta']},
        'scenes':{'type':'array','items':scene,'minItems':6,'maxItems':6}},
        'required':['title','subject','topic_key','share_reason','recall','share_card','scenes']}


def audit_schema():
    return {'type':'object','properties':{
        'ok':{'type':'boolean'},'reasons':{'type':'array','items':{'type':'string'}},
        'novel_topic':{'type':'boolean'},'scene_checks':{'type':'array','minItems':6,'maxItems':6,'items':{
            'type':'object','properties':{'scene':{'type':'integer'},'mechanism_matches':{'type':'boolean'}},'required':['scene','mechanism_matches']}}},
        'required':['ok','reasons','novel_topic','scene_checks']}
