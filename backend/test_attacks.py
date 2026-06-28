import socket, time, os, threading

print("=" * 50)
print("  XEDR Attack Simulator — Evaluation Tool")
print("=" * 50)

def test_port_scan():
    print("\n[TEST 1] Simulating port scan...")
    for port in range(8000, 8030):
        try:
            s = socket.socket()
            s.setblocking(False)
            s.connect_ex(("127.0.0.1", port))
            s.close()
        except:
            pass
    time.sleep(1)
    print("[TEST 1] Done — watch monitor for Port Scan alert")

def test_high_cpu():
    print("\n[TEST 2] Simulating high CPU spike for 20 seconds...")
    def burn():
        end = time.time() + 20
        while time.time() < end:
            _ = sum(i * i for i in range(10000))
    threads = [threading.Thread(target=burn) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("[TEST 2] Done — watch monitor for High CPU alert")

def test_suspicious_file():
    print("\n[TEST 3] Simulating suspicious file write in Temp...")
    temp = os.path.expanduser(
        "~\\AppData\\Local\\Temp\\xedr_test_payload.exe")
    with open(temp, "w") as f:
        f.write("XEDR test — safe to delete")
    time.sleep(3)
    os.remove(temp)
    print("[TEST 3] Done — watch monitor for Suspicious File alert")

def test_suspicious_port():
    print("\n[TEST 4] Simulating connection to suspicious port 4444...")
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect_ex(("127.0.0.1", 4444))
        s.close()
    except:
        pass
    print("[TEST 4] Done — watch monitor for Suspicious Port alert")

if __name__ == "__main__":
    test_port_scan()
    time.sleep(8)
    test_high_cpu()
    time.sleep(8)
    test_suspicious_file()
    time.sleep(8)
    test_suspicious_port()
    print("\n✅ All 4 tests complete. Check dashboard for alerts.")