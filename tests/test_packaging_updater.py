import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PackagingUpdaterTests(unittest.TestCase):
    def test_both_platforms_start_through_update_launcher(self):
        for spec_name in (
            "DHI_Screening_System_Windows.spec",
            "DHI_Screening_System_macOS.spec",
        ):
            spec = (PROJECT_ROOT / spec_name).read_text(encoding="utf-8")
            self.assertIn("['fast_start.py']", spec, spec_name)
            self.assertIn("'update_manager'", spec, spec_name)
            self.assertIn("'update_workers'", spec, spec_name)

    def test_release_requires_update(self):
        notes = json.loads(
            (PROJECT_ROOT / "release_notes.json").read_text(encoding="utf-8")
        )
        self.assertIs(notes["force_update"], True)

    def test_update_check_failure_cannot_fall_through_to_application(self):
        launcher = (PROJECT_ROOT / "fast_start.py").read_text(encoding="utf-8")
        self.assertIn(
            "update_check_worker.failed.connect(handle_update_check_failed)",
            launcher,
        )
        self.assertNotIn(
            "update_check_worker.failed.connect(lambda _message: "
            "start_application_after_update_check())",
            launcher,
        )


if __name__ == "__main__":
    unittest.main()
