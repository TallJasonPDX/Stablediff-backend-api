from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models import Workflow
from app.dependencies import get_current_active_user

router = APIRouter()

# Example workflows - in production these would come from a database
WORKFLOWS = [
    Workflow(
        id="lastnurses_api",
        name="lastnurses_api",
        display_name="The Last Nurses",
        description=
        "See your workplace as the Post-apocalyptic world it already is.",
    ),
    Workflow(
        id="nursefilter_v2",
        name="nursefilter_v2",
        display_name="Modern Nurse Filter",
        description="Contemporary medical professional style",
    )
]


@router.get("/list", response_model=List[Workflow])
async def list_workflows(current_user=Depends(get_current_active_user)):
    """List all available workflows"""
    return WORKFLOWS


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str,
                       current_user=Depends(get_current_active_user)):
    """Get workflow details by ID"""
    workflow = next((w for w in WORKFLOWS if w.id == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Workflow not found")
    return workflow
