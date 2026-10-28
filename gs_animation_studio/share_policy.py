"""Require a concrete recipient benefit, not generic engagement begging."""
KINDS={'common_misconception','exam_confusion','friend_quiz','everyday_use'}
CONTRACT="""SHARE VALUE: Keep the topic simple, but give a real reason to send it to a specific person. Return share_card:{kind:common_misconception|exam_confusion|friend_quiz|everyday_use,recipient:who benefits (3-12 Hindi words),benefit:the exact confusion/useful shortcut explained by THIS reel (5-22 Hindi words),cta:a natural Hindi invitation of 4-12 words, <=80 characters}. Also keep share_reason consistent with this card. The concrete benefit must be demonstrated before the invitation; merely saying share karo is insufficient. Useful patterns: resolve a common exam confusion for a study partner; show a counterintuitive everyday mechanism a friend misunderstands; give a tiny honest question to try together, with its answer explained in the reel. No invented 99% claims, shame, guaranteed marks/results, fake urgency, forced tagging or demands to share. Do not make an easy topic obscure just for surprise. Final scene still states the one-line recall; a small on-screen CTA is shown only in its final two seconds. The cta must mention the particular concept or confusion, rather than just friends/share/like/follow. """
def validate_share(plan):
 card=plan.get('share_card')
 if not isinstance(card,dict) or card.get('kind') not in KINDS:raise ValueError('Concrete share_card required')
 for key,lo,hi in [('recipient',3,12),('benefit',5,22),('cta',4,12)]:
  value=card.get(key)
  if not isinstance(value,str) or not lo<=len(value.split())<=hi:raise ValueError('Share '+key+' must be short and specific')
 if len(card['cta'])>80:raise ValueError('Share CTA too long for safe overlay')
 generic={'दोस्तों को शेयर करो','इस वीडियो को शेयर करो','दोस्तों को जरूर भेजो','लाइक शेयर और फॉलो करो'}
 if card['cta'].strip(' ।!') in generic:raise ValueError('Generic share request does not establish viewer value')
 return plan
