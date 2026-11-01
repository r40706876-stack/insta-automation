"""Constrain generated plans to complete six-scene data before semantic QA."""
def plan_schema(kinds,actions):
    string={'type':'string'}
    vector={'type':'array','items':{'type':'number'},'minItems':3,'maxItems':3}
    obj={'type':'object','properties':{
        'id':string,'kind':{'type':'string','enum':sorted(kinds)},'action':{'type':'string','enum':sorted(actions)},
        'label':string,'color':string,'pos':vector,'to':vector,'size':vector,
        'map_region':{'type':'string','enum':['india','world','gujarat']},
        'route':{'type':'array','items':{'type':'array','items':{'type':'number'},'minItems':2,'maxItems':2},'minItems':2,'maxItems':8},
        'markers':{'type':'array','items':{'type':'object','properties':{'at':{'type':'array','items':{'type':'number'},'minItems':2,'maxItems':2},'label':string},'required':['at','label']},'maxItems':3}},'required':['id','kind','action']}
    scene={'type':'object','properties':{
        'role':{'type':'string','enum':['hook','challenge','reveal','explain','transfer','revision']},
        'heading':string,'explanation':string,'speech':string,'teaches':string,'visual_action':string,
        'setting':{'type':'string','enum':['neutral','coast','space','institution','laboratory','village']},
        'revision_card':{'type':'boolean'},'objects':{'type':'array','items':obj,'minItems':2,'maxItems':4}},
        'required':['role','heading','explanation','speech','teaches','visual_action','setting','objects']}
    return {'type':'object','properties':{
        'title':string,'subject':string,'topic_key':string,'share_reason':string,'recall':string,
        'pyq_challenge':{'type':'boolean'},'share_card':{'type':'object','properties':{k:string for k in ('kind','recipient','benefit','cta')},'required':['kind','recipient','benefit','cta']},
        'scenes':{'type':'array','items':scene,'minItems':6,'maxItems':6}},
        'required':['title','subject','topic_key','share_reason','recall','share_card','scenes']}
