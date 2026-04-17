from typing import TypedDict, Optional, List

class CardState(TypedDict):
    # ---------- Input ----------
    url: str
    user_data: dict          # name, title, email, phone, etc.

    # ---------- Planner ----------
    plan: dict
    url_valid: bool

    # ---------- Research ----------
    og_image_url: Optional[str]
    screenshot_path: Optional[str]
    og_image_path: Optional[str]
    company_name: Optional[str]
    company_description: Optional[str]
    logo_url: Optional[str]
    logo_path: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    color_system: Optional[dict]
    all_extracted_colors: Optional[list]

    # ---------- Enrichment ----------
    brand_data_complete: bool
    missing_fields: List[str]

    # ---------- Template Selection ----------
    rejected_templates: List[str]
    selected_template_id: Optional[str]
    template_selection_reason: Optional[str]

    # ---------- Template Fetch ----------
    template_json: Optional[dict]

    # ---------- Fill ----------
    populated_json: Optional[dict]

    # ---------- Critic ----------
    validation_passed: bool
    validation_errors: List[str]
    retry_count: int

    # ---------- Final ----------
    final_card_json: Optional[dict]
    error: Optional[str]
