from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Agent, Customer
from app.api.agents import get_customer
import subprocess
import time

router = APIRouter()

SAP_USER = "dpkadm"

def ssh_run(host, command):
    result = subprocess.run(
        ['ssh', f'{SAP_USER}@{host}', command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60
    )
    return result.stdout.decode().strip(), result.stderr.decode().strip(), result.returncode

def parse_processes(raw):
    processes = []
    lines = raw.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if 'name, description' in line:
            continue
        if 'GetProcessList' in line:
            continue
        if 'OK' == line:
            continue
        if line[0].isdigit():
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 4 and parts[2] in ['GREEN', 'YELLOW', 'RED', 'GRAY']:
            processes.append({
                'name': parts[0],
                'description': parts[1],
                'status': parts[2],
                'text': parts[3],
                'pid': parts[6].strip() if len(parts) > 6 else ''
            })
    return processes

@router.get("/agents/{agent_id}/processes")
def get_processes(
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

    out, err, rc = ssh_run("bestehp", "sapcontrol -nr 67 -function GetProcessList")
    processes = parse_processes(out)
    overall = "GREEN" if processes and all(p['status'] == 'GREEN' for p in processes) else "RED"
    return {
        "sid": agent.sap_sid,
        "host": "bestehp",
        "instance": "67",
        "overall": overall,
        "processes": processes
    }

@router.post("/agents/{agent_id}/stop")
def stop_sap(
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
    out, err, rc = ssh_run("bestehp", "sapcontrol -nr 67 -function Stop")
    return {"status": "success", "message": "SAP stop command issued", "sid": agent.sap_sid}

@router.post("/agents/{agent_id}/start")
def start_sap(
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
    out, err, rc = ssh_run("bestehp", "sapcontrol -nr 67 -function Start")
    return {"status": "success", "message": "SAP start command issued", "sid": agent.sap_sid}

@router.post("/agents/{agent_id}/restart")
def restart_sap(
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
    ssh_run("bestehp", "sapcontrol -nr 67 -function Stop")
    time.sleep(5)
    ssh_run("bestehp", "sapcontrol -nr 67 -function Start")
    return {"status": "success", "message": "SAP restart initiated", "sid": agent.sap_sid}
