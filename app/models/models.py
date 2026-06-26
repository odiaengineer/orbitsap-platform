from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    agents = relationship("Agent", back_populates="customer")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    name = Column(String, nullable=False)
    sap_sid = Column(String, nullable=False)
    status = Column(String, default="offline")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship("Customer", back_populates="agents")
    runs = relationship("RefreshRun", back_populates="agent")

class RefreshRun(Base):
    __tablename__ = "refresh_runs"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    status = Column(String, default="pending")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    agent = relationship("Agent", back_populates="runs")
    steps = relationship("RefreshStep", back_populates="run")

class RefreshStep(Base):
    __tablename__ = "refresh_steps"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("refresh_runs.id"))
    step_name = Column(String, nullable=False)
    status = Column(String, default="pending")
    message = Column(String, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)
    run = relationship("RefreshRun", back_populates="steps")
