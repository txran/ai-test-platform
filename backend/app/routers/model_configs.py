from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import ModelConfig
from app.utils import format_datetime
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["model-configs"])


def serialize_config(cfg: ModelConfig):
    return {
        "id": cfg.id,
        "name": cfg.name,
        "provider": cfg.provider,
        "base_url": cfg.base_url,
        "api_key": cfg.api_key,
        "model_name": cfg.model_name,
        "is_default": cfg.is_default,
        "created_at": format_datetime(cfg.created_at),
    }


class ConfigCreate(BaseModel):
    name: str
    provider: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: str
    is_default: bool = False


class ConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    is_default: Optional[bool] = None


@router.get("/model-configs")
def list_configs(db: Session = Depends(get_db)):
    configs = db.query(ModelConfig).order_by(ModelConfig.created_at.desc()).all()
    return [serialize_config(c) for c in configs]


@router.post("/model-configs")
def create_config(body: ConfigCreate, db: Session = Depends(get_db)):
    if body.is_default:
        db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})
        db.commit()

    cfg = ModelConfig(
        name=body.name,
        provider=body.provider,
        base_url=body.base_url,
        api_key=body.api_key,
        model_name=body.model_name,
        is_default=body.is_default,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return serialize_config(cfg)


@router.put("/model-configs/{config_id}")
def update_config(config_id: int, body: ConfigUpdate, db: Session = Depends(get_db)):
    cfg = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")

    if body.is_default is not None and body.is_default:
        db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})
        db.commit()

    if body.name is not None:
        cfg.name = body.name
    if body.provider is not None:
        cfg.provider = body.provider
    if body.base_url is not None:
        cfg.base_url = body.base_url
    if body.api_key is not None:
        cfg.api_key = body.api_key
    if body.model_name is not None:
        cfg.model_name = body.model_name
    if body.is_default is not None:
        cfg.is_default = body.is_default

    db.commit()
    db.refresh(cfg)
    return serialize_config(cfg)


@router.delete("/model-configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    cfg = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(cfg)
    db.commit()
    return {"message": "删除成功"}
