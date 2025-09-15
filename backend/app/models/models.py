from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BrowserSession(Base):
    __tablename__ = 'browser_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    storage_path = Column(String(512))
    status = Column(String(50), default='ready')
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User')

class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    owner_id = Column(Integer, ForeignKey('users.id'))
    definition = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String(255), primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'))
    status = Column(String(50), default='queued')
    result = Column(JSON)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

class ProductSnapshot(Base):
    __tablename__ = 'product_snapshots'
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'))
    url = Column(String(1024))
    title = Column(String(512))
    price = Column(String(64))
    currency = Column(String(16))
    screenshot = Column(String(1024))
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Proxy(Base):
    __tablename__ = 'proxies'
    id = Column(Integer, primary_key=True)
    server = Column(String(512))
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    last_checked = Column(DateTime)
    healthy = Column(Boolean, default=True)
