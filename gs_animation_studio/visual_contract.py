"""Reject unsupported scene promises before voice/render/publishing."""
import math
VERSION='rich_3d_v1'
SETTINGS={'neutral','coast','space','institution','laboratory','village'}
ROLES={'ordinary','marcher','soldier','gandhi'}
BOUNDS={'world':(-180,-85,180,85),'india':(67,6,98,37),'gujarat':(68,20,75,25)}
def coordinate(p,b):
 return isinstance(p,list) and len(p)==2 and all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in p) and b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]
def validate_visual(plan):
 if plan.get('needs_custom_assets'):raise ValueError('Custom model needed: '+str(plan.get('asset_requirement','Unsupported subject-specific animation'))[:300])
 for i,s in enumerate(plan['scenes']):
  if s.get('setting') not in SETTINGS:raise ValueError(f'Scene {i+1}: explicit supported setting required')
  if not isinstance(s.get('visual_action'),str) or len(s['visual_action'].split())<4:raise ValueError(f'Scene {i+1}: explain the visible action, not just screen text')
  objects=s['objects'];ids={o['id']:o for o in objects};meaningful=0
  for o in objects:
   kind=o['kind'];action=o['action']
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
   if action=='trace' and kind!='map':raise ValueError('Trace is only implemented for geographic maps')
   if action=='wave' and kind!='ocean':raise ValueError('Wave is only implemented for ocean meshes')
   if kind=='ocean' and action!='wave':raise ValueError('Ocean must deform, not be a still background')
   # Decorative pulsing/growing alone cannot meet the teaching-motion requirement.
   if action in ('walk','move','flow','rise','fall','spin','orbit','trace','wave') or o.get('gesture') in ('point','collect','hold'):meaningful+=1
  if meaningful<1:raise ValueError(f'Scene {i+1}: no causal movement beyond decorative pulse/zoom')
 return plan
