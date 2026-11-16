import importlib.util
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).parents[1] / "skills" / "presentations" / "references" / "template"
SPEC = importlib.util.spec_from_file_location("check_requests", TEMPLATE / "check_requests.py")
check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check)


class CheckRequestsTest(unittest.TestCase):
    """The template's example requests hold on the template deck and break when undone."""

    def test_template_deck_meets_its_requests(self):
        source = (TEMPLATE / "deck.tex").read_text()
        self.assertTrue(all(met for met, _ in check.requests(source, ["Title", ""])))

    def test_a_dropped_questions_frame_and_a_filled_last_page_are_reported(self):
        source = (TEMPLATE / "deck.tex").read_text().replace("Questions?", "Thanks")
        broken = [request for met, request in check.requests(source, ["Title", "Backup text"]) if not met]
        self.assertEqual(len(broken), 2)


if __name__ == "__main__":
    unittest.main()
