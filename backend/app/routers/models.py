from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encrypt_api_key
from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigOut

router = APIRouter()


@router.get("", response_model=list[ModelConfigOut])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.is_active == True).order_by(ModelConfig.name)  # noqa: E712
    )
    return list(result.scalars().all())


@router.post("", response_model=ModelConfigOut, status_code=status.HTTP_201_CREATED)
async def create_model(data: ModelConfigCreate, db: AsyncSession = Depends(get_db)):
    model = ModelConfig(
        name=data.name,
        provider=data.provider,
        model_id=data.model_id,
        base_url=data.base_url,
        is_local=data.is_local,
        cost_per_input_token=data.cost_per_input_token,
        cost_per_output_token=data.cost_per_output_token,
    )
    if data.api_key:
        model.api_key_encrypted = encrypt_api_key(data.api_key)
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    model = await db.get(ModelConfig, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    model.is_active = False
    await db.commit()
