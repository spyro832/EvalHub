from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptOut

router = APIRouter()


@router.get("", response_model=list[PromptOut])
async def list_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prompt).order_by(Prompt.updated_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
async def create_prompt(data: PromptCreate, db: AsyncSession = Depends(get_db)):
    prompt = Prompt(**data.model_dump())
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptOut)
async def get_prompt(prompt_id: str, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return prompt


@router.put("/{prompt_id}", response_model=PromptOut)
async def update_prompt(prompt_id: str, data: PromptCreate, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    for field, value in data.model_dump().items():
        setattr(prompt, field, value)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(prompt_id: str, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    await db.delete(prompt)
    await db.commit()
