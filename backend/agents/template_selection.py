import json
import os
import random
from groq import Groq
from backend.state import CardState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── 5 Buckets with templates inside ──────────────────────

BUCKETS = {
    "CORPORATE": ["bold_header", "top_banner", "classic_clean", "bottom_bar", "executive_gold"],
    "CREATIVE":  ["split", "right_accent", "centered", "corner_box", "magazine_editorial"],
    "TECH":      ["dark_modern", "minimal_left", "neon_tech", "two_column"],
    "VIBRANT":   ["gradient_flow", "vibrant_block", "logo_hero"],
    "PERSONAL":  ["centered", "top_banner", "name_large", "pastel_soft", "minimal_right"]
}

# ── LLM Prompt — only 5 choices ──────────────────────────

BUCKET_PROMPT = """
You are a business card design classifier.

Look at this brand and pick ONE category:

CORPORATE = formal businesses, law, finance, consulting, B2B, enterprises
TECH      = software, SaaS, startups, developer tools, AI, cloud, APIs
CREATIVE  = agencies, branding, design studios, architecture, media, photography
VIBRANT   = retail, food, events, health, wellness, consumer apps, fintech
PERSONAL  = freelancers, coaches, personal brands, artists, portfolios

Brand:
- Company : {company_name}
- Description: {description}
- URL     : {url}

Return ONLY this JSON, nothing else:
{{"bucket": "CORPORATE"}}
"""

# ── Main Agent ────────────────────────────────────────────

def template_selection_agent(state: CardState) -> CardState:
    """
    🎨 Template Selection Agent
    ---------------------------
    Step 1: LLM picks 1 of 5 buckets
    Step 2: Random template picked from inside that bucket
    """
    print("[Template Selection] 🎨 Picking best template...")

    company_name = state.get("company_name", "Unknown")
    description  = state.get("company_description", "")
    source_url   = state.get("url", "")

    # ── Step 1: LLM picks bucket ──────────────────────────
    bucket = "CORPORATE"  # safe default

    try:
        prompt = BUCKET_PROMPT.format(
            company_name=company_name,
            description=description,
            url=source_url
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw    = response.choices[0].message.content
        result = json.loads(raw)
        bucket = result.get("bucket", "CORPORATE").upper()

        if bucket not in BUCKETS:
            print(f"[Template Selection] ⚠️  Invalid bucket '{bucket}', defaulting to CORPORATE")
            bucket = "CORPORATE"

        print(f"[Template Selection] 🪣 Bucket: {bucket}")

    except Exception as e:
        print(f"[Template Selection] ❌ LLM failed: {e}, using default bucket")

    # ── Step 2: Random template from bucket ───────────────
    rejected = state.get("rejected_templates", [])
    available_in_bucket = [t for t in BUCKETS[bucket] if t not in rejected]
    
    if available_in_bucket:
        final_template = random.choice(available_in_bucket)
    else:
        # Fallback to ANY template not rejected
        all_templates = [t for bucket_templates in BUCKETS.values() for t in bucket_templates]
        available_overall = [t for t in all_templates if t not in rejected]
        if available_overall:
            final_template = random.choice(available_overall)
            print(f"[Template Selection] ⚠️ Bucket exhausted, picked {final_template} overall")
        else:
            # Everything rejected? Just pick any random completely
            final_template = random.choice(all_templates)
            print(f"[Template Selection] ⚠️ ALL exhausted, forced {final_template}")

    print(f"[Template Selection] ✅ Final: {final_template} (random from {bucket})")

    return {
        **state,
        "selected_template_id":      final_template,
        "template_selection_reason": f"{bucket} → {final_template} (random excluding {rejected})",
    }
