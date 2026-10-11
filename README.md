# S4OM - online multiplayer for The Sims 4

S4OM is a script mod that lets several players share one household in The Sims 4,
each controlling their own Sim, live. Website: https://s4om.gg - Discord: https://discord.gg/XgJe2T5MBc

> **Status:** in testing, not released. Not affiliated with or endorsed by Electronic Arts or Maxis.

## What syncs

Game clock and speed, Sim positions, chat, household money, moods and needs,
relationships, inventory, skills and stats, buy-mode purchases, group travel.

## How it connects

- **LAN / direct IP (free):** the host listens on TCP 7655 and friends connect to it.
- **Online:** host and friends both connect out to the S4OM relay and meet by room
  code, so nobody needs to forward ports. The relay only pipes bytes; the game
  protocol is unchanged. Online access needs an S4OM membership token.

In-game cheat-console commands:

| Command | Does |
|---|---|
| `mp_host` | Host a room (also opens it on the relay when one is configured) |
| `mp_join <ip>` | Join a host on your network |
| `mp_join_code <CODE>` | Join an online room by code |
| `mp_say <text>` | Chat |
| `mp_status` | Connection status |

The S4OM Launcher writes `Documents\Electronic Arts\The Sims 4\Mods\mp_launcher_config.json`,
which the mod reads on load (`mode`, `name`, `relay`, `relay_token`, `room_code`, `host`, `port`).

## Build

Requires **Python 3.7** - The Sims 4 runs 3.7 and the `.pyc` magic number must match.

```
"C:\Program Files\Python37\python.exe" build.py            # -> build/S4OM.ts4script
"C:\Program Files\Python37\python.exe" build.py --deploy   # also copy into your Mods folder
```

## Tests

```
set PYTHONUTF8=1
"C:\Program Files\Python37\python.exe" tools\two_process_test.py lan     # host + 2 clients, real TCP
"C:\Program Files\Python37\python.exe" tools\two_process_test.py relay   # same, through a local relay
```

`tools/run_all_virtual_tests.py` runs the original SimSync suites.

## Credits and licence

S4OM is a fork of **SimSync / Sims4Multiplayer** by sora and k
(https://github.com/mo9652962-ai/sims4-multiplayer-dev). The original README is in
[README.zh-CN.md](README.zh-CN.md). Licensed under the **GNU GPL v3.0** - see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).

Fixes made in this fork include: a handshake race that dropped the host's initial world
state, client chat not reaching other clients in rooms of 3+, chat sender names,
launcher-started hosts never becoming host, and reconnects that silently broke the
session key.

The Sims is a trademark of Electronic Arts Inc.
