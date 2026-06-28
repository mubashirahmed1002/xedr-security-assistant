import platform
from datetime import datetime

def notify(title: str, message: str, severity: str = "High"):
    """Send a desktop notification for critical alerts."""
    try:
        from plyer import notification
        notification.notify(
            title       = f"🔴 XEDR — {title}",
            message     = message[:200],
            app_name    = "XEDR Security",
            timeout     = 8,
        )
    except Exception:
        # fallback — print to terminal with colour
        colours = {
            "Critical": "\033[95m",
            "High":     "\033[91m",
            "Medium":   "\033[93m",
        }
        c     = colours.get(severity, "\033[91m")
        reset = "\033[0m"
        now   = datetime.now().strftime("%H:%M:%S")
        print(f"\n{c}🔔 [{now}] NOTIFICATION: {title}{reset}")
        print(f"   {message}\n")
        