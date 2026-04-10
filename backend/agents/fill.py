import json
import os
from groq import Groq
from backend.state import CardState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FILL_PROMPT = """
You are a professional business card designer AI.

You will receive:
1. A card template JSON with FIXED coordinates
2. Brand data extracted from a website
3. User provided personal information

Your ONLY job is to fill values into the template components.

═══════════════════════════════════════════════
STRICT RULES — NEVER VIOLATE THESE:
═══════════════════════════════════════════════
1. NEVER change hCoords or vCoords values
2. NEVER add new components
3. NEVER remove existing components
4. ONLY fill these fields per component:
   - componentStyle  (colors, fontSize, fontWeight, etc.)
   - fallbackText    (name, title, company, email, etc.)
   - visible         (true if data exists, false if not)
   - valueSource     (type + extractedFrom)

═══════════════════════════════════════════════
COLOR RULES:
═══════════════════════════════════════════════
- cardBackground     → use primary_color as backgroundValue
- If background is DARK  → text color must be #FFFFFF or light
- If background is LIGHT → text color must be #1A1A1A or dark
- fullName           → use bold, slightly larger font
- position           → use accent/lighter version of primary color
- contact fields     → use muted color (#555555 or similar)
- website            → use primary_color with underline
- All colors MUST be valid hex (#RRGGBB)

═══════════════════════════════════════════════
TEXT RULES:
═══════════════════════════════════════════════
- fullName           → fontWeight bold, fontSize 22-28
- position           → textTransform uppercase, letterSpacing 1-2
- organization_name  → fontWeight normal, fontSize 13-15
- contact fields     → fontSize 11-13, fontWeight normal
- If user did NOT provide a field → set visible: false

═══════════════════════════════════════════════
VALUE SOURCE RULES:
═══════════════════════════════════════════════
- Colors/logo from brand data  → type: "ai_extracted", extractedFrom: "og_image" or "screenshot"
- User typed fields            → type: "user_input",   extractedFrom: "text_input"
- Company name from website    → type: "ai_extracted", extractedFrom: "screenshot"

═══════════════════════════════════════════════
OUTPUT:
═══════════════════════════════════════════════
Return ONLY the complete filled JSON object.
No explanation. No markdown. No extra text.
Just the raw JSON.

═══════════════════════════════════════════════
TEMPLATE:
═══════════════════════════════════════════════
{template_json}

═══════════════════════════════════════════════
BRAND DATA:
═══════════════════════════════════════════════
- company_name   : {company_name}
- primary_color  : {primary_color}
- secondary_color: {secondary_color}
- logo_url       : {logo_url}
- og_image_url   : {og_image_url}

═══════════════════════════════════════════════
USER DATA:
═══════════════════════════════════════════════
{user_data}
"""

SELF_CORRECT_PROMPT = """
You are a business card JSON fixer AI.

The following card JSON failed validation.
Fix ONLY the fields mentioned in the errors below.
Do NOT change any coords (hCoords, vCoords).
Return ONLY the corrected JSON, no explanation.

═══════════════════════════════════════════════
ERRORS TO FIX:
═══════════════════════════════════════════════
{errors}

═══════════════════════════════════════════════
CURRENT JSON (fix this):
═══════════════════════════════════════════════
{populated_json}
"""


def fill_agent(state: CardState) -> CardState:
    """
    ✍️ Fill Agent
    -------------
    Job: Send template + brand data + user data to LLM.
         Get back fully populated card JSON (Call 2).
         Also handles self-correction when called after 
         Critic Agent returns INVALID.
    """
    retry_count = state.get("retry_count", 0)
    errors      = state.get("validation_errors", [])

    # --- Self correction mode ---
    if retry_count > 0 and errors:
        print(f"[Fill] 🔁 Self-correcting (attempt {retry_count})...")
        prompt = SELF_CORRECT_PROMPT.format(
            errors="\n".join(f"- {e}" for e in errors),
            populated_json=json.dumps(state["populated_json"], indent=2)
        )
    else:
        # --- Normal fill mode ---
        print("[Fill] ✍️  Filling template with brand + user data...")
        prompt = FILL_PROMPT.format(
            template_json=json.dumps(state["template_json"], indent=2),
            company_name=state.get("company_name", ""),
            primary_color=state.get("primary_color", "#333333"),
            secondary_color=state.get("secondary_color", "#FFFFFF"),
            logo_url=state.get("logo_url", ""),
            og_image_url=state.get("og_image_url", ""),
            user_data=json.dumps(state.get("user_data", {}), indent=2)
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        raw = response.choices[0].message.content
        populated_json = json.loads(raw)

        print("[Fill] ✅ Template filled successfully")

        return {
            **state,
            "populated_json":   populated_json,
            "validation_errors": [],   # reset for next critic pass
        }

    except Exception as e:
        print(f"[Fill] ❌ LLM call failed: {e}")
        return {
            **state,
            "error": f"Fill agent failed: {str(e)}"
        }
