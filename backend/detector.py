import psutil
from datetime import datetime, timedelta
from database import get_session, Alert, ProcessEvent, NetworkEvent

# ─────────────────────────────────────────
#  THRESHOLDS  (tune these as needed)
# ─────────────────────────────────────────
HIGH_CPU_PERCENT      = 80.0   # CPU% to flag a process
HIGH_CPU_DURATION_S   = 30     # seconds it must stay high
MAX_CONNECTIONS       = 15     # outbound connections per process
SCAN_WINDOW_S         = 10     # time window for port-scan detection
SUSPICIOUS_PORTS      = {4444, 1337, 31337, 8888, 9999}   # common backdoor ports
SUSPICIOUS_DIRS       = [
    "\\AppData\\Local\\Temp\\",
    "\\AppData\\Roaming\\",
    "C:\\Windows\\Temp\\",
]
KNOWN_SAFE_PROCESSES = {
    # Windows system
    "svchost.exe", "explorer.exe", "csrss.exe",
    "lsass.exe", "winlogon.exe", "System",
    "System Idle Process", "Registry", "smss.exe",
    "wininit.exe", "services.exe", "dwm.exe",
    "taskhostw.exe", "spoolsv.exe", "sihost.exe",
    "fontdrvhost.exe", "dllhost.exe", "conhost.exe",
    "SearchIndexer.exe", "WmiPrvSE.exe", "RuntimeBroker.exe",
    # Dev tools
    "python.exe", "python3.exe", "Code.exe", "node.exe",
    "git.exe", "cmd.exe", "powershell.exe",
    # Browsers
    "chrome.exe", "msedge.exe", "firefox.exe",
    # Antivirus / system tools
    "MsMpEng.exe", "NisSrv.exe", "SecurityHealthService.exe",
}

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def save_alert(alert_type, severity, risk_score, process, description, evidence):
    """Save an alert to the database and print it."""
    session = get_session()
    alert = Alert(
        alert_type  = alert_type,
        severity    = severity,
        risk_score  = risk_score,
        process     = process,
        description = description,
        evidence    = str(evidence),
    )
    session.add(alert)
    session.commit()
    session.close()

    # colour-coded terminal output
    colours = {
        "Low":      "\033[94m",   # blue
        "Medium":   "\033[93m",   # yellow
        "High":     "\033[91m",   # red
        "Critical": "\033[95m",   # magenta
    }
    reset = "\033[0m"
    c     = colours.get(severity, "")
    now   = datetime.now().strftime("%H:%M:%S")
    print(f"\n{c}[ALERT][{now}] {severity} | {alert_type}{reset}")
    print(f"  Process : {process}")
    print(f"  Risk    : {risk_score}/100")
    print(f"  Details : {description}\n")


# ─────────────────────────────────────────
#  DETECTION RULES
# ─────────────────────────────────────────

def check_high_cpu():
    """Flag processes with sustained high CPU usage."""
    flagged = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'exe']):
        try:
            info = proc.info
            if info['name'] in KNOWN_SAFE_PROCESSES:
                continue
            cpu = info['cpu_percent'] or 0.0
            if cpu >= HIGH_CPU_PERCENT:
                flagged.append(info)
                save_alert(
                    alert_type  = "High CPU Usage",
                    severity    = "Medium",
                    risk_score  = min(50 + int(cpu / 2), 90),
                    process     = info['name'],
                    description = f"Process '{info['name']}' (PID {info['pid']}) "
                                  f"is consuming {cpu:.1f}% CPU.",
                    evidence    = {
                        "pid":      info['pid'],
                        "name":     info['name'],
                        "cpu":      cpu,
                        "exe":      info['exe'],
                    },
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return flagged


def check_port_scan():
    """Detect processes opening many outbound connections rapidly."""
    conn_count = {}
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.pid and conn.raddr:
                conn_count[conn.pid] = conn_count.get(conn.pid, 0) + 1
    except psutil.AccessDenied:
        return []

    flagged = []
    for pid, count in conn_count.items():
        if count >= MAX_CONNECTIONS:
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                if name in KNOWN_SAFE_PROCESSES:
                    continue
                flagged.append(pid)
                save_alert(
                    alert_type  = "Port Scan / Excessive Connections",
                    severity    = "High",
                    risk_score  = min(60 + count * 2, 95),
                    process     = name,
                    description = f"Process '{name}' (PID {pid}) has "
                                  f"{count} active outbound connections — "
                                  f"possible port scan or data exfiltration.",
                    evidence    = {"pid": pid, "name": name,
                                   "connection_count": count},
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return flagged


def check_suspicious_ports():
    """Flag connections to known backdoor / C2 ports."""
    flagged = []
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.raddr and conn.raddr.port in SUSPICIOUS_PORTS:
                pid  = conn.pid or 0
                name = "unknown"
                try:
                    name = psutil.Process(pid).name()
                except Exception:
                    pass
                flagged.append(conn)
                save_alert(
                    alert_type  = "Suspicious Port Connection",
                    severity    = "Critical",
                    risk_score  = 95,
                    process     = name,
                    description = f"Connection to suspicious port "
                                  f"{conn.raddr.port} detected from '{name}'. "
                                  f"This port is commonly used by backdoors / C2.",
                    evidence    = {
                        "pid":         pid,
                        "process":     name,
                        "remote_ip":   conn.raddr.ip,
                        "remote_port": conn.raddr.port,
                    },
                )
    except psutil.AccessDenied:
        pass
    return flagged


def check_new_executables():
    """Flag new processes running from suspicious directories."""
    flagged = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
        try:
            info    = proc.info
            exe     = info['exe'] or ""
            name    = info['name'] or "unknown"

            if name in KNOWN_SAFE_PROCESSES:
                continue

            # only check processes started in the last 30 seconds
            age = datetime.now().timestamp() - (info['create_time'] or 0)
            if age > 30:
                continue

            for sus_dir in SUSPICIOUS_DIRS:
                if sus_dir.lower() in exe.lower():
                    flagged.append(info)
                    save_alert(
                        alert_type  = "Suspicious Executable Location",
                        severity    = "High",
                        risk_score  = 80,
                        process     = name,
                        description = f"New process '{name}' started from "
                                      f"suspicious directory: {exe}",
                        evidence    = {
                            "pid": info['pid'],
                            "exe": exe,
                            "age_seconds": round(age, 1),
                        },
                    )
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return flagged


def check_no_parent():
    """Flag processes with no parent — common malware technique."""
    flagged = []
    for proc in psutil.process_iter(['pid', 'name', 'ppid', 'exe']):
        try:
            info = proc.info
            name = info['name'] or "unknown"

            if name in KNOWN_SAFE_PROCESSES or info['pid'] in (0, 4):
                continue

            if info['ppid'] == 0 or info['ppid'] is None:
                flagged.append(info)
                save_alert(
                    alert_type  = "Orphan Process (No Parent)",
                    severity    = "Medium",
                    risk_score  = 60,
                    process     = name,
                    description = f"Process '{name}' (PID {info['pid']}) "
                                  f"has no parent process — unusual behaviour.",
                    evidence    = {
                        "pid":  info['pid'],
                        "name": name,
                        "exe":  info['exe'],
                    },
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return flagged


# ─────────────────────────────────────────
#  MAIN RUN — called from monitor.py
# ─────────────────────────────────────────

def run_all_checks():
    """Run every detection rule and return total alerts found."""
    total = 0
    total += len(check_high_cpu())
    total += len(check_port_scan())
    total += len(check_suspicious_ports())
    total += len(check_new_executables())
    total += len(check_no_parent())
    return total