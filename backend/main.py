from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from backend.graph import run_agent, run_regen_agent
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(
    title="Rolo AI Card Generator",
    description="Multi-agent pipeline to generate business cards from a URL",
    version="1.0.0"
)

# Allow Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserData(BaseModel):
    fullName:    str
    position:    str
    email:       str
    phoneNumber: str
    website:     Optional[str] = None
    fbLink:      Optional[str] = None
    liLink:      Optional[str] = None
    igLink:      Optional[str] = None


class GenerateCardRequest(BaseModel):
    url:       str
    user_data: UserData


class GenerateCardResponse(BaseModel):
    success:        bool
    final_card_json: Optional[dict] = None
    template_id:    Optional[str]   = None
    backend_state:  Optional[dict]  = None
    error:          Optional[str]   = None


class RegenerateCardRequest(BaseModel):
    backend_state:      dict
    rejected_templates: list[str]


@app.post("/generate-card", response_model=GenerateCardResponse)
def generate_card(request: GenerateCardRequest):
    """
    Main endpoint — runs the full agent pipeline.
    
    Input:  URL + user_data
    Output: Fully populated card JSON
    """
    try:
        result = run_agent(
            url=request.url,
            user_data=request.user_data.model_dump()
        )

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )

        return GenerateCardResponse(
            success=True,
            final_card_json=result.get("final_card_json"),
            template_id=result.get("selected_template_id"),
            backend_state=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        return GenerateCardResponse(
            success=False,
            error=str(e)
        )


@app.post("/regenerate-card", response_model=GenerateCardResponse)
def regenerate_card(request: RegenerateCardRequest):
    """
    Endpoint to regenerate a card using a different template
    skipping the research and enrichment steps.
    """
    try:
        result = run_regen_agent(
            previous_state=request.backend_state,
            rejected_templates=request.rejected_templates
        )

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )

        return GenerateCardResponse(
            success=True,
            final_card_json=result.get("final_card_json"),
            template_id=result.get("selected_template_id"),
            backend_state=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        return GenerateCardResponse(
            success=False,
            error=str(e)
        )


@app.get("/health")
def health():
    return {"status": "ok"}


# Run with: uvicorn backend.main:app --reload
