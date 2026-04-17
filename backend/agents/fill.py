import json
import os
from pathlib import Path
from groq import Groq
from PIL import Image
from backend.state import CardState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
LOGO_IMAGE_PATH = OUTPUT_DIR / "logo.png"

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
2. NEVER give the same background colour to any other component like email,phonenumber,website,fullname,position,or any other component.
3. NEVER add new components
4. NEVER remove existing components
5. ONLY fill these fields per component:
   - componentStyle  (colors, fontSize, fontWeight, etc.)
   - fallbackText    (name, title, company, email, etc.)
   - visible         (true if data exists, false if not)
   - valueSource     (type + extractedFrom)

═══════════════════════════════════════════════
COLOR RULES:
═══════════════════════════════════════════════
- cardBackground     → use primary_color (if the component is a solid background block)
- fullName           → use #FFFFFF if dark background, #1A1A1A if light background.
- position           → strictly use secondary_color or a vibrant accent derived from primary_color.
- email, phoneNumber, website → USE THE EXACT SAME COLOR as the `position` field.
   This creates visual harmony. Do NOT use grey, yellow, or lime on a light background.
   Pick a color that is sharp and readable — the same brand accent used for position.
- logo               → ALWAYS apply white badge behind logo.
    add white padding so logo never visually blends into card background.
- FINAL STRICT CHECK:
    For EVERY visible text component, color MUST NOT match ANY visible cardBackground color.
    If a collision happens, you MUST replace text with a readable high-contrast color.
    Never return output with text that blends into the background.

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


def _normalize_hex(color: str | None) -> str | None:
    if not color or not isinstance(color, str):
        return None

    value = color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)

    if len(value) != 6:
        return None

    try:
        int(value, 16)
    except ValueError:
        return None

    return f"#{value.upper()}"


def _brightness(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000


def _relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def _linearize(v: float) -> float:
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (_linearize(c) for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    l1 = _relative_luminance(hex_a)
    l2 = _relative_luminance(hex_b)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _rects_overlap(a: dict, b: dict) -> bool:
    a_left = int(a.get("left", 0))
    a_top = int(a.get("top", 0))
    a_width = int(a.get("width", 0))
    a_height = int(a.get("height", 0))
    a_right = a_left + max(a_width, 0)
    a_bottom = a_top + max(a_height, 0)

    b_left = int(b.get("left", 0))
    b_top = int(b.get("top", 0))
    b_width = int(b.get("width", 0))
    b_height = int(b.get("height", 0))
    b_right = b_left + max(b_width, 0)
    b_bottom = b_top + max(b_height, 0)

    return not (a_right <= b_left or b_right <= a_left or a_bottom <= b_top or b_bottom <= a_top)


def _collect_background_layers(populated_json: dict, fallback_primary: str) -> list[dict]:
    layers: list[dict] = []
    for comp in populated_json.get("components", []):
        if not comp.get("visible", True):
            continue
        if comp.get("componentType") != "cardBackground":
            continue

        style = comp.get("componentStyle", {}) or {}
        color = _normalize_hex(style.get("backgroundValue") or style.get("backgroundColor"))
        if not color:
            continue

        coords = comp.get("hCoords", {}) or {}
        width = int(coords.get("width", 0))
        height = int(coords.get("height", 0))
        layer = {
            "zIndex": int(comp.get("zIndex", 0)),
            "area": max(width, 0) * max(height, 0),
            "color": color,
            "rect": {
                "top": int(coords.get("top", 0)),
                "left": int(coords.get("left", 0)),
                "width": width,
                "height": height,
            },
        }
        layers.append(layer)

    if not layers:
        return [{"zIndex": 0, "area": 0, "color": _normalize_hex(fallback_primary) or "#333333", "rect": {"top": 0, "left": 0, "width": 704, "height": 396}}]

    layers.sort(key=lambda item: (item["zIndex"], -item["area"]))
    return layers


def _local_background_color(comp: dict, bg_layers: list[dict], default_bg: str) -> str:
    coords = comp.get("hCoords", {}) or {}
    comp_rect = {
        "top": int(coords.get("top", 0)),
        "left": int(coords.get("left", 0)),
        "width": int(coords.get("width", 0)),
        "height": int(coords.get("height", 0)),
    }
    comp_z = int(comp.get("zIndex", 0))

    candidates = [
        layer for layer in bg_layers
        if layer["zIndex"] <= comp_z and _rects_overlap(comp_rect, layer["rect"])
    ]
    if not candidates:
        return default_bg

    candidates.sort(key=lambda item: (item["zIndex"], item["area"]))
    return candidates[-1]["color"]


def _pick_readable_color(
    local_bg: str,
    preferred: str | None,
    min_contrast: float,
    forbidden: set[str],
) -> str:
    candidates: list[str] = []
    pref = _normalize_hex(preferred)
    if pref:
        candidates.append(pref)

    candidates.extend([
        "#FFFFFF",
        "#1A1A1A",
        "#38BDF8",
        "#2563EB",
        "#22C55E",
        "#F59E0B",
        "#EF4444",
    ])

    ranked = []
    seen = set()
    for color in candidates:
        norm = _normalize_hex(color)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        if norm in forbidden or norm == local_bg:
            continue
        contrast = _contrast_ratio(norm, local_bg)
        ranked.append((contrast, norm))

    if not ranked:
        return "#FFFFFF" if _brightness(local_bg) < 128 else "#1A1A1A"

    valid = [item for item in ranked if item[0] >= min_contrast]
    if valid:
        valid.sort(key=lambda item: item[0], reverse=True)
        return valid[0][1]

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _enforce_strict_text_color_rules(
    populated_json: dict,
    primary_color: str,
    secondary_color: str | None,
) -> dict:
    bg_layers = _collect_background_layers(populated_json, primary_color)
    main_bg = bg_layers[0]["color"]
    forbidden_bg_colors = {layer["color"] for layer in bg_layers}

    default_name = "#FFFFFF" if _brightness(main_bg) < 128 else "#1A1A1A"
    default_accent = _pick_readable_color(
        main_bg,
        _normalize_hex(secondary_color),
        3.0,
        forbidden_bg_colors,
    )

    contact_types = {"email", "phoneNumber", "website", "fbLink", "liLink", "igLink"}

    for comp in populated_json.get("components", []):
        if not comp.get("visible", True):
            continue
        if comp.get("type") != "role_content":
            continue

        ctype = comp.get("componentType", "")
        style = comp.get("componentStyle", {}) or {}
        current_color = _normalize_hex(style.get("color"))

        local_bg = _local_background_color(comp, bg_layers, main_bg)
        min_contrast = 4.5 if ctype in contact_types else 3.0

        if ctype == "fullName":
            preferred = default_name
        elif ctype in {"position", "organization_name"}:
            preferred = default_accent
        else:
            preferred = default_accent

        safe_color = _pick_readable_color(local_bg, preferred, min_contrast, forbidden_bg_colors)

        needs_fix = False
        if not current_color:
            needs_fix = True
        elif current_color in forbidden_bg_colors:
            needs_fix = True
        elif current_color == local_bg:
            needs_fix = True
        elif _contrast_ratio(current_color, local_bg) < min_contrast:
            needs_fix = True

        if needs_fix:
            style["color"] = safe_color
            comp["componentStyle"] = style
            print(
                f"[Fill] ⚠️  Forced safe color for {ctype}: "
                f"{current_color or 'None'} -> {safe_color} (bg: {local_bg})"
            )

    return populated_json


def _extract_logo_representative_color(logo_path: Path) -> str | None:
    if not logo_path.exists():
        return None

    try:
        with Image.open(logo_path) as img:
            rgba = img.convert("RGBA")
            rgba.thumbnail((64, 64))
            reduced = rgba.quantize(colors=64).convert("RGBA")
            colors = reduced.getcolors(maxcolors=4096) or []

        weighted_r = 0.0
        weighted_g = 0.0
        weighted_b = 0.0
        weight_sum = 0.0

        for color_entry in colors:
            if not isinstance(color_entry, tuple) or len(color_entry) != 2:
                continue

            count, rgba_pixel = color_entry
            if not isinstance(rgba_pixel, tuple) or len(rgba_pixel) < 4:
                continue

            r = int(rgba_pixel[0])
            g = int(rgba_pixel[1])
            b = int(rgba_pixel[2])
            a = int(rgba_pixel[3])
            if a < 32:
                continue
            w = (a / 255.0) * count
            weighted_r += r * w
            weighted_g += g * w
            weighted_b += b * w
            weight_sum += w

        if weight_sum == 0:
            return None

        avg_r = int(round(weighted_r / weight_sum))
        avg_g = int(round(weighted_g / weight_sum))
        avg_b = int(round(weighted_b / weight_sum))
        return f"#{avg_r:02X}{avg_g:02X}{avg_b:02X}"
    except Exception as e:
        print(f"[Fill] ⚠️  Logo color extraction failed: {e}")
        return None


def _pick_logo_badge_color(local_bg: str, logo_color: str | None) -> str:
    _ = local_bg
    _ = logo_color
    # Keep badge color deterministic and design-safe.
    return "#FFFFFF"


def _enforce_conditional_logo_badge(populated_json: dict, primary_color: str) -> dict:
    _ = primary_color

    for comp in populated_json.get("components", []):
        if not comp.get("visible", True):
            continue
        if comp.get("componentType") != "logo":
            continue

        style = comp.get("componentStyle", {}) or {}

        raw_padding = style.get("padding")
        existing_padding = raw_padding if isinstance(raw_padding, dict) else {}
        top = int(existing_padding.get("top", 0))
        right = int(existing_padding.get("right", 0))
        bottom = int(existing_padding.get("bottom", 0))
        left = int(existing_padding.get("left", 0))
        pad = max(8, top, right, bottom, left)

        style["backgroundColor"] = "#FFFFFF"
        style["padding"] = {
            "top": pad,
            "right": pad,
            "bottom": pad,
            "left": pad,
        }
        style["autoLogoBadge"] = True
        if not isinstance(style.get("borderRadius"), (int, float)):
            style["borderRadius"] = 8

        comp["componentStyle"] = style
        print(f"[Fill] ✅ Applied white logo badge with {pad}px padding")

    return populated_json


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

        raw = response.choices[0].message.content or "{}"
        populated_json = json.loads(raw)

        # ── Post-Process Safety Net ──────────────
        for comp in populated_json.get("components", []):
            ct = comp.get("componentType")
            if ct == "website" and clean_url:
                comp["visible"] = True
                comp["fallbackText"] = clean_url
            elif ct == "organization_name" and clean_company_name:
                comp["fallbackText"] = clean_company_name

        populated_json = _enforce_strict_text_color_rules(
            populated_json,
            state.get("primary_color") or "#333333",
            state.get("secondary_color") or "#FFFFFF",
        )
        populated_json = _enforce_conditional_logo_badge(
            populated_json,
            state.get("primary_color") or "#333333",
        )
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
