import json
from pathlib import Path
from backend.state import CardState

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def template_fetch_agent(state: CardState) -> CardState:
    """
    📦 Template Fetch Agent
    -----------------------
    Job: Load the selected template JSON from disk.
         Pure code — no LLM call needed.
    """
    template_id = state.get("selected_template_id", "minimal_left")

    print(f"[Template Fetch] 📦 Loading template: {template_id}")

    template_file = TEMPLATES_DIR / f"{template_id}.json"

    # --- Try to load individual template file ---
    if template_file.exists():
        with open(template_file, "r") as f:
            template_json = json.load(f)
        print(f"[Template Fetch] ✅ Template loaded from {template_file}")
        return {**state, "template_json": template_json}

    # --- Fallback: load from combined templates file ---
    combined_file = TEMPLATES_DIR / "rolo_card_templates_20.json"
    if combined_file.exists():
        with open(combined_file, "r") as f:
            all_templates = json.load(f)

        for template in all_templates.get("templates", []):
            if template.get("templateId") == template_id:
                print(f"[Template Fetch] ✅ Template found in combined file")
                return {**state, "template_json": template}

    # --- Hard fallback: use minimal_left if nothing found ---
    print(f"[Template Fetch] ⚠️  Template '{template_id}' not found, using minimal_left")
    if combined_file.exists():
        with open(combined_file, "r") as f:
            all_templates = json.load(f)
        for template in all_templates.get("templates", []):
            if template.get("templateId") == "minimal_left":
                return {
                    **state,
                    "template_json": template,
                    "selected_template_id": "minimal_left"
                }

    # --- Last resort: return error ---
    return {
        **state,
        "template_json": None,
        "error": "No templates found. Check templates directory."
    }
