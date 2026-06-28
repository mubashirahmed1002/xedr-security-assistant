import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from database import get_session, FileEvent

# Folders to monitor — add more if needed
WATCH_DIRS = [
    os.path.expanduser("~\\AppData\\Roaming"),   # Windows
    os.path.expanduser("~\\Desktop"),
]

class SecurityFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self._save("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._save("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._save("deleted", event.src_path)

    def _save(self, event_type, path):
        try:
            session = get_session()
            event = FileEvent(
                event_type = event_type,
                file_path  = path,
                directory  = os.path.dirname(path),
            )
            session.add(event)
            session.commit()
            session.close()
            print(f"[FILE] {event_type.upper()} → {path}")
        except Exception as e:
            print(f"[FILE] Error saving event: {e}")

def start_file_watcher():
    observer = Observer()
    handler  = SecurityFileHandler()

    for directory in WATCH_DIRS:
        if os.path.exists(directory):
            observer.schedule(handler, directory, recursive=True)
            print(f"[FILE] Watching: {directory}")

    observer.start()
    print("[FILE] File watcher running...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[FILE] File watcher stopped.")

    observer.join()

if __name__ == "__main__":
    from database import init_db
    init_db()
    start_file_watcher()