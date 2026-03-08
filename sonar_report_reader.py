from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class BooleanField(Enum):
    EMPTY = "EMPTY"
    YES = "YES"
    NO = "NO"


@dataclass
class SonarReportEntry:
    project: str
    module: str
    report_date: str
    month: str
    year: int
    lines_of_code: int
    critical_code_smells: int
    unit_test_coverage: float
    hot_fixes_given: BooleanField
    mostly_written: BooleanField
    using_ai_assistant: BooleanField
    cc_list: List[str] = field(default_factory=list)
    created: str = ""
    created_by: str = ""


class SonarReportReader:
    def __init__(self) -> None:
        self.entries: List[SonarReportEntry] = []
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare_code_smells(
        self,
        base_month: str,
        base_year: int,
        compare_month: str,
        compare_year: int,
    ) -> dict:
        """Compare critical code smells between two months across all projects/modules.

        Returns a dict with keys:
            increased, decreased, unchanged, new_in_compare, missing_in_compare
        Each value is a list of result dicts.
        """
        base_key = f"{base_month}_{base_year}"
        compare_key = f"{compare_month}_{compare_year}"

        # Build lookup: (project, module) -> smells for each period
        base_map: dict[tuple[str, str], int] = {}
        compare_map: dict[tuple[str, str], int] = {}

        for entry in self.entries:
            key = (entry.project, entry.module)
            if entry.month == base_month and entry.year == base_year:
                base_map[key] = entry.critical_code_smells
            elif entry.month == compare_month and entry.year == compare_year:
                compare_map[key] = entry.critical_code_smells

        increased: list[dict] = []
        decreased: list[dict] = []
        unchanged: list[dict] = []
        new_in_compare: list[dict] = []
        missing_in_compare: list[dict] = []

        # Modules present in both periods
        all_keys = set(base_map.keys()) | set(compare_map.keys())

        for proj_mod in sorted(all_keys):
            project, module = proj_mod
            in_base = proj_mod in base_map
            in_compare = proj_mod in compare_map

            if in_base and in_compare:
                base_val = base_map[proj_mod]
                comp_val = compare_map[proj_mod]
                delta = comp_val - base_val

                row = {
                    "project": project,
                    "module": module,
                    base_key: base_val,
                    compare_key: comp_val,
                    "delta": delta,
                }

                if delta > 0:
                    increased.append(row)
                elif delta < 0:
                    decreased.append(row)
                else:
                    unchanged.append(row)

            elif in_compare and not in_base:
                new_in_compare.append({
                    "project": project,
                    "module": module,
                    "critical_code_smells": compare_map[proj_mod],
                })

            elif in_base and not in_compare:
                missing_in_compare.append({
                    "project": project,
                    "module": module,
                    "critical_code_smells": base_map[proj_mod],
                })

        return {
            "increased": increased,
            "decreased": decreased,
            "unchanged": unchanged,
            "new_in_compare": new_in_compare,
            "missing_in_compare": missing_in_compare,
        }