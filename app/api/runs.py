from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Agent, Customer, RefreshRun, RefreshStep
from app.api.agents import get_customer
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

@router.post("/agents/{agent_id}/runs/start")
def start_run(
    agent_id: int,
    customer: Customer = Depends(get_customer),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.customer_id == customer.id
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    run = RefreshRun(agent_id=agent_id, status="pending")
    db.add(run)
    db.commit()
    db.refresh(run)
    return {
        "run_id": run.id,
        "agent_id": agent_id,
        "status": run.status,
        "started_at": run.started_at,
        "message": "Refresh run started"
    }

@router.post("/runs/{run_id}/steps")
def update_step(
    run_id: int,
    step_name: str,
    status: str,
    message: str = None,
    customer: Customer = Depends(get_customer),
    db: Session = Depends(get_db)
):
    run = db.query(RefreshRun).filter(RefreshRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    step = RefreshStep(
        run_id=run_id,
        step_name=step_name,
        status=status,
        message=message,
        executed_at=datetime.utcnow()
    )
    db.add(step)
    db.commit()
    return {"message": "Step recorded", "step": step_name, "status": status}

@router.post("/runs/{run_id}/complete")
def complete_run(
    run_id: int,
    status: str = "completed",
    customer: Customer = Depends(get_customer),
    db: Session = Depends(get_db)
):
    run = db.query(RefreshRun).filter(RefreshRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = status
    run.completed_at = datetime.utcnow()
    db.commit()
    return {"run_id": run_id, "status": status, "completed_at": run.completed_at}

@router.get("/agents/{agent_id}/runs")
def list_runs(
    agent_id: int,
    customer: Customer = Depends(get_customer),
    db: Session = Depends(get_db)
):
    runs = db.query(RefreshRun).filter(RefreshRun.agent_id == agent_id).all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "steps": [
                {
                    "step": s.step_name,
                    "status": s.status,
                    "message": s.message,
                    "executed_at": s.executed_at
                }
                for s in r.steps
            ]
        }
        for r in runs
    ]
