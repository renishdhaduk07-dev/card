import re
from backend.state import CardState

MAX_RETRIES = 3

# Valid hex color pattern
HEX_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')

# Components that MUST have fallbackText
REQUIRED_TEXT_COMPONENTS = {"fullName", "position", "organization_name"}

# Components that MUST have a color in componentStyle
REQUIRED_COLOR_COMPONENTS = {"fullName", "position", "organization_name",
                              "email", "phoneNumber", "website"}


def _is_valid_hex(color: str) -> bool:
    return bool(HEX_PATTERN.match(color)) if color else False


def _get_original_component(component_id: str, template_json: dict) -> dict | None:
    for c in template_json.get("components", []):
        if c.get("id") == component_id:
            return c
    return None


def critic_agent(state: CardState) -> CardState:
    """
    🔍 Critic Agent
    ---------------
    Job: Validate the populated JSON from Fill Agent.
         Returns VALID or INVALID with detailed errors.
    """
    print("[Critic] 🔍 Validating populated JSON...")

    populated = state.get("populated_json")
    template  = state.get("template_json")
    errors    = []

    if not populated:
        return {
            **state,
            "validation_passed": False,
            "validation_errors": ["populated_json is empty or None"]
        }

    if not template:
        return {
            **state,
            "validation_passed": False,
            "validation_errors": ["template_json is missing for coord comparison"]
        }

    components = populated.get("components", [])

    if not components:
        errors.append("No components found in populated_json")

    for comp in components:
        comp_id   = comp.get("id", "unknown")
        comp_type = comp.get("componentType", "")
        style     = comp.get("componentStyle", {})
        visible   = comp.get("visible", True)

        # ── 1. Coords must not change ──────────────────────────
        original = _get_original_component(comp_id, template)
        if original:
            orig_h = original.get("hCoords", {})
            curr_h = comp.get("hCoords", {})
            if orig_h != curr_h:
                errors.append(
                    f"[{comp_id}] hCoords changed! "
                    f"Expected {orig_h}, got {curr_h}"
                )

            orig_v = original.get("vCoords", {})
            curr_v = comp.get("vCoords", {})
            if orig_v != curr_v:
                errors.append(
                    f"[{comp_id}] vCoords changed! "
                    f"Expected {orig_v}, got {curr_v}"
                )

        # ── 2. Valid hex colors ────────────────────────────────
        if visible and comp_type in REQUIRED_COLOR_COMPONENTS:
            color = style.get("color")
            if color and not _is_valid_hex(color):
                errors.append(
                    f"[{comp_id}] Invalid text color: '{color}'"
                )

        bg_value = style.get("backgroundValue")
        if bg_value and style.get("backgroundType") == "color":
            if not _is_valid_hex(bg_value):
                errors.append(
                    f"[{comp_id}] Invalid backgroundColor: '{bg_value}'"
                )

        # ── 3. Required text fields must have fallbackText ─────
        if comp_type in REQUIRED_TEXT_COMPONENTS and visible:
            text = comp.get("fallbackText", "").strip()
            if not text:
                errors.append(
                    f"[{comp_id}] '{comp_type}' is visible but has no fallbackText"
                )

        # ── 4. fontSize must be within range ───────────────────
        font_size = style.get("fontSize")
        if font_size is not None:
            if not (8 <= font_size <= 72):
                errors.append(
                    f"[{comp_id}] fontSize {font_size} out of range (8-72)"
                )

        # ── 5. opacity must be 0-1 ────────────────────────────
        opacity = style.get("opacity")
        if opacity is not None:
            if not (0 <= opacity <= 1):
                errors.append(
                    f"[{comp_id}] opacity {opacity} out of range (0-1)"
                )

        # ── 6. zIndex must exist ──────────────────────────────
        if "zIndex" not in comp:
            errors.append(f"[{comp_id}] missing zIndex field")

        # ── 7. valueSource must be present ───────────────────
        if "valueSource" not in comp:
            errors.append(f"[{comp_id}] missing valueSource field")

    # ── Result ────────────────────────────────────────────────
    passed = len(errors) == 0

    if passed:
        print("[Critic] ✅ Validation PASSED")
    else:
        print(f"[Critic] ❌ Validation FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  → {e}")

    return {
        **state,
        "validation_passed": passed,
        "validation_errors": errors,
        "retry_count": state.get("retry_count", 0) + (0 if passed else 1),
    }


def decide_critic_result(state: CardState) -> str:
    """
    Edge decision function for LangGraph.
    Returns 'valid' or 'invalid'.
    """
    if state["validation_passed"]:
        return "valid"

    if state.get("retry_count", 0) >= MAX_RETRIES:
        print(f"[Critic] ⚠️  Max retries ({MAX_RETRIES}) reached, forcing finalize.")
        return "valid"

    return "invalid"
