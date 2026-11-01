"""One explicit final revision card may remain still for 2–6 measured seconds."""
MIN_REVISION_SECONDS=2.0
MAX_REVISION_SECONDS=6.0

def is_revision_card(scene,index,count):
    return (count==6 and index==count-1 and scene.get('role')=='revision'
            and scene.get('revision_card') is True
            and bool(scene.get('heading') or scene.get('label')) and bool(scene.get('teaches')))

def validate_revision_duration(seconds):
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not MIN_REVISION_SECONDS<=seconds<=MAX_REVISION_SECONDS:
        raise ValueError('Final revision card must last 2–6 measured seconds')
