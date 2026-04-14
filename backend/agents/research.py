import io
from pathlib import Path
from playwright.sync_api import sync_playwright
from colorthief import ColorThief
from PIL import Image
from backend.state import CardState

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SCREENSHOT_PATH = OUTPUT_DIR / "website_snapshot.png"
OG_IMAGE_PATH   = OUTPUT_DIR / "og_image_snapshot.png"
LOGO_IMAGE_PATH = OUTPUT_DIR / "logo.png"
LOAD_DELAY_MS   = 5000
USER_AGENT      = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# -- helpers -------------------------------------------------

def _get_og_image_url(page) -> str | None:
    meta = page.query_selector(
        'meta[property="og:image"],'
        'meta[name="og:image"],'
        'meta[property="og:image:secure_url"]'
    )
    return meta.get_attribute("content") if meta else None


def _save_og_image(context, image_url: str) -> None:
    resp = context.request.get(image_url, timeout=30000)
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status} fetching og:image")
    data = resp.body()
    with Image.open(io.BytesIO(data)) as img:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(OG_IMAGE_PATH, format="PNG")


def _save_logo_image(context, image_url: str) -> None:
    resp = context.request.get(image_url, timeout=30000)
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status} fetching logo")
    data = resp.body()
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.save(LOGO_IMAGE_PATH, format="PNG")
    except Exception as e:
        print(f"[Research] Warning: Could not save logo as PNG (might be SVG): {e}")


def _get_company_name(page) -> str | None:
    for selector in [
        'meta[property="og:site_name"]',
        'meta[property="og:title"]',
    ]:
        tag = page.query_selector(selector)
        if tag:
            val = tag.get_attribute("content")
            if val:
                return val.strip()
    title = page.title()
    return title.strip() if title else None


def _get_company_description(page) -> str | None:
    """
    Extract company description in priority order:
    1. meta description
    2. og:description
    3. twitter:description
    4. First meaningful paragraph
    """

    for selector in [
        'meta[name="description"]',
        'meta[property="og:description"]',
        'meta[name="twitter:description"]',
    ]:
        try:
            tag = page.query_selector(selector)
            if tag:
                val = tag.get_attribute("content")
                if val and len(val.strip()) > 10:
                    return val.strip()[:300]
        except Exception:
            continue

    try:
        p_tags = page.query_selector_all("p")
        for p_tag in p_tags[:10]:
            text = p_tag.inner_text().strip()
            if len(text) > 40:
                return text[:300]
    except Exception:
        pass

    return None


def _get_logo_url(page, base_url: str) -> str | None:
    for selector in [
        'link[rel="apple-touch-icon"]',
        'link[rel="shortcut icon"]',
        'link[rel="icon"]',
    ]:
        tag = page.query_selector(selector)
        if tag:
            href = tag.get_attribute("href")
            if href:
                return href if href.startswith("http") else f"{base_url}{href}"
    return None


def _extract_colors(image_path: str) -> tuple[str | None, str | None]:
    try:
        ct = ColorThief(image_path)
        dominant = ct.get_color(quality=1)
        primary  = "#{:02X}{:02X}{:02X}".format(*dominant)
        palette  = ct.get_palette(color_count=3, quality=1)
        secondary = "#{:02X}{:02X}{:02X}".format(*palette[1])
        return primary, secondary
    except Exception as e:
        print(f"[Research] Warning: Color extraction failed: {e}")
        return None, None


def _reset_output_artifacts() -> None:
    """Clear previous run artifacts to avoid stale file leakage."""
    for path in (SCREENSHOT_PATH, OG_IMAGE_PATH, LOGO_IMAGE_PATH):
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            print(f"[Research] Warning: Could not remove {path.name}: {e}")


# -- main playwright runner --------------------------------

def _run_playwright(url: str) -> dict:
    _reset_output_artifacts()

    og_image_url   = None
    company_name   = None
    company_description = None
    logo_url       = None
    primary_color  = None
    secondary_color = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page    = context.new_page()

        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(LOAD_DELAY_MS)

            og_image_url = _get_og_image_url(page)
            page_title = page.title()

            # Retry if Cloudflare challenge or response error
            if (
                not og_image_url
                or page_title == "Just a moment..."
                or (response and response.status >= 400)
            ):
                page.wait_for_timeout(LOAD_DELAY_MS)
                response = page.reload(wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(LOAD_DELAY_MS)
                og_image_url = _get_og_image_url(page)

            # Screenshot
            screenshot_bytes = page.screenshot()
            with open(SCREENSHOT_PATH, "wb") as f:
                f.write(screenshot_bytes)

            # Meta extraction
            company_name = _get_company_name(page)
            company_description = _get_company_description(page)
            base_url = "/".join(url.split("/")[:3])
            logo_url = _get_logo_url(page, base_url)

            # Priority 1: Extract colors from OG image
            if og_image_url:
                try:
                    _save_og_image(context, og_image_url)
                    if OG_IMAGE_PATH.exists():
                        primary_color, secondary_color = _extract_colors(str(OG_IMAGE_PATH))
                except Exception as e:
                    print(f"[Research] Warning: OG image error: {e}")

            # Priority 2: Extract colors from logo if OG failed
            if logo_url:
                try:
                    _save_logo_image(context, logo_url)
                    if not primary_color and LOGO_IMAGE_PATH.exists():
                        primary_color, secondary_color = _extract_colors(str(LOGO_IMAGE_PATH))
                except Exception as e:
                    print(f"[Research] Warning: Logo fetch error: {e}")

            # Priority 3: Extract from screenshot if both OG and logo failed
            if not primary_color:
                primary_color, secondary_color = _extract_colors(str(SCREENSHOT_PATH))

        except Exception as e:
            print(f"[Research] Error: Playwright failed: {e}")
        finally:
            browser.close()

    return {
        "og_image_url":    og_image_url,
        "screenshot_path": str(SCREENSHOT_PATH),
        "og_image_path":   str(OG_IMAGE_PATH) if OG_IMAGE_PATH.exists() else None,
        "company_name":    company_name,
        "company_description": company_description,
        "logo_url":        logo_url,
        "primary_color":   primary_color,
        "secondary_color": secondary_color,
    }


# -- agent node --------------------------------------------

def research_agent(state: CardState) -> CardState:
    """
    Research Agent
    Job: Run Playwright and return all extracted brand data.
    """
    print(f"[Research] Running Playwright for: {state['url']}")

    result = _run_playwright(state["url"])

    missing = []
    if not result["logo_url"]:
        missing.append("logo_url")
    if not result["primary_color"]:
        missing.append("primary_color")
    if not result["company_name"]:
        missing.append("company_name")

    print(f"[Research] Done. Missing fields: {missing or 'none'}")

    return {
        **state,
        "og_image_url":    result["og_image_url"],
        "screenshot_path": result["screenshot_path"],
        "og_image_path":   result["og_image_path"],
        "company_name":    result["company_name"],
        "company_description": result["company_description"],
        "logo_url":        result["logo_url"],
        "primary_color":   result["primary_color"],
        "secondary_color": result["secondary_color"],
        "missing_fields":  missing,
    }
