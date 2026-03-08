import unittest

from sonar_report_reader import SonarReportReader, SonarReportEntry, BooleanField

_PROJECT1 = "PROJECT 1"
_PROJECT2 = "PROJECT 2"
_PROJECT3 = "PROJECT 3"


def _make_entry(
    module: str,
    month: str,
    year: int,
    smells: int,
    project: str = _PROJECT1,
) -> SonarReportEntry:
    return SonarReportEntry(
        project=project,
        module=module,
        report_date="",
        month=month,
        year=year,
        lines_of_code=0,
        critical_code_smells=smells,
        unit_test_coverage=0.0,
        hot_fixes_given=BooleanField.EMPTY,
        mostly_written=BooleanField.EMPTY,
        using_ai_assistant=BooleanField.EMPTY,
        cc_list=[],
        created="",
        created_by="",
    )


def _filter_by_project(result: dict, project: str) -> dict:
    filtered = {}
    for key, value in result.items():
        if isinstance(value, list):
            filtered[key] = [r for r in value if r.get("project") == project]
        else:
            filtered[key] = value
    return filtered


class TestPROJECT1CodeSmellDiff(unittest.TestCase):
    """Compare PROJECT1 code smells between January and February 2026 using in-memory data."""

    @classmethod
    def setUpClass(cls):
        reader = SonarReportReader.__new__(SonarReportReader)
        reader.entries = [
            _make_entry("BACKEND",  "January",  2026, 169),
            _make_entry("BACKEND",  "February", 2026, 185),
            _make_entry("FRONTEND", "January",  2026, 0),
            _make_entry("FRONTEND", "February", 2026, 0),
        ]
        reader._loaded = True
        full_result = reader.compare_code_smells("January", 2026, "February", 2026)
        cls.result = _filter_by_project(full_result, _PROJECT1)

    def test_project1_jan_vs_feb_code_smell_differences(self):
        increased = {r["module"]: r for r in self.result["increased"]}
        decreased = {r["module"]: r for r in self.result["decreased"]}
        unchanged = {r["module"]: r for r in self.result["unchanged"]}

        # BACKEND: 169 → 185  (+16)
        self.assertIn("BACKEND", increased)
        self.assertEqual(increased["BACKEND"]["January_2026"],  169)
        self.assertEqual(increased["BACKEND"]["February_2026"], 185)
        self.assertEqual(increased["BACKEND"]["delta"],          16)

        # FRONTEND: 0 → 0  (unchanged)
        self.assertIn("FRONTEND", unchanged)
        self.assertEqual(unchanged["FRONTEND"]["January_2026"],  0)
        self.assertEqual(unchanged["FRONTEND"]["February_2026"], 0)
        self.assertEqual(unchanged["FRONTEND"]["delta"],         0)

        # No modules decreased
        self.assertEqual(decreased, {})

        # No modules should be new or missing
        self.assertEqual(self.result["new_in_compare"],     [])
        self.assertEqual(self.result["missing_in_compare"], [])


class TestPROJECT2CodeSmellDiff(unittest.TestCase):
    """Compare PROJECT2 code smells between January and February 2026.

    Synthetic data exercises the 'decreased' and 'increased' paths together.
    MODULE_A: 245 → 198  (decreased by 47)
    MODULE_B:  80 →  80  (unchanged)
    MODULE_C: 120 → 155  (increased by 35)
    """

    @classmethod
    def setUpClass(cls):
        reader = SonarReportReader.__new__(SonarReportReader)
        reader.entries = [
            _make_entry("MODULE_A", "January",  2026, 245, _PROJECT2),
            _make_entry("MODULE_A", "February", 2026, 198, _PROJECT2),
            _make_entry("MODULE_B", "January",  2026,  80, _PROJECT2),
            _make_entry("MODULE_B", "February", 2026,  80, _PROJECT2),
            _make_entry("MODULE_C", "January",  2026, 120, _PROJECT2),
            _make_entry("MODULE_C", "February", 2026, 155, _PROJECT2),
        ]
        reader._loaded = True
        full_result = reader.compare_code_smells("January", 2026, "February", 2026)
        cls.result = _filter_by_project(full_result, _PROJECT2)

    def test_project2_module_a_decreased(self):
        decreased = {r["module"]: r for r in self.result["decreased"]}
        self.assertIn("MODULE_A", decreased)
        self.assertEqual(decreased["MODULE_A"]["January_2026"],  245)
        self.assertEqual(decreased["MODULE_A"]["February_2026"], 198)
        self.assertEqual(decreased["MODULE_A"]["delta"],         -47)

    def test_project2_module_b_unchanged(self):
        unchanged = {r["module"]: r for r in self.result["unchanged"]}
        self.assertIn("MODULE_B", unchanged)
        self.assertEqual(unchanged["MODULE_B"]["January_2026"],  80)
        self.assertEqual(unchanged["MODULE_B"]["February_2026"], 80)
        self.assertEqual(unchanged["MODULE_B"]["delta"],          0)

    def test_project2_module_c_increased(self):
        increased = {r["module"]: r for r in self.result["increased"]}
        self.assertIn("MODULE_C", increased)
        self.assertEqual(increased["MODULE_C"]["January_2026"],  120)
        self.assertEqual(increased["MODULE_C"]["February_2026"], 155)
        self.assertEqual(increased["MODULE_C"]["delta"],          35)

    def test_project2_no_new_or_missing_modules(self):
        self.assertEqual(self.result["new_in_compare"],     [])
        self.assertEqual(self.result["missing_in_compare"], [])


class TestPROJECT3CodeSmellDiff(unittest.TestCase):
    """Compare PROJECT3 code smells between January and February 2026.

    Synthetic data exercises the 'new_in_compare' and 'missing_in_compare' paths.
    MODULE_AUTH:  present only in January  → missing_in_compare  (75 smells)
    MODULE_UI:    50 → 60  (increased by 10)
    MODULE_API:   present only in February → new_in_compare      (30 smells)
    """

    @classmethod
    def setUpClass(cls):
        reader = SonarReportReader.__new__(SonarReportReader)
        reader.entries = [
            # MODULE_AUTH exists only in January
            _make_entry("MODULE_AUTH", "January",  2026, 75, _PROJECT3),
            # MODULE_UI exists in both months
            _make_entry("MODULE_UI",   "January",  2026, 50, _PROJECT3),
            _make_entry("MODULE_UI",   "February", 2026, 60, _PROJECT3),
            # MODULE_API is new in February
            _make_entry("MODULE_API",  "February", 2026, 30, _PROJECT3),
        ]
        reader._loaded = True
        full_result = reader.compare_code_smells("January", 2026, "February", 2026)
        cls.result = _filter_by_project(full_result, _PROJECT3)

    def test_project3_module_ui_increased(self):
        increased = {r["module"]: r for r in self.result["increased"]}
        self.assertIn("MODULE_UI", increased)
        self.assertEqual(increased["MODULE_UI"]["January_2026"],  50)
        self.assertEqual(increased["MODULE_UI"]["February_2026"], 60)
        self.assertEqual(increased["MODULE_UI"]["delta"],         10)

    def test_project3_module_api_is_new_in_compare(self):
        new_modules = {r["module"]: r for r in self.result["new_in_compare"]}
        self.assertIn("MODULE_API", new_modules)
        self.assertEqual(new_modules["MODULE_API"]["critical_code_smells"], 30)

    def test_project3_module_auth_is_missing_in_compare(self):
        missing_modules = {r["module"]: r for r in self.result["missing_in_compare"]}
        self.assertIn("MODULE_AUTH", missing_modules)
        self.assertEqual(missing_modules["MODULE_AUTH"]["critical_code_smells"], 75)

    def test_project3_no_decreased_or_unchanged(self):
        self.assertEqual(self.result["decreased"], [])
        self.assertEqual(self.result["unchanged"], [])


if __name__ == "__main__":
    unittest.main()
