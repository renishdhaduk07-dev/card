import requests
from colorthief import ColorThief
from backend.state import CardState

SEARCH_API_URL = "https://api.duckduckgo.com/"


# ── helpers ──────────────────────────────────────────────

def _search_logo_on_web(company_name: str) -> str | None:
    """
    Search DuckDuckGo for company logo URL.
    Falls back to Clearbit logo API which is free.
    """
    try:
        # Clearbit Logo API — free, no key needed
        # Returns logo image directly from domain name
        domain_guess = company_name.lower().replace(" ", "") + ".com"
        clearbit_url = f"https://logo.clearbit.com/{domain_guess}"
        resp = requests.head(clearbit_url, timeout=5)
        if resp.status_code == 200:
            print(f"[Enrichment] 🔍 Logo found via Clearbit: {clearbit_url}")
            return clearbit_url
    except Exception as e:
        print(f"[Enrichment] ⚠️  Clearbit logo search failed: {e}")

    return None


def _extract_color_from_image(image_path: str) -> tuple[str | None, str | None]:
    """
    Extract primary and secondary color from a local image file.
    """
    try:
        ct = ColorThief(image_path)
        dominant  = ct.get_color(quality=1)
        primary   = "#{:02X}{:02X}{:02X}".format(*dominant)
        palette   = ct.get_palette(color_count=3, quality=1)
        secondary = "#{:02X}{:02X}{:02X}".format(*palette[1])
        return primary, secondary
    except Exception as e:
        print(f"[Enrichment] ⚠️  Color extraction failed: {e}")
        return None, None


def _extract_company_from_url(url: str) -> str:
    """
    Last resort — extract company name from URL domain.
    e.g. https://google.com → Google
    """
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        name   = domain.replace("www.", "").split(".")[0]
        return name.capitalize()
    except Exception:
        return "Unknown Company"


# ── agent node ───────────────────────────────────────────

def enrichment_agent(state: CardState) -> CardState:
    """
    🎯 Enrichment Agent
    -------------------
    Job: Fix anything missing from Research Agent output.
         - Missing logo    → search Clearbit
         - Missing color   → extract from screenshot
         - Missing company → extract from URL
    """
    missing = state.get("missing_fields", [])

    if not missing:
        print("[Enrichment] ✅ All brand data complete, skipping.")
        return {**state, "brand_data_complete": True}

    print(f"[Enrichment] 🎯 Fixing missing fields: {missing}")

    logo_url       = state.get("logo_url")
    primary_color  = state.get("primary_color")
    secondary_color = state.get("secondary_color")
    company_name   = state.get("company_name")

    # --- Fix logo ---
    if "logo_url" in missing and company_name:
        logo_url = _search_logo_on_web(company_name)
        if logo_url:
            print(f"[Enrichment] ✅ Logo found: {logo_url}")
        else:
            print("[Enrichment] ⚠️  Logo not found, will use fallback.")

    # --- Fix color ---
    if "primary_color" in missing:
        screenshot = state.get("screenshot_path")
        if screenshot:
            primary_color, secondary_color = _extract_color_from_image(
                screenshot
            )
            if primary_color:
                print(f"[Enrichment] ✅ Color extracted: {primary_color}")
            else:
                # Hard fallback
                primary_color  = "#333333"
                secondary_color = "#FFFFFF"
                print("[Enrichment] ⚠️  Using fallback color: #333333")

    # --- Fix company name ---
    if "company_name" in missing:
        company_name = _extract_company_from_url(state["url"])
        print(f"[Enrichment] ✅ Company name extracted: {company_name}")

    # Recalculate missing fields after enrichment
    still_missing = []
    if not logo_url:      still_missing.append("logo_url")
    if not primary_color: still_missing.append("primary_color")
    if not company_name:  still_missing.append("company_name")

    brand_data_complete = len(still_missing) == 0

    print(
        f"[Enrichment] {'✅ Brand data complete' if brand_data_complete else f'⚠️  Still missing: {still_missing}'}"
    )

    return {
        **state,
        "logo_url":            logo_url,
        "primary_color":       primary_color,
        "secondary_color":     secondary_color,
        "company_name":        company_name,
        "missing_fields":      still_missing,
        "brand_data_complete": brand_data_complete,
    }
