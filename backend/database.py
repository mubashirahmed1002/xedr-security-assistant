import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

# --- TABLES ---

class ProcessEvent(Base):
    __tablename__ = "process_events"
    id          = Column(Integer, primary_key=True)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    pid         = Column(Integer)
    name        = Column(String)
    cpu_percent = Column(Float)
    memory_mb   = Column(Float)
    status      = Column(String)
    username    = Column(String)
    exe_path    = Column(String)
    parent_pid  = Column(Integer)

class NetworkEvent(Base):
    __tablename__ = "network_events"
    id           = Column(Integer, primary_key=True)
    timestamp    = Column(DateTime, default=datetime.utcnow)
    pid          = Column(Integer)
    process_name = Column(String)
    local_addr   = Column(String)
    local_port   = Column(Integer)
    remote_addr  = Column(String)
    remote_port  = Column(Integer)
    status       = Column(String)

class FileEvent(Base):
    __tablename__ = "file_events"
    id         = Column(Integer, primary_key=True)
    timestamp  = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)
    file_path  = Column(String)
    directory  = Column(String)

class Alert(Base):
    __tablename__ = "alerts"
    id          = Column(Integer, primary_key=True)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    alert_type  = Column(String)
    severity    = Column(String)
    risk_score  = Column(Integer)
    process     = Column(String)
    description = Column(Text)
    evidence    = Column(Text)
    explained   = Column(Text)

# --- ENGINE SETUP ---

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "security.db")

engine = None
SessionLocal = None

def init_db():
    global engine, SessionLocal
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    print(f"[DB] Database ready at {DB_PATH}")

def get_session():
    return SessionLocal()