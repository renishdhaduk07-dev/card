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
- cardBackground     → use primary_color (if the component is a solid background block)
- strictly follow this : do not give the same background colour to any other component like email,phonenumber,website,fullname,position,or any other component .
- fullName           → use #FFFFFF if dark background, #1A1A1A if light background.
- position           → strictly use secondary_color or a vibrant accent derived from primary_color.
- email, phoneNumber, website → USE THE EXACT SAME COLOR as the `position` field.
   This creates visual harmony. Do NOT use grey, yellow, or lime on a light background.
   Pick a color that is sharp and readable — the same brand accent used for position.

═══════════════════════════════════════════════
TEXT RULES:
═══════════════════════════════════════════════
- fullName           → fontWeight bold, fontSize 22-28
- position           → textTransform uppercase, letterSpacing 1-2
- organization_name  → Extract ONLY the core, short business name! Drop SEO taglines (e.g. use "PayPal" instead of "A Simple and Safer Way... | PayPal IN").
- website            → CRITICAL: Set visible to true and use EXACTLY `{website_url}` as fallbackText. Do NOT hide it.
- contact fields     → fontSize 11-13, fontWeight normal
- For other fields (fbLink, liLink, igLink) → if not in user_data, set visible: false

═══════════════════════════════════════════════
VALUE SOURCE RULES:
═══════════════════════════════════════════════
- Colors/logo from brand data  → type: "ai_extracted", extractedFrom: "og_image" or "screenshot"
- User typed fields            → type: "user_input",   extractedFrom: "text_input"
- Company name from website    → type: "ai_extracted", extractedFrom: "screenshot"
- website field                → map the exact `website_url` value into the `fallbackText` field!

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
- website_url    : {website_url}

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

    # ── Always compute these so post-processing can use them ──
    raw_company_name = state.get("company_name", "") or ""
    parts = raw_company_name.replace("|", "-").split("-")
    parts = [p.strip() for p in parts if p.strip()]
    clean_company_name = min(parts, key=len) if len(parts) > 1 else raw_company_name

    url_input = state.get("url", "") or ""
    clean_url = url_input.replace("https://", "").replace("http://", "").strip("/")

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
            company_name=clean_company_name,
            primary_color=state.get("primary_color", "#333333"),
            secondary_color=state.get("secondary_color", "#FFFFFF"),
            logo_url=state.get("logo_url", ""),
            og_image_url=state.get("og_image_url", ""),
            website_url=clean_url,
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

        # ── Post-Process Safety Net ──────────────
        for comp in populated_json.get("components", []):
            ct = comp.get("componentType")
            if ct == "website" and clean_url:
                comp["visible"] = True
                comp["fallbackText"] = clean_url
            elif ct == "organization_name" and clean_company_name:
                comp["fallbackText"] = clean_company_name
        # ─────────────────────────────────────────

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
