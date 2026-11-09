"""Reject unsupported scene promises before voice/render/publishing."""
import math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from gs_scene_policy import is_revision_card
VERSION='rich_3d_v1'
SETTINGS={'neutral','coast','space','institution','laboratory','village'}
ROLES={'ordinary','marcher','soldier','gandhi'}
GENERIC_KINDS={'arrow','gear','sphere','box','cylinder','book'}
GENERIC_PEOPLE={'विद्यार्थी','छात्र','छात्रा','व्यक्ति','student','Student'}
GENERIC_LABELS={'तीर','इशारा','कार्ड','मार्ग','स्मरण','स्मरण पुस्तक','नदी विकल्प','विकल्प','वस्तु','चीज़'}
BOUNDS={'world':(-180,-85,180,85),'india':(67,6,98,37),'gujarat':(68,20,75,25)}
def coordinate(p,b):
 return isinstance(p,list) and len(p)==2 and all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in p) and b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]
def validate_visual(plan):
 if plan.get('needs_custom_assets'):raise ValueError('Custom model needed: '+str(plan.get('asset_requirement','Unsupported subject-specific animation'))[:300])
 for i,s in enumerate(plan['scenes']):
  if s.get('setting') not in SETTINGS:raise ValueError(f'Scene {i+1}: explicit supported setting required')
  if not isinstance(s.get('visual_action'),str) or len(s['visual_action'].split())<4:raise ValueError(f'Scene {i+1}: explain the visible action, not just screen text')
  
  if s.get('camera_view','oblique') not in ('front','top','oblique'):raise ValueError('Unsupported camera view')
  objects=s['objects'];ids={o['id']:o for o in objects};meaningful=0
  if len(objects)>9:raise ValueError(f'Scene {i+1}: excessive on-screen objects; simplify the visual')
  if len(ids)!=len(objects):raise ValueError(f'Scene {i+1}: duplicate object IDs')
  for o in objects:
   kind=o['kind'];action=o['action']
   window=o.get('animation_window',[0,1])
   if not isinstance(window,list) or len(window)!=2 or any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) for x in window) or not 0<=window[0]<window[1]<=1 or window[1]-window[0]<.45:raise ValueError('Animation window must leave at least 45 percent for readable movement')
   if action=='compress' and kind!='rock_layers':raise ValueError('Compression is implemented only for continuous rock layers')
   if kind=='rock_layers' and action!='compress':raise ValueError('Rock layers must show compression')
   if kind=='box' and any(word in (o.get('id','')+' '+o.get('label','')).lower() for word in ('india','asia','himalaya','भारत','एशिया','हिमालय','organ','हृदय')):raise ValueError('Named real objects need a matching model, not a generic box')
   if kind in ('person','soldier'):
    if o.get('role','ordinary') not in ROLES:raise ValueError('Unimplemented character likeness; custom asset required')
    if o.get('gesture','') not in ('','point','collect','hold'):raise ValueError('Unsupported gesture')
    if o.get('gesture') in ('collect','hold'):
     target=ids.get(o.get('interact_with'))
     if not target or target['kind']!='salt':raise ValueError('This grasp rig currently supports salt only; do not pretend to grasp another asset')
   if kind=='map':
    region=o.get('map_region');bounds=BOUNDS.get(region)
    if not bounds:raise ValueError('Map requires a bundled sourced region')
    route=o.get('route',[])
    if action=='trace' and not 2<=len(route)<=8:raise ValueError('Map trace needs 2-8 sourced geographical points')
    if route and (action!='trace' or not all(coordinate(p,bounds) for p in route)):raise ValueError('Map coordinates outside sourced region')
    markers=o.get('markers',[])
    if len(markers)>3 or any(not coordinate(m.get('at'),bounds) or not isinstance(m.get('label'),str) or not 1<=len(m['label'])<=24 for m in markers):raise ValueError('Invalid map markers')
   if o.get('route') and kind!='map':raise ValueError('Geographic routes require an actual map asset')
   if action=='trace' and kind!='map':raise ValueError('Trace is only implemented for geographic maps')
   if kind=='map' and (o.get('highlight_states') or o.get('rivers') or o.get('latitude_lines')):
    if o.get('map_region')!='india':raise ValueError('State/river/latitude overlays exist only on the India map')
    ok_states={'Gujarat','Rajasthan','Madhya Pradesh','Maharashtra','Uttar Pradesh','Bihar','West Bengal','Orissa','Karnataka','Tamil Nadu','Kerala','Goa','Chhattisgarh','Jharkhand','Assam','Punjab','Haryana','Himachal Pradesh','Uttaranchal','Sikkim','Meghalaya','Tripura','Mizoram','Manipur','Nagaland','Arunachal Pradesh'}
    ok_rivers={'Ganga','Yamuna','Brahmaputra','Godavari','Krishna','Narmada','Tapi','Mahanadi','Kaveri','Chambal','Son','Betwa','Mahi','Tungabhadra','Ghaghara','Gandak','Teesta','Penner'}
    if not set(o.get('highlight_states',[]))<=ok_states:raise ValueError('Unsupported or unsourced state highlight')
    if not set(o.get('rivers',[]))<=ok_rivers:raise ValueError('River not in the sourced river dataset')
    if any(not 6<float(x.get('lat',0))<31.5 for x in o.get('latitude_lines',[])):raise ValueError('Latitude line outside mapped India region')
   VAR={'lens':('convex','concave'),'mirror':('convex','concave'),'wave':('high',),'beaker':('acid','base'),'molecule':('h2o','co2','o2','ch4','nh3','nacl'),'cell':('plant','animal')}
   if kind in ('lens','mirror','prism','circuit','pendulum','spring','lever','wave','beaker','test_tube','molecule','cell','solar_system','earth_layers','volcano','water_cycle','timeline','bar_chart','flag') and o.get('variant') is not None and o.get('variant') not in VAR.get(kind,()):raise ValueError('Unknown diagram variant')
   if kind=='timeline':
    ev=o.get('events');
    if not isinstance(ev,list) or not 2<=len(ev)<=5 or any(not isinstance(e,dict) or not str(e.get('year','')).strip() or not 1<=len(str(e.get('label','')))<=24 for e in ev):raise ValueError('Timeline needs 2-5 sourced events with year and short label')
   if kind=='bar_chart':
    bars=o.get('bars')
    if not isinstance(bars,list) or not 2<=len(bars)<=5 or any(not isinstance(b,dict) or not isinstance(b.get('value'),(int,float)) or b['value']<0 or not 1<=len(str(b.get('label','')))<=14 for b in bars):raise ValueError('Bar chart needs 2-5 sourced numeric values')
   if action=='wave' and kind!='ocean':raise ValueError('Wave is only implemented for ocean meshes')
   if kind=='ocean' and action!='wave':raise ValueError('Ocean must deform, not be a still background')
   # Decorative pulsing/growing alone cannot meet the teaching-motion requirement.
   if action in ('walk','move','flow','rise','fall','spin','orbit','trace','wave','compress') or o.get('gesture') in ('point','collect','hold') or kind in ('lens','mirror','prism','circuit','pendulum','spring','lever','wave','beaker','test_tube','molecule','cell','solar_system','earth_layers','volcano','water_cycle','timeline','bar_chart','flag') or (kind=='map' and (o.get('highlight_states') or o.get('rivers') or o.get('latitude_lines'))):meaningful+=1
  if meaningful<1 and not is_revision_card(s,i,len(plan['scenes'])) and not s.get('hook_question'):raise ValueError(f'Scene {i+1}: no causal movement beyond decorative pulse/zoom')
  if s.get('role')=='hook' and not (s.get('hook_question') or s.get('quiz_card') or s.get('heading')):raise ValueError('Hook must show an immediate readable question or challenge')
  # 4 Nov insights: flop reels used a walking 'विद्यार्थी', spinning arrows labelled '11'/'12',
  # a gear for 'संशोधन' and a map for a Polity question. Top reels always showed the real thing.
  if not is_revision_card(s,i,len(plan['scenes'])) and not s.get('hook_question'):
   has_map=any(o['kind']=='map' for o in objects)
   def generic(o):
    label=str(o.get('label','')).strip()
    if o['kind'] in ('person','soldier'):return label in GENERIC_PEOPLE
    # A labelled sphere/arrow can stand for a real thing (वायु अणु, नीला प्रकाश); an empty,
    # numeric or placeholder label cannot.
    return o['kind'] in GENERIC_KINDS and (not label or label.replace('.','').isdigit() or label in GENERIC_LABELS or label.rstrip('0123456789')=='विकल्प')
   real=[o for o in objects if not generic(o)]
   if not has_map and not real and s.get('role')!='challenge':raise ValueError(f'Scene {i+1}: only generic props (arrow/gear/sphere/box/student); show a topic-specific object or skip this topic')
   for o in objects:
    if s.get('role')!='challenge' and str(o.get('label','')).strip() in GENERIC_LABELS:raise ValueError(f'Scene {i+1}: meaningless label "{o.get("label")}"; label must name the real thing or be empty')
 # Never silently accept a repeated, motionless middle sequence.
 for a,b in zip(plan['scenes'],plan['scenes'][1:]):
  if a.get('role') not in ('hook','challenge') and b.get('role') not in ('revision',):
   sig=lambda sc:tuple(sorted((str(o.get('kind')),str(o.get('action')),str(o.get('label')),str(o.get('variant')),str(o.get('rivers')),str(o.get('highlight_states')),str(o.get('latitude_lines'))) for o in sc.get('objects',[])))
   if sig(a)==sig(b) and a.get('visual_action')==b.get('visual_action'):
    raise ValueError('Adjacent scenes repeat the same objects and action without new visual information')
 subject=str(plan.get('subject',''))
 if any(o['kind']=='map' for sc in plan['scenes'] for o in sc['objects']) and subject and not any(w in subject for w in ('Geography','भूगोल','History','इतिहास','Traditional GK','Static','स्टैटिक','QA')):
  raise ValueError('Map shown for a non-geography/history topic')
 return plan

