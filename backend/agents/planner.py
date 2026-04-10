from backend.state import CardState
from urllib.parse import urlparse


def planner_agent(state: CardState) -> CardState:
    """
    🧠 Planner Agent
    ----------------
    Job: Validate input, check what user_data is 
         provided vs missing, build a task plan.
    """
    url = state.get("url", "").strip()
    user_data = state.get("user_data", {})

    # --- Validate URL ---
    try:
        parsed = urlparse(url)
        url_valid = all([parsed.scheme, parsed.netloc])
    except Exception:
        url_valid = False

    if not url_valid:
        return {
            **state,
            "url_valid": False,
            "error": f"Invalid URL provided: '{url}'"
        }

    # --- Check user_data fields ---
    required_fields = ["fullName", "position", "email", "phoneNumber"]
    provided = {k: v for k, v in user_data.items() if v}
    missing_user_fields = [f for f in required_fields if f not in provided]

    # --- Build plan ---
    plan = {
        "url": url,
        "user_data_provided": list(provided.keys()),
        "user_data_missing": missing_user_fields,
        "steps": [
            "research",
            "enrichment",
            "template_selection",
            "template_fetch",
            "fill",
            "critic"
        ],
        "notes": (
            f"Missing user fields: {missing_user_fields}"
            if missing_user_fields
            else "All user fields provided"
        )
    }

    print(f"[Planner] ✅ URL valid: {url}")
    print(f"[Planner] 📋 Plan created: {plan['notes']}")

    return {
        **state,
        "url_valid": True,
        "plan": plan,
        "error": None,
        # Initialize defaults
        "retry_count": 0,
        "validation_passed": False,
        "validation_errors": [],
        "missing_fields": [],
        "brand_data_complete": False
    }
