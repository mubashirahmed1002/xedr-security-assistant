import os
import pickle
import numpy as np
import psutil
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from database import get_session, ProcessEvent, Alert

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
MODEL_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")
SCALER_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scaler.pkl")
MIN_SAMPLES    = 50       # minimum events needed before training
CONTAMINATION  = 0.05     # expect 5% anomalies in training data
ANOMALY_SCORE_THRESHOLD = -0.1   # below this = anomaly

model  = None
scaler = None

# ─────────────────────────────────────────
#  FEATURE EXTRACTION
# ─────────────────────────────────────────

def extract_features_from_db():
    """Pull process events from DB and convert to feature matrix."""
    session = get_session()
    events  = session.query(ProcessEvent).order_by(
                  ProcessEvent.timestamp.desc()
              ).limit(500).all()
    session.close()

    if len(events) < MIN_SAMPLES:
        print(f"[ML] Not enough data yet — {len(events)}/{MIN_SAMPLES} samples")
        return None

    features = []
    for e in events:
        features.append([
            e.cpu_percent  or 0.0,
            e.memory_mb    or 0.0,
            1 if (e.exe_path and "Temp" in e.exe_path)    else 0,
            1 if (e.exe_path and "AppData" in e.exe_path) else 0,
            1 if (e.exe_path and "System32" in e.exe_path)else 0,
            e.parent_pid   or 0,
        ])

    return np.array(features)


def extract_live_features():
    """Extract features from currently running processes."""
    features  = []
    meta      = []   # store process info for alert messages

    for proc in psutil.process_iter(['pid','name','cpu_percent',
                                     'memory_info','exe','ppid']):
        try:
            info = proc.info
            exe  = info['exe'] or ""
            mem  = info['memory_info'].rss / 1024 / 1024 if info['memory_info'] else 0.0

            features.append([
                info['cpu_percent'] or 0.0,
                mem,
                1 if "Temp"    in exe else 0,
                1 if "AppData" in exe else 0,
                1 if "System32"in exe else 0,
                info['ppid']   or 0,
            ])
            meta.append({
                "pid":  info['pid'],
                "name": info['name'] or "unknown",
                "exe":  exe,
                "cpu":  info['cpu_percent'] or 0.0,
                "mem":  round(mem, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return np.array(features) if features else None, meta

# ─────────────────────────────────────────
#  TRAIN
# ─────────────────────────────────────────

def train_model():
    """Train Isolation Forest on historical process data."""
    global model, scaler

    print("[ML] Starting model training...")
    X = extract_features_from_db()

    if X is None:
        return False

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators  = 100,
        contamination = CONTAMINATION,
        random_state  = 42,
        n_jobs        = -1,
    )
    model.fit(X_scaled)

    # save to disk so we don't retrain every restart
    with open(MODEL_PATH,  "wb") as f: pickle.dump(model,  f)
    with open(SCALER_PATH, "wb") as f: pickle.dump(scaler, f)

    print(f"[ML] Model trained on {len(X)} samples — saved to disk")
    return True


def load_model():
    """Load existing model from disk if available."""
    global model, scaler

    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        with open(MODEL_PATH,  "rb") as f: model  = pickle.load(f)
        with open(SCALER_PATH, "rb") as f: scaler = pickle.load(f)
        print("[ML] Loaded existing model from disk")
        return True
    return False

# ─────────────────────────────────────────
#  DETECT
# ─────────────────────────────────────────

def detect_anomalies():
    """Score live processes and flag anomalies."""
    global model, scaler

    if model is None or scaler is None:
        return 0

    X_live, meta = extract_live_features()

    if X_live is None or len(X_live) == 0:
        return 0

    X_scaled = scaler.transform(X_live)
    scores   = model.decision_function(X_scaled)   # negative = more anomalous
    preds    = model.predict(X_scaled)              # -1 = anomaly, 1 = normal

    alert_count = 0
    session     = get_session()

    for i, (score, pred) in enumerate(zip(scores, preds)):
        if pred == -1 and score < ANOMALY_SCORE_THRESHOLD:
            proc = meta[i]

            # skip very common safe names
            safe = {
                # Windows core
                "System Idle Process","System","Registry","smss.exe",
                "csrss.exe","wininit.exe","services.exe","lsass.exe",
                "svchost.exe","dwm.exe","explorer.exe","winlogon.exe",
                "fontdrvhost.exe","sihost.exe","taskhostw.exe",
                "RuntimeBroker.exe","ShellExperienceHost.exe",
                "StartMenuExperienceHost.exe","SearchHost.exe",
                "SearchIndexer.exe","dllhost.exe","conhost.exe",
                "WmiPrvSE.exe","spoolsv.exe","TextInputHost.exe",
                "ApplicationFrameHost.exe","ctfmon.exe",
                # Microsoft apps
                "OneDrive.exe","OneDrive.Sync.Service.exe",
                "MsMpEng.exe","NisSrv.exe","SecurityHealthService.exe",
                "SgrmBroker.exe","AggregatorHost.exe",
                # Dev tools
                "python.exe","python3.exe","Code.exe","node.exe",
                "git.exe","cmd.exe","powershell.exe","uvicorn.exe",
                # Browsers
                "chrome.exe","msedge.exe","firefox.exe","brave.exe",
}
            if proc['name'] in safe:
                continue

            risk = min(int(abs(score) * 200), 95)   # scale score to 0-95

            alert = Alert(
                alert_type  = "ML Anomaly Detected",
                severity    = "High" if risk > 70 else "Medium",
                risk_score  = risk,
                process     = proc['name'],
                description = (f"Isolation Forest flagged '{proc['name']}' "
                               f"(PID {proc['pid']}) as anomalous. "
                               f"Anomaly score: {score:.4f}. "
                               f"CPU: {proc['cpu']}% | RAM: {proc['mem']}MB | "
                               f"EXE: {proc['exe']}"),
                evidence    = str(proc),
            )
            session.add(alert)
            alert_count += 1

            sev_colour = "\033[91m" if risk > 70 else "\033[93m"
            reset      = "\033[0m"
            print(f"\n{sev_colour}[ML ALERT] Anomaly — {proc['name']} "
                  f"| Score: {score:.4f} | Risk: {risk}/100{reset}")

    session.commit()
    session.close()
    return alert_count

# ─────────────────────────────────────────
#  INIT — called once at startup
# ─────────────────────────────────────────

def init_ml():
    """Load existing model or train a new one."""
    if not load_model():
        print("[ML] No saved model found — will train after collecting data...")

def maybe_retrain(scan_num):
    """Retrain every 20 scans to keep model fresh."""
    global model
    if scan_num % 20 == 0:
        print("[ML] Retraining model with latest data...")
        train_model()
    elif model is None:
        train_model()