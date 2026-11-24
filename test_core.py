import unittest

import matching
import profile_parser as pp
import store


class ParserTests(unittest.TestCase):
    def test_english_note(self):
        p = pp.parse_voice_text("I am an electrician with 8 years experience in Hebbal, free tomorrow, 900 rupees")
        self.assertEqual(p["trade"], "electrician")
        self.assertEqual(p["years"], 8)
        self.assertEqual(p["area"], "hebbal")
        self.assertEqual(p["availability"], "tomorrow")
        self.assertEqual(p["wage_expected"], 900)

    def test_number_words_and_two_word_area(self):
        p = pp.parse_voice_text("plumber, eight years, BTM Layout")
        self.assertEqual((p["trade"], p["years"], p["area"]), ("plumber", 8, "btm layout"))

    def test_hindi_words(self):
        p = pp.parse_voice_text("मैं बिजली का काम करता हूँ, 5 साल, hebbal, कल खाली हूँ")
        self.assertEqual((p["trade"], p["years"], p["availability"]), ("electrician", 5, "tomorrow"))

    def test_missing_fields(self):
        self.assertEqual(pp.missing_fields(pp.parse_voice_text("hello")), ["trade", "area"])

    def test_kal_inside_word_is_not_tomorrow(self):
        self.assertEqual(pp.parse_voice_text("local electrician in hebbal")["availability"], "anytime")


class MatchingTests(unittest.TestCase):
    def setUp(self):
        store.reset()

    def test_only_same_trade_and_open(self):
        w = {"trade": "electrician", "area": "hebbal", "availability": "anytime"}
        ranked = matching.rank_jobs(w, list(store.jobs.values()))
        self.assertTrue(ranked)
        self.assertTrue(all(r["job"]["trade"] == "electrician" for r in ranked))

    def test_nearer_job_ranks_higher(self):
        w = {"trade": "electrician", "area": "hebbal", "availability": "anytime"}
        ranked = matching.rank_jobs(w, list(store.jobs.values()))
        self.assertEqual(ranked[0]["job"]["area"], "hebbal")
        self.assertGreaterEqual(ranked[0]["score"], ranked[-1]["score"])

    def test_typical_wage_is_median(self):
        self.assertEqual(matching.typical_wage("electrician", list(store.jobs.values())), 900)

    def test_reply_mentions_jobs_and_tip(self):
        w = {"trade": "plumber", "area": "indiranagar", "years": 3}
        m = matching.rank_jobs(dict(w, availability="today"), list(store.jobs.values()))
        text = matching.build_reply(w, m, 790, "Test tip")
        self.assertIn("3 years", text)
        self.assertIn("Tip: Test tip", text)
        self.assertIn("a plumber", text)
        e = matching.build_reply({"trade": "electrician", "area": "hebbal"}, [], None, None)
        self.assertIn("an electrician", e)


class RatingTests(unittest.TestCase):
    def setUp(self):
        store.reset()
        self.w = store.add_worker({"trade": "electrician", "area": "hebbal", "years": 8})

    def test_cannot_rate_before_completion(self):
        ok, _ = store.add_rating(self.w["id"], 1, 5)
        self.assertFalse(ok)

    def test_complete_then_rate_once(self):
        self.assertTrue(store.complete_job(1, self.w["id"])[0])
        self.assertTrue(store.add_rating(self.w["id"], 1, 5)[0])
        self.assertFalse(store.add_rating(self.w["id"], 1, 4)[0])
        card = store.skill_card(self.w["id"])
        self.assertEqual((card["jobs_completed"], card["ratings"], card["average_rating"]), (1, 1, 5.0))

    def test_wrong_trade_cannot_complete(self):
        self.assertFalse(store.complete_job(4, self.w["id"])[0])   # job 4 is a plumber job

    def test_verified_after_three_good_ratings(self):
        for jid in (1, 2, 3):
            store.complete_job(jid, self.w["id"])
            store.add_rating(self.w["id"], jid, 5)
        self.assertTrue(store.skill_card(self.w["id"])["verified_by_employers"])


if __name__ == "__main__":
    unittest.main()
