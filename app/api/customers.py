from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Customer
from pydantic import BaseModel
import secrets

router = APIRouter()

class CustomerCreate(BaseModel):
    name: str
    email: str

@router.post("/customers/register")
def register_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter(Customer.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    api_key = secrets.token_hex(32)
    customer = Customer(name=data.name, email=data.email, api_key=api_key)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "api_key": customer.api_key,
        "message": "Customer registered successfully"
    }

@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [{"id": c.id, "name": c.name, "email": c.email} for c in customers]
