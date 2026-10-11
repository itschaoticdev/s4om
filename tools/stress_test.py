# -*- coding: utf-8 -*-
"""12-player stress test through a real relay.

Every player is its own process (like 12 PCs). For DURATION seconds each one sends a chat
message every INTERVAL seconds. Passes only if:
  - all 12 stay connected the whole time (no disconnect / relay host error in their logs)
  - every player receives every other player's messages (exact counts, in order per sender)
  - nothing is dropped as pre-auth, nothing errors in message processing
  - a 13th player trying to join mid-test is refused with ERR ROOM_FULL
Run:  python tools/stress_test.py   (env S4OM_STRESS_SECONDS, S4OM_STRESS_INTERVAL)
"""
import json
import os
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import two_process_test as t  # noqa: E402  (game stubs, paths)

PLAYERS = 12
DURATION = float(os.environ.get("S4OM_STRESS_SECONDS", "75"))
INTERVAL = float(os.environ.get("S4OM_STRESS_INTERVAL", "2"))
RELAY_PORT, STATUS_PORT = 18656, 18657
CHAOS = os.environ.get("S4OM_STRESS_CHAOS") == "1"
CHAOS_AT, CHAOS_DOWN, RECOVER = 0.33, 3.0, 25.0   # kill at 1/3, down 3s, allow 25s to reconnect
ROOM = "STRESS"
ROLES = ["host"] + ["p%02d" % i for i in range(1, PLAYERS)]


def run_peer(role):
    t._install_game_stubs()
    sys.path.insert(0, t.SRC)
    import threading
    from multimod import network, lobby

    log, got = [], {}
    network._log = lambda m: log.append((time.time(), str(m)))
    network._notify = lambda m: None
    network._ensure_alarm = lambda: None
    cfg = {"name": role, "password": "", "relay": "127.0.0.1:%d" % RELAY_PORT}
    network._load_launcher_config = lambda: cfg

    orig_add = lobby.add_chat

    def counting_add(sender, text):
        parts = str(text).split()
        if len(parts) == 3 and parts[0] == "msg":
            got.setdefault(parts[1], []).append(int(parts[2]))
        return orig_add(sender, text)
    lobby.add_chat = counting_add

    if role == "host":
        network._is_host = True
        network._my_player_id = 0
        lobby.ROOM_CODE = ROOM
        network._start_relay_host()
        time.sleep(2.0)
    else:
        time.sleep(2.5)
        network._is_host = False
        ok, desc = network._join_via_relay(ROOM)
        assert ok, desc

    start = time.time() + 4.0         # give everyone time to connect first
    sent = 0
    next_send = start
    end = start + DURATION
    proc_errors = 0
    while time.time() < end + 6.0:    # keep draining after the last send
        try:
            network._process_incoming()
        except Exception as e:
            proc_errors += 1
            log.append((time.time(), "process_incoming error: {!r}".format(e)))
        now = time.time()
        if now >= next_send and now < end:
            network.mp_say("msg {} {}".format(role, sent))
            sent += 1
            next_send += INTERVAL
        time.sleep(0.03)

    # only problems while the session was running count - at the very end the host exits a
    # moment before the others, which they correctly see as a disconnect
    bad = [l for ts, l in log if ts < end + 2.0 and ("pre-auth" in l or "relay host error" in l or "disconnected" in l
           or "recv error" in l or "HMAC mismatch" in l or "CRC mismatch" in l)]
    if CHAOS:   # outages are expected - judge on what happened after recovery
        bad = [l for ts, l in log if ts < end + 2.0 and ("pre-auth" in l or "HMAC mismatch" in l or "CRC mismatch" in l)]
    print("RESULT " + json.dumps({"role": role, "sent": sent, "got": got, "bad": bad[:10], "t0": start,
                                  "proc_errors": proc_errors,
                                  "connected": len(network._clients) if role == "host" else network._client_socket is not None}))


def join_13th():
    s = socket.create_connection(("127.0.0.1", RELAY_PORT), timeout=10)
    s.sendall(("S4OM JOIN %s -\n" % ROOM).encode())
    b = b""
    while not b.endswith(b"\n"):
        c = s.recv(1)
        if not c:
            break
        b += c
    s.close()
    return b.decode().strip()


def main():
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    def start_relay():
        r = subprocess.Popen([sys.executable, t.RELAY_PY, "--open", "--port", str(RELAY_PORT), "--status-port",
                              str(STATUS_PORT), "--bind", "127.0.0.1", "--log", os.devnull],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        while r.stdout.readline().strip() != b"READY":
            pass
        return r
    relay = start_relay()
    try:
        procs = {r: subprocess.Popen([sys.executable, __file__, r], stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, env=env) for r in ROLES}
        if CHAOS:
            time.sleep(4.0 + DURATION * CHAOS_AT)
            relay.kill(); relay.wait()
            killed_at = time.time()
            print("relay KILLED at t+{:.0f}s".format(DURATION * CHAOS_AT))
            time.sleep(CHAOS_DOWN)
            relay = start_relay()
            print("relay back after {:.0f}s".format(time.time() - killed_at))
            time.sleep(max(1.0, DURATION * 0.5 - DURATION * CHAOS_AT))
        else:
            time.sleep(4.0 + DURATION / 2)
        thirteenth = join_13th()
        import urllib.request
        mid = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/" % STATUS_PORT, timeout=5).read())
        results = {}
        for r, p in procs.items():
            out = p.communicate(timeout=DURATION + 60)[0].decode("utf-8", "replace")
            line = [l for l in out.splitlines() if l.startswith("RESULT ")]
            results[r] = json.loads(line[-1][7:]) if line else {"error": out[-800:]}
    finally:
        relay.kill()

    ok = True
    sent = {r: results[r].get("sent", 0) for r in ROLES}
    for r in ROLES:
        res = results[r]
        if "error" in res:
            print(r, "CRASHED", res["error"])
            ok = False
            continue
        problems = []
        for other in ROLES:
            if other == r:
                continue
            want = list(range(sent[other]))
            have = res["got"].get(other, [])
            if CHAOS:   # messages sent after the outage + reconnect window must ALL arrive
                first_ok = int((DURATION * CHAOS_AT + CHAOS_DOWN + RECOVER) / INTERVAL) + 1
                want = [n for n in want if n >= first_ok]
                have = [n for n in have if n >= first_ok]
            if have != want:
                missing = len(set(want) - set(have))
                problems.append("{}: got {}/{}{}".format(other, len(have), len(want),
                                                         " (out of order)" if not missing and have != want else ""))
        if res["bad"] or res["proc_errors"]:
            problems.append("log: {}".format(res["bad"][:3] or res["proc_errors"]))
        status = "PASS" if not problems else "FAIL"
        ok = ok and not problems
        received = sum(len(v) for v in res["got"].values())
        print("{:5} {}  sent {:3}  received {:4}  {}".format(r, status, res["sent"], received, "; ".join(problems)[:200]))
    total = sum(sent.values())
    print("messages sent: {}, deliveries checked: {}".format(total, total * (PLAYERS - 1)))
    print("relay mid-test: {} rooms, {} players".format(mid["rooms"], mid["players"]))
    full_ok = thirteenth == "ERR ROOM_FULL" and mid["players"] == PLAYERS
    print("13th player mid-test ->", thirteenth, "PASS" if full_ok else "FAIL")
    ok = ok and full_ok
    print("STRESS", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_peer(sys.argv[1])
    else:
        sys.exit(main())
