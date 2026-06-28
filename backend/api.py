import os
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import init_db, get_session, Alert, ProcessEvent, NetworkEvent
from fastapi.responses import FileResponse
import os

app = FastAPI(title="XEDR Security Assistant API", version="1.0.0")

# allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

init_db()

# ─────────────────────────────────────────
#  WEBSOCKET MANAGER
# ─────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        print(f"[WS] Client connected — {len(self.active)} active")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        print(f"[WS] Client disconnected — {len(self.active)} active")

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

# ─────────────────────────────────────────
#  PYDANTIC MODELS
# ─────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

# ─────────────────────────────────────────
#  REST ENDPOINTS
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "XEDR API running", "version": "1.0.0"}


@app.get("/api/alerts")
def get_alerts(limit: int = 50, severity: Optional[str] = None):
    """Get recent alerts — optionally filtered by severity."""
    session = get_session()
    query   = session.query(Alert).order_by(Alert.timestamp.desc())
    if severity:
        query = query.filter(Alert.severity == severity)
    alerts = query.limit(limit).all()
    session.close()

    return [{
        "id":          a.id,
        "timestamp":   a.timestamp.isoformat(),
        "alert_type":  a.alert_type,
        "severity":    a.severity,
        "risk_score":  a.risk_score,
        "process":     a.process,
        "description": a.description,
        "evidence":    a.evidence,
        "explained":   a.explained,
    } for a in alerts]


@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: int):
    """Get a single alert by ID."""
    session = get_session()
    alert   = session.query(Alert).filter(Alert.id == alert_id).first()
    session.close()

    if not alert:
        return {"error": "Alert not found"}

    return {
        "id":          alert.id,
        "timestamp":   alert.timestamp.isoformat(),
        "alert_type":  alert.alert_type,
        "severity":    alert.severity,
        "risk_score":  alert.risk_score,
        "process":     alert.process,
        "description": alert.description,
        "evidence":    alert.evidence,
        "explained":   alert.explained,
    }


@app.get("/api/alerts/{alert_id}/explain")
def explain_alert_endpoint(alert_id: int):
    """Generate AI explanation for a specific alert."""
    from ai_engine import explain_alert
    session = get_session()
    alert   = session.query(Alert).filter(Alert.id == alert_id).first()
    session.close()

    if not alert:
        return {"error": "Alert not found"}

    explanation = explain_alert(alert)
    return {"alert_id": alert_id, "explanation": explanation}


@app.get("/api/stats")
def get_stats():
    """Dashboard summary stats."""
    session  = get_session()
    now      = datetime.utcnow()
    last_24h = now - timedelta(hours=24)

    total      = session.query(Alert).count()
    today      = session.query(Alert).filter(Alert.timestamp >= last_24h).count()
    critical   = session.query(Alert).filter(Alert.severity == "Critical").count()
    high       = session.query(Alert).filter(Alert.severity == "High").count()
    processes  = session.query(ProcessEvent).count()
    session.close()

    return {
        "total_alerts":    total,
        "alerts_24h":      today,
        "critical_alerts": critical,
        "high_alerts":     high,
        "total_processes": processes,
        "status":          "monitoring",
        "last_updated":    now.isoformat(),
    }


@app.get("/api/timeline")
def get_timeline():
    """Alert counts grouped by hour for the threat timeline chart."""
    session = get_session()
    alerts  = (session.query(Alert)
                      .filter(Alert.timestamp >= datetime.utcnow() - timedelta(hours=24))
                      .order_by(Alert.timestamp.asc())
                      .all())
    session.close()

    # group by hour
    buckets = {}
    for a in alerts:
        hour = a.timestamp.strftime("%H:00")
        if hour not in buckets:
            buckets[hour] = {"hour": hour, "total": 0,
                             "critical": 0, "high": 0, "medium": 0, "low": 0}
        buckets[hour]["total"] += 1
        buckets[hour][a.severity.lower()] = \
            buckets[hour].get(a.severity.lower(), 0) + 1

    return list(buckets.values())


@app.get("/api/processes")
def get_processes(limit: int = 20):
    """Get recent process events."""
    session   = get_session()
    processes = (session.query(ProcessEvent)
                        .order_by(ProcessEvent.timestamp.desc())
                        .limit(limit)
                        .all())
    session.close()

    return [{
        "id":          p.id,
        "timestamp":   p.timestamp.isoformat(),
        "pid":         p.pid,
        "name":        p.name,
        "cpu_percent": p.cpu_percent,
        "memory_mb":   p.memory_mb,
        "status":      p.status,
        "username":    p.username,
        "exe_path":    p.exe_path,
    } for p in processes]


@app.get("/api/network")
def get_network(limit: int = 20):
    """Get recent network events."""
    session  = get_session()
    networks = (session.query(NetworkEvent)
                       .order_by(NetworkEvent.timestamp.desc())
                       .limit(limit)
                       .all())
    session.close()

    return [{
        "id":           n.id,
        "timestamp":    n.timestamp.isoformat(),
        "pid":          n.pid,
        "process_name": n.process_name,
        "local_addr":   n.local_addr,
        "local_port":   n.local_port,
        "remote_addr":  n.remote_addr,
        "remote_port":  n.remote_port,
        "status":       n.status,
    } for n in networks]


@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    """Chat with the AI security assistant."""
    from ai_engine import chat
    reply, updated_history = chat(request.message, request.history)
    return {
        "reply":   reply,
        "history": updated_history,
    }


# ─────────────────────────────────────────
#  WEBSOCKET — live alert feed
# ─────────────────────────────────────────

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Stream new alerts to the frontend in real time."""
    await manager.connect(websocket)
    last_id = 0

    try:
        while True:
            session   = get_session()
            new_alerts = (session.query(Alert)
                                 .filter(Alert.id > last_id)
                                 .order_by(Alert.id.asc())
                                 .all())
            session.close()

            for alert in new_alerts:
                last_id = alert.id
                await manager.broadcast({
                    "type":       "new_alert",
                    "id":         alert.id,
                    "timestamp":  alert.timestamp.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity":   alert.severity,
                    "risk_score": alert.risk_score,
                    "process":    alert.process,
                    "description":alert.description,
                })

            await asyncio.sleep(3)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
@app.post("/api/report")
def generate_report_endpoint(hours: int = 24):
    """Generate and return a PDF incident report."""
    from report_generator import generate_report
    filepath = generate_report(hours=hours)
    return FileResponse(
        filepath,
        media_type   = "application/pdf",
        filename     = os.path.basename(filepath),
    )

@app.get("/api/reports")
def list_reports():
    """List all generated reports."""
    reports_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "reports")
    if not os.path.exists(reports_dir):
        return []
    files = sorted(os.listdir(reports_dir), reverse=True)
    return [{"filename": f, "size_kb": round(
        os.path.getsize(os.path.join(reports_dir, f)) / 1024, 1
    )} for f in files if f.endswith(".pdf")]


# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)