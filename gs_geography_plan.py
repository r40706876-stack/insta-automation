"""Reusable source-driven geography scenes for a supplied river-flow dataset."""
import copy
import hashlib

def grounded_map_plan(reference,storyboard):
    geometry=reference.get('map_geometry') or {}
    if geometry.get('purpose')!='river_flow_direction':return None
    route=geometry.get('route') or []
    if geometry.get('region') not in ('india','world','gujarat') or not 2<=len(route)<=8 or not geometry.get('sources'):
        raise ValueError('Sourced geographic route required')
    origin=geometry.get('origin_label');mouth=geometry.get('destination_label')
    if not origin or not mouth:raise ValueError('Grounded source and destination labels required')
    first={'at':route[0],'label':origin};last={'at':route[-1],'label':mouth}
    lat0=route[0][1]
    # Map Test 01: from the source, two equal dashed paths to BOTH seas (does not reveal the answer).
    choices=[[route[0],[70.0,19.5]],[route[0],[87.8,19.0]]] if geometry['region']=='india' else []
    def map_asset(trace=False,markers=(),choice=False):
        value={'id':'geographic_map','kind':'map','action':'trace' if trace else 'none','map_region':geometry['region'],'label':'','pos':[0,0,0],'size':[1.45]*3,'color':'#268f89','markers':list(markers)}
        if trace:value['route']=copy.deepcopy(route)
        if geometry['region']=='india':
            # Same regional crop in every scene: always include the source and the mouth.
            value['choice_lines']=copy.deepcopy(choices) if choice else []
            value['frame_points']=[route[0],route[-1]]+[c[1] for c in choices]
        return value
    scenes=copy.deepcopy(storyboard)
    # Same spatial context throughout. The first two scenes show equal alternatives,
    # and never draw only the correct river route before the reveal.
    for index in (0,1):
        scenes[index].update(setting='neutral',camera_view='front',visual_action='Two equally weighted east and west choices move over the sourced regional map; neither is marked correct',teaches='Identify the two possible directions without revealing the answer',objects=[map_asset(False,[first],True),
          {'id':'east_choice','kind':'arrow','action':'move','label':'पूर्व','pos':[-.3,-.35,.9],'to':[.9,-.35,.9],'size':[.5]*3,'color':'#56bbdf'},
          {'id':'west_choice','kind':'arrow','action':'move','label':'पश्चिम','pos':[.3,-.35,.9],'to':[-.9,-.35,.9],'size':[.5]*3,'color':'#56bbdf'}])
    scenes[2].update(setting='neutral',camera_view='front',visual_action='The sourced river polyline traces from its origin toward its actual destination',teaches='Read the correct flow direction on real geographic context',objects=[map_asset(True,[first,last])])
    scenes[3].update(setting='neutral',camera_view='front',visual_action='A labelled origin remains anchored to its geographic position while the river path begins there',teaches='Locate the named origin on the sourced route',objects=[map_asset(True,[first])])
    scenes[4].update(setting='neutral',camera_view='front',visual_action='The river route reaches the labelled destination on the regional map',teaches='Link the correct flow direction with the named destination',objects=[map_asset(True,[last])])
    scenes[5].update(setting='neutral',camera_view='front',visual_action='A short still revision map retains the two geographic location markers',teaches='Recall direction and destination in one readable revision card',revision_card=True,objects=[map_asset(False,[first,last])])
    answer=str(reference['options'][reference['answer']]).rstrip('।.')
    return {'title':reference['question'],'subject':reference.get('subject','Geography'),'topic_key':'river_flow_'+hashlib.sha256(reference['question'].encode()).hexdigest()[:12],
       'share_reason':'नदी की दिशा और मुहाने का भ्रम स्पष्ट करना','recall':scenes[-1]['speech'],
       'share_card':{'kind':'friend_quiz','recipient':'भूगोल की तैयारी वाला दोस्त','benefit':'नदी की दिशा और समुद्र का सही संबंध याद रखना','cta':'दोस्त से यही नदी वाला सवाल पूछिए'},'scenes':scenes,'source_geometry':geometry}
