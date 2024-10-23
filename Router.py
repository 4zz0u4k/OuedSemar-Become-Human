from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services import StoryService

router = APIRouter(prefix="/game", tags=["game"])
story_service = StoryService()

class Choice(BaseModel):
    choice: int

@router.post("/start/{player_id}")
async def start_game(player_id: str) -> Dict:
    try:
        return await story_service.start_new_game(player_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/choice/{player_id}")
async def make_choice(player_id: str, choice: Choice) -> Dict:
    if not 1 <= choice.choice <= 3:
        raise HTTPException(status_code=400, detail="Choice must be between 1 and 3")
    
    try:
        return await story_service.make_choice(player_id, choice.choice)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))