#!/usr/bin/env python3

"""
GHOST Reasoning & Planning Engine
Initial planning module.
No system actions are executed by this module.
"""

import json
import re


SYSTEM_PROMPT = """
You are GHOST Reasoning and Planning Engine.

Your role is to understand the owner's objective and create a safe,
accurate and practical plan. You NEVER execute actions.

OWNER AUTHORITY:
- The owner is the only final authority.
- Never approve your own actions.
- Never override or weaken an owner's restriction.
- Level 4 actions require specific owner approval.
- If risk, scope or permission is unclear, stop and ask.

MANDATORY RESTRICTION ANALYSIS:
1. Read the complete owner's request before planning.
2. Identify every prohibited action explicitly.
3. Convert each prohibition into a HARD CONSTRAINT.
4. Apply all hard constraints to every proposed plan step.
5. A forbidden action must never appear as a recommended step,
   even if it would make the task easier.
6. Do not interpret a request for analysis as permission to
   open, read, inspect or modify files.
7. If the objective cannot be achieved within the restrictions,
   explain the limitation and ask the owner.

EXAMPLES:
- "Do not open files" means no opening files.
- "Do not read files" means no reading file contents.
- "Analysis only" means analysis without changing anything.
- "Do not modify or delete" prohibits both operations.
- Never suggest a prohibited action as an intermediate step.

PLANNING:
- Understand the actual subject and objective.
- Distinguish files, folders, projects, applications and systems.
- Separate verified facts, assumptions and unknowns.
- Never invent files, system conditions or completed work.
- Provide at least 3 relevant steps when a safe plan is possible.
- If no safe plan is possible, explain why instead of inventing steps.
- Keep each step specific and concise.

RISK:
1 = Routine.
2 = Operational within authorized scope.
3 = Important within explicitly pre-authorized scope.
4 = Critical, destructive, irreversible or high-impact.
- Level 4 always requires specific owner approval.
- Never downgrade risk to avoid approval.
- If uncertain, use the safer classification.

OUTPUT:
Return ONLY valid JSON with these fields:
{
  "objective": "Owner's goal",
  "understanding": "Meaning of the request",
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

Do not execute anything.
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

    for field in ("objective", "understanding", "status"):
        if not isinstance(plan[field], str) or not plan[field].strip():
            raise ValueError(f"{field} must be non-empty text.")

    for field in ("facts", "assumptions", "unknowns", "risks"):
        if not isinstance(plan[field], list):
            raise ValueError(f"{field} must be a list.")

        if not all(isinstance(item, str) for item in plan[field]):
            raise ValueError(f"Every item in {field} must be text.")

    if type(plan["risk_level"]) is not int:
        raise ValueError("Risk level must be an integer.")

    if plan["risk_level"] not in (1, 2, 3, 4):
        raise ValueError("Invalid risk level.")

    if type(plan["approval_required"]) is not bool:
        raise ValueError("Approval flag must be true or false.")

    if not isinstance(plan["approval_reason"], str):
        raise ValueError("Approval reason must be text.")

    if not isinstance(plan["plan"], list) or not plan["plan"]:
        raise ValueError("Plan must contain at least one actionable step.")

    for number, step in enumerate(plan["plan"], 1):
        if isinstance(step, str):
            if not step.strip():
                raise ValueError(f"Step {number} cannot be empty.")

        elif isinstance(step, dict):
            if not any(
                isinstance(value, str) and value.strip()
                for value in step.values()
            ):
                raise ValueError(f"Step {number} must contain useful text.")

        else:
            raise ValueError(
                f"Step {number} must be text or a JSON object."
            )

    # Reject duplicate or repeated plan steps.
    seen_steps = set()

    for number, step in enumerate(plan["plan"], 1):
        if isinstance(step, str):
            step_text = step
        else:
            step_text = " ".join(
                value for value in step.values()
                if isinstance(value, str)
            )

        normalized = " ".join(step_text.casefold().split())
        normalized = normalized.rstrip(" .!?;:")

        if normalized in seen_steps:
            raise ValueError(
                f"Duplicate plan step detected at step {number}."
            )

        seen_steps.add(normalized)

    if plan["status"] not in ("planned", "needs_review", "blocked"):
        raise ValueError("Invalid plan status.")

    if plan["risk_level"] == 4 and not plan["approval_required"]:
        raise ValueError("Level 4 requires specific owner approval.")

    if plan["approval_required"] and not plan["approval_reason"].strip():
        raise ValueError("Approval reason is required.")

    return True



def parse_plan(response_text):
    if not isinstance(response_text, str):
        raise ValueError("Model response must be text.")

    # Remove trailing commas outside JSON strings.
    cleaned = []
    in_string = False
    escaped = False
    i = 0

    while i < len(response_text):
        char = response_text[i]

        if in_string:
            cleaned.append(char)
            if escaped:
                escaped = False
            elif char == "\\\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
                cleaned.append(char)
            elif char == ',':
                j = i + 1
                while j < len(response_text) and response_text[j].isspace():
                    j += 1
                if j < len(response_text) and response_text[j] in '}]':
                    i += 1
                    continue
                cleaned.append(char)
            else:
                cleaned.append(char)

        i += 1

    try:
        return json.loads("".join(cleaned))
    except json.JSONDecodeError as error:
        raise ValueError("Model did not return valid JSON.") from error


# Local Qwen API connection
API_URL = "http://127.0.0.1:8080/v1/chat/completions"


# Automatic Plan Correction: maximum 3 attempts.



def ask_reasoning(user_request):
    if not isinstance(user_request, str) or not user_request.strip():
        raise ValueError("User request cannot be empty.")

    original_request = user_request.strip()
    feedback = None
    last_error = None

    for attempt in range(1, 4):
        system_message, user_message = create_plan(original_request)

        if feedback:
            system_message["content"] += (
                "\n\nVALIDATION CORRECTION:\n"
                "The previous plan was rejected.\n"
                "Correct the plan while preserving every owner restriction.\n"
                "Return complete valid JSON only.\n"
                "Ensure the plan contains at least 3 actionable steps.\n"
                "Do not include prohibited actions.\n"
                "Validator feedback: " + feedback
            )

        try:
            import urllib.request
            import urllib.error

            payload = {
                "model": "qwen",
                "messages": [system_message, user_message],
                "temperature": 0.1,
                "max_tokens": 900
            }

            request = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))

            answer = result["choices"][0]["message"]["content"].strip()
            plan = parse_plan(answer)
            validate_plan(plan)
            return enforce_constraints(original_request, plan)

        except (ValueError, RuntimeError, KeyError, IndexError, TypeError) as error:
            last_error = error
            feedback = str(error)

    raise RuntimeError(
        "GHOST could not produce a valid safe plan after "
        "3 attempts. Owner review required. Last error: "
        + str(last_error)
    ) from last_error


# V4: Action + Target Constraint Validator

def enforce_constraints(user_request, plan):
    import re

    if not isinstance(user_request, str) or not isinstance(plan, dict):
        raise ValueError("Invalid request or plan structure.")

    steps = plan.get("plan")
    if not isinstance(steps, list):
        raise ValueError("Plan steps must be a list.")

    request = user_request.lower()

    restrictions = {
        "no_open": any(term in request for term in (
            "jangan buka", "jangan baca", "jangan akses",
            "jangan periksa", "do not open", "do not read",
            "do not access", "do not inspect"
        )),
        "no_modify": any(term in request for term in (
            "jangan ubah", "jangan edit", "jangan tulis",
            "jangan cipta", "jangan simpan", "do not modify",
            "do not edit", "do not write", "do not install",
            "do not deploy", "jangan pasang", "jangan memasang",
            "jangan install", "analysis only",
            "analisis sahaja", "plan only", "pelan sahaja"
        )),
        "no_delete": any(term in request for term in (
            "jangan padam", "jangan hapus",
            "do not delete", "do not remove"
        )),
        "no_move": any(term in request for term in (
            "jangan pindah", "jangan alih",
            "do not move", "do not transfer"
        )),
        "no_rename": any(term in request for term in (
            "jangan namakan semula", "jangan tukar nama",
            "do not rename"
        ))
    }

    action_patterns = {
        "no_open": r"\b(open|read|inspect|review|access|scan|examine|browse|buka|membuka|baca|membaca|meneliti|memeriksa|mengakses|menyemak)\b",
        "no_modify": r"\b(create|edit|modify|write|save|update|install|deploy|replace|copy|cipta|mencipta|ubah|mengubah|menulis|menyimpan|pasang|memasang|menyalin)\b",
        "no_delete": r"\b(delete|remove|erase|unlink|padam|memadam|hapus|menghapus)\b",
        "no_move": r"\b(move|relocate|transfer|pindah|memindahkan|mengalih)\b",
        "no_rename": r"\b(rename|namakan semula|menamakan semula)\b"
    }

    file_targets = (
        "file", "files", "fail", "dokumen", "document",
        "folder", "directory", "direktori", "database",
        "pangkalan data", "disk", "drive", "pemacu",
        "server", "sistem", "system", "project folder",
        "folder projek"
    )

    critical_terms = (
        "delete database", "drop database", "destroy database",
        "wipe database", "truncate table", "drop table",
        "format disk", "format drive", "wipe hard drive",
        "shred disk", "factory reset server",
        "padam pangkalan data", "hapus pangkalan data",
        "kosongkan pangkalan data", "padam semua data",
        "delete all data", "destroy all data",
        "hapus semua rekod", "delete all records"
    )

    violations = []

    for number, step in enumerate(steps, 1):
        if isinstance(step, dict):
            text = " ".join(
                str(step.get(key, ""))
                for key in ("action", "step", "description", "target")
            ).lower()
        elif isinstance(step, str):
            text = step.lower()
        else:
            violations.append(
                f"Step {number}: unsupported step format."
            )
            continue

        for restriction, enabled in restrictions.items():
            if not enabled:
                continue

            actions = re.findall(action_patterns[restriction], text)

            if not actions:
                continue

            # An action is blocked when its target is a file,
            # folder, database, disk, server or computer system.
            target_found = any(target in text for target in file_targets)

            # If an action is present but its target is unclear,
            # reject conservatively for owner review.
            context_targets = (
                "maklumat yang diberikan",
                "maklumat yang sudah diberikan",
                "konteks perbualan",
                "perbualan",
                "provided information",
                "information already provided",
                "available context",
                "conversation context",
                "owner's instructions",
                "arahan pemilik",
            )
            context_found = any(target in text for target in context_targets)

            if target_found or (
                restriction == "no_open" and not context_found
            ):
                violations.append(
                    f"Step {number}: {restriction} action "
                    f"targets or may target a restricted resource: {text}"
                )
                break

    plan_text = " ".join(
        str(step).lower() for step in steps
    )

    if any(term in plan_text for term in critical_terms):
        plan["risk_level"] = 4
        plan["approval_required"] = True
        plan["approval_reason"] = (
            "Critical action detected. Specific owner approval required."
        )

    if violations:
        raise ValueError(
            "PLAN REJECTED:\n" + "\n".join(violations)
        )

    if plan.get("risk_level") == 4:
        plan["approval_required"] = True

    validate_plan(plan)
    return plan
