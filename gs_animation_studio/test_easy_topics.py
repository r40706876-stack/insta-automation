import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from gs_animation_bridge import choose_reference,topic_priority
from planner import EASY_MEMORY_CONTRACT

def q(text,subject='Economics'):
 return {'question':text,'subject':subject,'options':{'a':'उत्तर'},'answer':'a','explanation':'एक प्रमाणित स्रोत की सरल व्याख्या इस प्रश्न का सही उत्तर बताती है।'}
class EasyTopicTests(unittest.TestCase):
 def test_everyday_question_preferred_before_obscure_date(self):
  hard=q('1905 में किस सम्मेलन की अध्यक्षता किसने की थी?')
  easy=q('कीमत वही लेकिन सामान कम क्यों मिल रहा है?')
  self.assertEqual(choose_reference([hard,easy],'Economics',set())[1],easy)
 def test_year_density_is_penalized(self):
  self.assertLess(topic_priority(q('1905 1911 1920 में हुए सम्मेलन?')),topic_priority(q('कौन सा सम्मेलन हुआ?')))
 def test_easy_topic_must_still_match_subject(self):
  a=q('बारिश क्यों होती है?','Geography');b=q('बहुमत कैसे बनता है?','Polity')
  self.assertEqual(choose_reference([a,b],'Polity',set())[1],b)
 def test_used_easy_topic_is_not_repeated(self):
  a=q('कीमत क्यों बढ़ती है?');b=q('बचत कैसे काम करती है?')
  used={hashlib.sha256(a['question'].encode()).hexdigest()}
  self.assertEqual(choose_reference([a,b],'Economics',used)[1],b)
 def test_topic_policy_keeps_manual_topic_and_one_takeaway(self):
  self.assertIn('ONE small idea',EASY_MEMORY_CONTRACT)
  self.assertIn('Never replace an explicitly requested user topic',EASY_MEMORY_CONTRACT)
  self.assertIn('at most 16 words',EASY_MEMORY_CONTRACT)
if __name__=='__main__':unittest.main()
