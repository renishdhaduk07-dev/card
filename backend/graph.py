from langgraph.graph import StateGraph, END
from backend.state import CardState

# Import all agents
from backend.agents.planner           import planner_agent
from backend.agents.research          import research_agent
from backend.agents.enrichment        import enrichment_agent
from backend.agents.template_selection import template_selection_agent
from backend.agents.template_fetch    import template_fetch_agent
from backend.agents.fill              import fill_agent
from backend.agents.critic            import critic_agent, decide_critic_result


def finalize(state: CardState) -> CardState:
    """
    Final node — clean up and return final card JSON.
    """
    print("[Finalize] 🎉 Card generation complete!")
    return {
        **state,
        "final_card_json": state.get("populated_json"),
        "error": None
    }


def build_graph():
    graph = StateGraph(CardState)

    # ── Register all nodes ────────────────────────────────
    graph.add_node("planner",            planner_agent)
    graph.add_node("research",           research_agent)
    graph.add_node("enrichment",         enrichment_agent)
    graph.add_node("template_selection", template_selection_agent)
    graph.add_node("template_fetch",     template_fetch_agent)
    graph.add_node("fill",               fill_agent)
    graph.add_node("critic",             critic_agent)
    graph.add_node("finalize",           finalize)

    # ── Entry point ───────────────────────────────────────
    graph.set_entry_point("planner")

    # ── Linear edges ─────────────────────────────────────
    graph.add_edge("planner",            "research")
    graph.add_edge("research",           "enrichment")
    graph.add_edge("enrichment",         "template_selection")
    graph.add_edge("template_selection", "template_fetch")
    graph.add_edge("template_fetch",     "fill")
    graph.add_edge("fill",               "critic")

    # ── Critic conditional edge ───────────────────────────
    # valid   → finalize → END
    # invalid → fill     → critic (loop, max 3 retries)
    graph.add_conditional_edges(
        "critic",
        decide_critic_result,
        {
            "valid":   "finalize",
            "invalid": "fill"
        }
    )

    graph.add_edge("finalize", END)

    return graph.compile()


# ── Run ───────────────────────────────────────────────────
compiled_graph = build_graph()


def run_agent(url: str, user_data: dict) -> dict:
    """
    Main entry point to run the full agent pipeline.
    
    Args:
        url       : Website URL to extract brand data from
        user_data : Dict with keys: fullName, position, 
                    email, phoneNumber, website, etc.
    
    Returns:
        final_card_json : Fully populated card JSON ready to render
    """
    initial_state: CardState = {
        "url":                      url,
        "user_data":                user_data,
        "plan":                     {},
        "url_valid":                False,
        "og_image_url":             None,
        "screenshot_path":          None,
        "og_image_path":            None,
        "company_name":             None,
        "company_description":      None,
        "logo_url":                 None,
        "primary_color":            None,
        "secondary_color":          None,
        "color_system":             None,
        "all_extracted_colors":     None,
        "brand_data_complete":      False,
        "missing_fields":           [],
        "rejected_templates":       [],
        "selected_template_id":     None,
        "template_selection_reason": None,
        "template_json":            None,
        "populated_json":           None,
        "validation_passed":        False,
        "validation_errors":        [],
        "retry_count":              0,
        "final_card_json":          None,
        "error":                    None,
    }

    result = compiled_graph.invoke(initial_state)
    return result


def build_regen_graph():
    graph = StateGraph(CardState)
    graph.add_node("template_selection", template_selection_agent)
    graph.add_node("template_fetch",     template_fetch_agent)
    graph.add_node("fill",               fill_agent)
    graph.add_node("critic",             critic_agent)
    graph.add_node("finalize",           finalize)
    
    graph.set_entry_point("template_selection")
    graph.add_edge("template_selection", "template_fetch")
    graph.add_edge("template_fetch",     "fill")
    graph.add_edge("fill",               "critic")
    graph.add_conditional_edges(
        "critic",
        decide_critic_result,
        {
            "valid":   "finalize",
            "invalid": "fill"
        }
    )
    graph.add_edge("finalize", END)
    return graph.compile()

compiled_regen_graph = build_regen_graph()


def run_regen_agent(previous_state: dict, rejected_templates: list) -> dict:
    """
    Entry point to regenerate skipping research and enrichment.
    """
    previous_state["rejected_templates"] = rejected_templates
    previous_state["retry_count"] = 0
    previous_state["error"] = None
    previous_state["validation_passed"] = False
    previous_state["validation_errors"] = []
    
    result = compiled_regen_graph.invoke(previous_state)
    return result


# ── Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    result = run_agent(
        url="https://stripe.com",
        user_data={
            "fullName":    "John Doe",
            "position":    "Software Engineer",
            "email":       "john@stripe.com",
            "phoneNumber": "+1 234 567 8900",
        }
    )

    print("\n" + "="*50)
    print("FINAL CARD JSON:")
    print("="*50)
    print(json.dumps(result.get("final_card_json"), indent=2))

    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
