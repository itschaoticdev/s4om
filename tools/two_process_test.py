# -*- coding: utf-8 -*-
"""Two-process loopback test: real host and real client in separate interpreters.

The older virtual_test_* suites run host and client inside one process, so both
sides share network.py's module globals (_my_player_id, _hmac_keys, ...). This
test runs each side in its own process, like two real PCs, over 127.0.0.1.

Usage:  python tools/two_process_test.py
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
PORT = 19777
ROLES = ("host", "client", "client2")
RUN_SECONDS = 8.0


def _install_game_stubs():
    class _Commands:
        CommandType = type('CT', (), {'Live': 1, 'Cheat': 2})

        def Command(self, name, command_type=None):
            def deco(fn):
                return fn
            return deco

        def CheatOutput(self, conn):
            return lambda msg: None

    class _Sims4:
        commands = _Commands()

    sys.modules['sims4'] = _Sims4()
    sys.modules['sims4.commands'] = _Sims4.commands
    sys.modules['services'] = type('services', (), {})
    sys.modules['sims4'].services = sys.modules['services']
    sys.modules['autonomy'] = type('autonomy', (), {})
    sys.modules['autonomy.settings'] = type('settings', (), {})
    sys.modules['sims4.resources'] = type('resources', (), {})


def run_peer(role):
    _install_game_stubs()
    sys.path.insert(0, SRC)
    import threading
    from multimod import network, lobby

    log = []
    network._log = lambda msg: log.append(str(msg))
    network._notify = lambda msg: log.append("NOTIFY " + str(msg))
    network._ensure_alarm = lambda: None
    network._load_launcher_config = lambda: {"name": role, "password": ""}
    network.ALLOW_SELF = True

    if role == "host":
        network._is_host = True
        network._my_player_id = 0
        threading.Thread(target=network._server_thread, args=(PORT,), daemon=True).start()
    else:
        time.sleep(1.0 if role == "client" else 1.5)  # let the host bind first
        network._is_host = False
        threading.Thread(target=network._client_thread, args=("127.0.0.1", PORT), daemon=True).start()

    said = False
    ever_connected = False
    deadline = time.time() + RUN_SECONDS
    while time.time() < deadline:
        try:
            network._process_incoming()
        except Exception as e:
            log.append("process_incoming error: {!r}".format(e))
        connected = (len(network._clients) > 0) if role == "host" else (network._client_socket is not None)
        ever_connected = ever_connected or connected
        if connected and not said and time.time() > deadline - RUN_SECONDS + 3.0:
            try:
                network.mp_say("hello from " + role)
                said = True
            except Exception as e:
                log.append("mp_say error: {!r}".format(e))
        time.sleep(0.05)

    others = [r for r in ROLES if r != role]
    texts = [c.get("text") for c in lobby._chat_history]
    # client-originated chat must arrive labelled with the sender's real name
    by_text = {c.get("text"): c.get("from") for c in lobby._chat_history}
    bad_names = [(t, by_text.get(t)) for t in ("hello from " + o for o in others if o != "host")
                 if t in by_text and by_text.get(t) != t[len("hello from "):]]
    result = {
        "role": role,
        "connected": ever_connected,
        "my_player_id": network._my_player_id,
        "said": said,
        "got_peer_chat": all(("hello from " + o) in texts for o in others),
        "bad_names": bad_names,
        "chat": texts[-5:],
        "rtt_ms": network.get_rtt_ms(),
        "preauth_drops": [l for l in log if "pre-auth" in l],
        "log_tail": log[-15:],
    }
    print("RESULT " + json.dumps(result, ensure_ascii=False))


def main():
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    procs = {r: subprocess.Popen([sys.executable, __file__, r], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, env=env)
             for r in ROLES}
    results = {}
    for role, p in procs.items():
        out, _ = p.communicate(timeout=RUN_SECONDS + 15)
        text = out.decode("utf-8", "replace")
        line = [l for l in text.splitlines() if l.startswith("RESULT ")]
        if not line:
            print("[{}] no result; output:\n{}".format(role, text))
            results[role] = None
            continue
        results[role] = json.loads(line[-1][len("RESULT "):])

    ok = True
    for role in ROLES:
        r = results.get(role)
        if r is None:
            ok = False
            continue
        passed = r["connected"] and r["said"] and r["got_peer_chat"] and not r["preauth_drops"] and not r["bad_names"]
        ok = ok and passed
        print("{:6} {}  connected={} pid={} said={} got_peer_chat={} preauth_drops={} rtt={}".format(
            role, "PASS" if passed else "FAIL", r["connected"], r["my_player_id"],
            r["said"], r["got_peer_chat"], len(r["preauth_drops"]), r["rtt_ms"]))
        if not passed:
            print("  chat:", r["chat"], "bad_names:", r["bad_names"])
            for l in r["log_tail"]:
                print("  log:", l)
    print("OVERALL", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_peer(sys.argv[1])
    else:
        sys.exit(main())
