import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_audit_logger, get_model_registry, get_training_manager, reset_runtime_state
from app.api.security import require_admin_api_key
from app.logging.audit import PredictionAuditLogger
from app.ml.registry import ModelRegistry
from app.services.control_plane import AsyncTrainingManager

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_api_key)])
logger = logging.getLogger(__name__)


@router.post("/train")
async def trigger_train(manager: AsyncTrainingManager = Depends(get_training_manager)) -> dict:
    payload = manager.start_training()
    logger.info("admin_action", extra={"action": "train", "status": payload["status"]})
    return {"action": "train", **payload}


@router.get("/train/status")
async def train_status(manager: AsyncTrainingManager = Depends(get_training_manager)) -> dict:
    return {"action": "train_status", "training": manager.status()}


@router.post("/activate/{version}")
async def activate(version: str, registry: ModelRegistry = Depends(get_model_registry)) -> dict:
    try:
        registry.activate_version(version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    logger.info("admin_action", extra={"action": "activate", "version": version})
    return {"action": "activate", "status": "ok", "active_version": version}


@router.post("/reload")
async def reload_runtime() -> dict:
    reset_runtime_state()
    logger.info("admin_action", extra={"action": "reload"})
    return {"action": "reload", "status": "ok"}


@router.delete("/audit/clear")
async def clear_audit(audit_logger: PredictionAuditLogger = Depends(get_audit_logger)) -> dict:
    audit_logger.clear()
    logger.info("admin_action", extra={"action": "audit_clear"})
    return {"action": "audit_clear", "status": "ok"}
