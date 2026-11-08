import unittest
from app import friendly_failure
from analyst import summarize, abstain


class FriendlyReplyTests(unittest.TestCase):
    def test_empty_result_not_found_two_languages(self):
        result={"rows":[],"columns":["name"]}
        self.assertIn("natija topilmadi",summarize(result,"uz"))
        self.assertIn("не найдены",summarize(result,"ru"))

    def test_null_is_not_zero_or_absent_row(self):
        result={"rows":[{"avg":None}],"columns":["avg"]}
        self.assertIn("yetarli",summarize(result,"uz"))
        result={"rows":[{"n":0}],"columns":["n"]}
        self.assertEqual(summarize(result,"uz"),"n: 0")

    def test_rejected_sql_is_not_claimed_empty(self):
        self.assertIn("tekshirib bo‘lmadi",friendly_failure(422,"uz"))
        self.assertNotIn("natija topilmadi",friendly_failure(422,"uz"))
        self.assertIn("проверить",friendly_failure(422,"ru"))

    def test_unavailable_is_evidence_limit(self):
        self.assertIn("yetarli",abstain("unavailable","uz","insufficient")["answer"])
        self.assertIn("недостаточно",abstain("unavailable","ru","insufficient")["answer"].lower())

if __name__ == "__main__":
    unittest.main()
