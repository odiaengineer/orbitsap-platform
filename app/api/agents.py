from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Agent, Customer
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

def get_customer(api_key: str = Header(...), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.api_key == api_key).first()
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return customer

class AgentRegister(BaseModel):
    name: str
    sap_sid: str
    sap_host: str
    sap_instance: str
    sap_client: str

@router.post("/agents/register")
def register_agent(
    data: AgentRegister,
    customer: Customer = Depends(get_customer),
    db: Session = Depends(get_db)
):
    agent = Agent(
        customer_id=customer.id,
        name=data.name,
        sap_sid=data.sap_sid,
        status="online",
        last_seen=datetime.utcnow()
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {
        "agent_id": agent.id,
        "name": agent.name,
        "sap_sid": agent.sap_sid,
        "status": agent.status,
        "message": "Agent registered successfully"
    }

@router.get("/agents")
def list_agents(
    customer: Customer = Depends(get_customer),
    db: Session = Depends(get_db)
):
    agents = db.query(Agent).filter(Agent.customer_id == customer.id).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "sap_sid": a.sap_sid,
            "status": a.status,
            "last_seen": a.last_seen
        }
        for a in agents
    ]

@router.post("/agents/{agent_id}/heartbeat")
def heartbeat(
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
    agent.status = "online"
    agent.last_seen = datetime.utcnow()
    db.commit()
    return {"status": "ok", "agent_id": agent_id}
