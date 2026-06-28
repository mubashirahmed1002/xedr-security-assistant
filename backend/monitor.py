import psutil
import time
import os
import platform
from datetime import datetime
from database import init_db, get_session, ProcessEvent, NetworkEvent

# --- CONFIG ---
SCAN_INTERVAL   = 5
HIGH_CPU_THRESH = 50.0
MAX_CONNECTIONS = 20

print("[MONITOR] Starting Security Monitor Daemon...")
print(f"[MONITOR] Platform: {platform.system()} {platform.release()}")
print(f"[MONITOR] Scan interval: {SCAN_INTERVAL}s")

def collect_processes(session):
    count = 0
    for proc in psutil.process_iter(['pid','name','cpu_percent',
                                     'memory_info','status',
                                     'username','exe','ppid']):
        try:
            info = proc.info
            event = ProcessEvent(
                pid         = info['pid'],
                name        = info['name'] or "unknown",
                cpu_percent = info['cpu_percent'] or 0.0,
                memory_mb   = round(info['memory_info'].rss / 1024 / 1024, 2)
                              if info['memory_info'] else 0.0,
                status      = info['status'] or "unknown",
                username    = info['username'] or "unknown",
                exe_path    = info['exe'] or "unknown",
                parent_pid  = info['ppid'] or 0,
            )
            session.add(event)
            count += 1
        except (psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    session.commit()
    return count

def collect_network(session):
    count = 0
    try:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            try:
                proc_name = "unknown"
                if conn.pid:
                    try:
                        proc_name = psutil.Process(conn.pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                event = NetworkEvent(
                    pid          = conn.pid or 0,
                    process_name = proc_name,
                    local_addr   = conn.laddr.ip if conn.laddr else "",
                    local_port   = conn.laddr.port if conn.laddr else 0,
                    remote_addr  = conn.raddr.ip if conn.raddr else "",
                    remote_port  = conn.raddr.port if conn.raddr else 0,
                    status       = conn.status or "NONE",
                )
                session.add(event)
                count += 1
            except Exception:
                pass
        session.commit()
    except psutil.AccessDenied:
        print("[MONITOR] Network access denied — try running as Administrator")
    return count

def print_summary(proc_count, net_count, scan_num, rule_alerts, ml_alerts):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] Scan #{scan_num} | "
          f"{proc_count} processes | {net_count} connections | "
          f"Rules: {rule_alerts} alert(s) | ML: {ml_alerts} anomaly(s)")

def run():
    init_db()
    from detector  import run_all_checks
    from ml_engine import init_ml, detect_anomalies, maybe_retrain
    from ai_engine import explain_latest_alerts
    from notifier  import notify

    init_ml()
    scan_num = 0
    print("[MONITOR] Daemon running. Press Ctrl+C to stop.\n")

    while True:
        try:
            scan_num += 1
            session = get_session()

            proc_count = collect_processes(session)
            net_count  = collect_network(session)
            session.close()

            rule_alerts = run_all_checks()
            maybe_retrain(scan_num)
            ml_alerts   = detect_anomalies()

            print_summary(proc_count, net_count, scan_num,
                          rule_alerts, ml_alerts)

            # notify on critical/high alerts
            if rule_alerts + ml_alerts > 0:
                session2 = get_session()
                from database import Alert
                recent = (session2.query(Alert)
                                  .order_by(Alert.timestamp.desc())
                                  .limit(1).first())
                session2.close()
                if recent and recent.severity in ("Critical", "High"):
                    notify(
                        title    = recent.alert_type,
                        message  = f"{recent.process} — Risk {recent.risk_score}/100",
                        severity = recent.severity,
                    )

            if scan_num % 3 == 0 and (rule_alerts + ml_alerts) > 0:
                explain_latest_alerts(n=2)

            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            print("\n[MONITOR] Stopped by user.")
            break
        except Exception as e:
            print(f"[MONITOR] Error in scan #{scan_num}: {e}")
            time.sleep(SCAN_INTERVAL)
            
if __name__ == "__main__":
    run()