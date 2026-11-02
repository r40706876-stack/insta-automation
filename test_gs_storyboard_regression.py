"""Subject explainer regression checks; 7 PYQ and mega formats are untouched."""
import unittest
from gs_storyboard import grounded_storyboard

QUESTION = {
    "subject": "Geography",
    "question": "नर्मदा नदी किस दिशा में बहती है?",
    "options": {"a": "पश्चिम", "b": "पूर्व"},
    "answer": "a",
    "explanation": "नर्मदा पश्चिम की ओर बहती है। यह अरब सागर में मिलती है।"
}

class StoryboardTests(unittest.TestCase):
    def test_question_first(self):
        for fmt in ("exam_trap", "visual_mystery", "map_pyq_challenge"):
            with self.subTest(fmt=fmt):
                scenes = grounded_storyboard(QUESTION, fmt)
                self.assertEqual(scenes[0]["speech"], QUESTION["question"])
                self.assertEqual(len(scenes), 6)
                self.assertIn("दो सेकंड", scenes[1]["speech"])
                self.assertIn("पश्चिम", scenes[2]["speech"])

    def test_bad_answer_rejected(self):
        with self.assertRaises(ValueError):
            grounded_storyboard(dict(QUESTION, answer="z"), "exam_trap")

if __name__ == "__main__":
    unittest.main()
