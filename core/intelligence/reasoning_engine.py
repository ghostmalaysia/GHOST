#!/usr/bin/env python3

"""
GHOST Reasoning & Planning Engine
Initial planning module.
No system actions are executed by this module.
"""

import json
import re


SYSTEM_PROMPT = """
You are the Reasoning and Planning Engine of GHOST LOCAL AI.

Your task is to analyse the owner's request and prepare a clear plan.

OWNER AUTHORITY:
- The owner is the final authority.
- Never approve your own critical actions.
- Never execute actions.
- Level 4 critical, destructive, irreversible or high-impact
  actions require specific owner approval.
- If risk or authorization is unclear, stop and ask.

ANALYSIS RULES:
- Understand the actual objective.
- Separate facts, assumptions and unknown information.
- Identify missing information.
- Break complex tasks into practical steps.
- Identify risks and required permissions.
- Do not invent capabilities or claim completed actions.

Return ONLY valid JSON using this structure:

{
  "objective": "What the owner wants to achieve",
  "understanding": "Your interpretation of the request",
  "facts": [],
  "assumptions": [],
  "unknowns": [],
  "plan": [],
  "risk_level": 1,
  "risks": [],
  "approval_required": false,
  "approval_reason": "",
  "status": "planned"
}

Risk levels:
1 = Routine
2 = Operational
3 = Important
4 = Critical

Do not execute the plan.
"""


def create_plan(user_request):
    if not isinstance(user_request, str) or not user_request.strip():
        raise ValueError("User request cannot be empty.")

    return {
        "role": "system",
        "content": SYSTEM_PROMPT
    }, {
        "role": "user",
        "content": user_request.strip()
    }


def validate_plan(plan):
    required_fields = {
        "objective",
        "understanding",
        "facts",
        "assumptions",
        "unknowns",
        "plan",
        "risk_level",
        "risks",
        "approval_required",
        "approval_reason",
        "status"
    }

    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object.")

    if not required_fields.issubset(plan):
        raise ValueError("Plan is missing required fields.")

    if type(plan["risk_level"]) is not int:
        raise ValueError("Risk level must be an integer.")

    if plan["risk_level"] not in (1, 2, 3, 4):
        raise ValueError("Invalid risk level.")

    if type(plan["approval_required"]) is not bool:
        raise ValueError("Approval flag must be true or false.")

    if not isinstance(plan["plan"], list):
        raise ValueError("Plan steps must be a list.")

    if not isinstance(plan["risks"], list):
        raise ValueError("Risks must be a list.")

    if plan["risk_level"] == 4 and not plan["approval_required"]:
        raise ValueError("Level 4 requires owner approval.")

    return True


def parse_plan(response_text):
    try:
        plan = json.loads(response_text)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("Model did not return valid JSON.") from error

    validate_plan(plan)
    return plan


# Local Qwen API connection
API_URL = "http://127.0.0.1:8080/v1/chat/completions"


def ask_reasoning(user_request):
    import urllib.request
    import urllib.error

    system_message, user_message = create_plan(user_request)

    payload = {
        "model": "qwen",
        "messages": [system_message, user_message],
        "temperature": 0.2,
        "max_tokens": 512
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result["choices"][0]["message"]["content"].strip()

        return parse_plan(answer)

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Qwen API error {error.code}: {details}"
        ) from error

    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            "Qwen returned an unexpected response format."
        ) from error


# Reasoning Engine v2: Context and Constraint Awareness
SYSTEM_PROMPT += """

ADDITIONAL REASONING REQUIREMENTS:

1. CONTEXT UNDERSTANDING
- Identify the actual subject of the request.
- Distinguish between a file, folder, project, application and system.
- Interpret the complete request, not isolated keywords.
- Use available conversation context when provided.
- Never assume the user means only one file when referring to a project.

2. USER CONSTRAINTS
- Identify every explicit instruction, restriction and prohibition.
- Treat instructions such as "do not modify", "do not delete",
  "read-only" and "analysis only" as mandatory constraints.
- The plan must never contradict these constraints.
- For read-only requests, recommend inspection and analysis only.
- Do not suggest saving, editing, moving or deleting files
  when the user prohibits modifications.

3. FACTS AND ASSUMPTIONS
- Do not invent project files, system conditions or capabilities.
- Separate verified facts from assumptions.
- Put missing information under unknowns.
- Ask for clarification when the objective cannot be understood safely.

4. RISK ASSESSMENT
- Assess the actual consequences of proposed steps.
- Level 1: Routine.
- Level 2: Operational within authorized scope.
- Level 3: Important, only within explicitly pre-authorized scope.
- Level 4: Critical, destructive, irreversible or high-impact.
- Level 4 always requires specific owner approval.
- Never approve your own actions.
- If risk or authorization is unclear, stop and ask.

5. PLAN QUALITY
- Every step must directly support the owner's objective.
- Respect all user restrictions.
- Prefer the safest practical approach.
- Do not claim that any action has been completed.
- This engine creates plans only; it never executes actions.

Return only the required JSON structure.
"""




# Preserve original function and apply enforcement to Qwen results.
_original_ask_reasoning = ask_reasoning


def ask_reasoning(user_request):
    result = _original_ask_reasoning(user_request)
    return enforce_constraints(user_request, result)


# V3.1: Strict action and scope enforcement

def enforce_constraints(user_request, plan):
    request = user_request.lower()

    plan_only = any(x in request for x in [
        "pelan sahaja", "analisis sahaja",
        "analysis only", "plan only"
    ])

    restrictions = {
        "no_open": (
            "jangan buka" in request or
            ("jangan" in request and "buka" in request) or
            "do not open" in request
        ),
        "no_modify": (
            "jangan ubah" in request or
            ("jangan" in request and "ubah" in request) or
            "do not modify" in request or
            "analisis sahaja" in request or
            "analysis only" in request or
            "pelan sahaja" in request or
            "plan only" in request
        ),
        "no_delete": (
            "padam" in request or "delete" in request
        ) and ("jangan" in request or "do not" in request),
        "no_move": (
            "pindah" in request or "move" in request
        ) and ("jangan" in request or "do not" in request),
        "no_rename": (
            "namakan semula" in request or "rename" in request
        ) and ("jangan" in request or "do not" in request)
    }

    blocked = {
        "no_open": [
            "open", "read", "inspect", "review",
            "access", "scan", "examine", "browse"
        ],
        "no_modify": [
            "create", "edit", "modify", "write",
            "save", "update", "install", "replace",
            "copy", "document"
        ],
        "no_delete": ["delete", "remove", "erase", "unlink"],
        "no_move": ["move", "relocate", "transfer"],
        "no_rename": ["rename"]
    }

    violations = []
    steps = plan.get("plan", [])

    if not isinstance(steps, list):
        raise ValueError("Invalid plan structure.")

    for number, step in enumerate(steps, 1):
        if isinstance(step, dict):
            action = str(step.get("action", step.get("step", ""))).lower()
            description = str(step.get("description", "")).lower()
        else:
            action = str(step).lower()
            description = ""

        words = set(re.findall(r"[a-z]+", action + " " + description))

        for restriction, enabled in restrictions.items():
            if enabled and words.intersection(blocked[restriction]):
                violations.append(
                    f"Step {number}: violates {restriction}: {action}"
                )

        if plan_only and words.intersection({
            "notify", "inform", "send", "contact", "execute",
            "implement", "deploy"
        }):
            violations.append(
                f"Step {number}: exceeds plan-only scope: {action}"
            )

    if violations:
        plan["status"] = "rejected"
        plan["approval_required"] = True
        plan["approval_reason"] = "Plan violates owner restrictions."
        plan["constraint_violations"] = violations

        raise ValueError(
            "PLAN REJECTED:\n" + "\n".join(violations)
        )

    if plan.get("risk_level") == 4:
        plan["approval_required"] = True

    return plan
