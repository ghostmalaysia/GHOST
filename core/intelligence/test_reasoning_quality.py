import unittest
from core.intelligence.reasoning_engine import (
    validate_plan,
    enforce_constraints,
)


def sample_plan():
    return {
        "objective": "Build a secure local AI",
        "understanding": "Develop a local AI with owner control.",
        "facts": ["The project uses a local Qwen model."],
        "assumptions": ["The current server remains available."],
        "unknowns": ["Final server hardware."],
        "plan": [
            "Audit the existing architecture.",
            "Design the security permission layer.",
            "Test memory integration."
        ],
        "risk_level": 1,
        "risks": [],
        "approval_required": False,
        "approval_reason": "",
        "status": "planned"
    }


class ReasoningQualityTests(unittest.TestCase):

    def test_valid_plan(self):
        self.assertTrue(validate_plan(sample_plan()))

    def test_reject_empty_facts_item_type(self):
        plan = sample_plan()
        plan["facts"] = [123]
        with self.assertRaises(ValueError):
            validate_plan(plan)

    def test_reject_duplicate_steps(self):
        plan = sample_plan()
        plan["plan"] = [
            "Audit architecture.",
            "Audit architecture.",
            "Test memory."
        ]
        with self.assertRaises(ValueError):
            enforce_constraints("Create a development plan.", plan)

    def test_reject_forbidden_file_modification(self):
        plan = sample_plan()
        plan["plan"][0] = "Modify the project files."
        with self.assertRaises(ValueError):
            enforce_constraints(
                "Plan only. Do not modify files.",
                plan
            )

    def test_level_four_requires_approval(self):
        plan = sample_plan()
        plan["risk_level"] = 4
        plan["approval_required"] = False
        with self.assertRaises(ValueError):
            validate_plan(plan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
