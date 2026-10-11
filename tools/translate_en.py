# -*- coding: utf-8 -*-
"""One-off: replace the mod's Chinese user-facing strings (notifications, console output,
log lines, mood labels) with English. Docstrings/comments are left alone. Identical source
strings get identical translations everywhere, so anything that compares them stays
consistent. Run from the repo root:  python tools/translate_en.py
"""
import ast
import glob
import io
import os
import re
import tokenize

EN = {
    "      mp_reload_all  重载全部模块": "      mp_reload_all  reload all modules",
    "  [{}] {} 准备={} 进图={} 在线={} {}": "  [{}] {} ready={} in_lot={} online={} {}",
    "(本机)": "(you)",
    "=== 房间状态 ({}人) 房间码: {} ===": "=== Room ({} players) code: {} ===",
    "AI 状态: 已禁用远端 sim = {}": "AI: disabled on remote Sims = {}",
    "MP 主机已开启 :{} 等待连接...": "S4OM: hosting on port {} - waiting for players...",
    "MP 主机模式启动 (端口 {})": "S4OM: host mode started (port {})",
    "MP 交互同步: {}": "S4OM interaction sync: {}",
    "MP 已经在运行": "S4OM is already running",
    "Saves 目录存档 ({}):": "Saves in the Saves folder ({}):",
    "discovered room at {}: {} ({}人) code={}": "discovered room at {}: {} ({} players) code={}",
    "lobby: promoted {} to host (标记)": "lobby: promoted {} to host (flagged)",
    "money sync: 应用资金 {}": "money sync: applied funds {}",
    "mp_buysync: Buy 家具同步已{}": "mp_buysync: buy-mode furniture sync {}",
    "mp_hello v4.2 生效!": "mp_hello v4.2 works!",
    "mp_intsync: 交互同步已{}": "mp_intsync: interaction sync {}",
    "mp_invsync: 背包同步已{}": "mp_invsync: inventory sync {}",
    "mp_relsync: 关系同步已{}": "mp_relsync: relationship sync {}",
    "stats sync: 应用 {} 个需求": "stats sync: applied {} needs",
    "{} 加入了房间": "{} joined the room",
    "{} 成为新房主，正在重连...": "{} is the new host - reconnecting...",
    "{} 掉线了": "{} disconnected",
    "{} 离开了房间": "{} left the room",
    "⏳ 旅行加载中：等待 {} ({}s)": "⏳ Travelling: waiting for {} ({}s)",
    "⚠️ 协议版本不兼容：你的 mod v{} 与房主 v{} 不匹配，请双方更新到同一版本":
        "⚠️ Version mismatch: your S4OM is v{} but the host has v{}. Both of you need the same version (update the launcher).",
    "⚠️ 旅行超时：{} 未到达，已解除锁定": "⚠️ Travel timed out: {} didn't arrive - game unlocked",
    "⚠️ 请手动旅行到房主的新地点（跟随失败已记录日志）": "⚠️ Please travel to the host's new location yourself (auto-follow failed - see the log)",
    "⚠️ 部分成员未到达：{}，已解除锁定": "⚠️ Some players didn't arrive: {} - game unlocked",
    "⚠️ 重载失败: {}": "⚠️ Reload failed: {}",
    "⚠️ 重载错误 {}: {}": "⚠️ Reload error {}: {}",
    "⚡ 精力充沛": "⚡ Energized",
    "⚡ 精力爆棚": "⚡ Very Energized",
    "✅ 全员就绪，请与房主同时旅行！": "✅ Everyone's ready - travel together with the host!",
    "✅ 全员已到达新场景，继续游戏！": "✅ Everyone has arrived - carry on playing!",
    "✅ 全员确认完毕，可以同时旅行了！": "✅ Everyone confirmed - you can travel together now!",
    "✅ 已准备": "✅ Ready",
    "✅ 重载完成": "✅ Reload complete",
    "✅ 重载成功: {}": "✅ Reloaded: {}",
    "✨ 灵感": "✨ Inspired",
    "❌ 重载失败": "❌ Reload failed",
    "主机": "host",
    "位置同步已停止": "Position sync stopped",
    "位置同步已开始 (每 {}s 广播)": "Position sync started (every {}s)",
    "你已被移出房间: {}": "You were removed from the room: {}",
    "先完成存档同步后才能开始游戏!": "Sync the save first, then start the game!",
    "关": "off",
    "关闭": "off",
    "加入模式缺少 host IP": "Join mode needs the host's IP",
    "加入被拒绝: {}": "Join refused: {}",
    "只有房主可以发起旅行同步": "Only the host can start group travel",
    "只有房主可以同步存档": "Only the host can sync the save",
    "只有房主可以开始游戏": "Only the host can start the game",
    "只有房主可以踢人": "Only the host can kick players",
    "只有房主可以转交身份": "Only the host can hand over hosting",
    "只有房主能发起旅行同步!": "Only the host can start group travel!",
    "同步存档失败（成员未全准备）": "Couldn't sync the save (not everyone is ready)",
    "存档不存在: {}": "Save not found: {}",
    "存档写入失败: {}": "Couldn't write the save: {}",
    "存档发送失败: {}": "Couldn't send the save: {}",
    "存档发送完成!": "Save sent!",
    "存档同步: {} | 开始权: {}": "Save sync: {} | can start: {}",
    "存档同步完成! 可以开始游戏": "Save synced! You can start the game",
    "存档同步完成! 所有成员现在可以开始游戏": "Save synced! Everyone can start the game now",
    "存档块缺失，正在请求重传 ({} 块)...": "Parts of the save are missing - asking for them again ({} parts)...",
    "存档块缺失，请房主重新发送": "Parts of the save are missing - ask the host to send it again",
    "存档已同步! 请返回主菜单后重新加载存档 {}": "Save synced! Go back to the main menu and load save {}",
    "存档已接收并写入: {} ({:.1f}KB, 校验✅)": "Save received: {} ({:.1f}KB, verified ✅)",
    "存档接收仍不完整，请房主重新发送": "The save is still incomplete - ask the host to send it again",
    "存档校验失败（可能损坏），请房主重新发送": "The save failed its check (may be damaged) - ask the host to send it again",
    "客机": "guest",
    "对端小人 {}": "remote Sim {}",
    "已关闭 {} 个非活动 sim 的 AI": "Turned off autonomy for {} inactive Sims",
    "已准备!": "Ready!",
    "已发送 {}": "Sent {}",
    "已发送: {}": "Sent: {}",
    "已发送存档同步请求，等待成员确认...": "Save sync requested - waiting for players to confirm...",
    "已取消准备": "No longer ready",
    "已将 {} 移出房间": "Removed {} from the room",
    "已将房主身份转交 {} (需重建房间生效)": "Hosting handed to {} (takes effect when the room restarts)",
    "已广播当前资金": "Sent current household funds",
    "已恢复 {} 个 sim 的 AI": "Restored autonomy for {} Sims",
    "已报告抵达新场景，等待全员...": "Arrival reported - waiting for everyone...",
    "已按配置自动连接 ({})": "Connected automatically from launcher settings ({})",
    "已确认旅行就绪，等待全员...": "Ready to travel - waiting for everyone...",
    "已离开房间": "Left the room",
    "已请求同步存档": "Save sync requested",
    "已踢出": "Kicked",
    "已转交": "Handed over",
    "已连接主机 {}:{}": "Connected to host {}:{}",
    "已重连主机": "Reconnected to the host",
    "开": "on",
    "开启": "on",
    "心情同步: {} | 当前 mood: {}": "Mood sync: {} | current mood: {}",
    "心情同步已关闭": "Mood sync off",
    "心情同步已开启": "Mood sync on",
    "快捷表情: ": "Quick emotes: ",
    "成员": "member",
    "成员 {} 已抵达新场景 ({}/{})": "{} has arrived ({}/{})",
    "成员 {} 已确认旅行就绪 ({}/{})": "{} is ready to travel ({}/{})",
    "我": "Me",
    "我的 sim_id: {} ({})": "My sim_id: {} ({})",
    "房主": "host",
    "房主将你移出房间": "The host removed you from the room",
    "房主已开始游戏!": "The host started the game!",
    "房主掉线，正在竞选新房主...": "The host disconnected - picking a new host...",
    "房主无需确认": "The host doesn't need to confirm",
    "房主要求同步旅行：请输入 mp_travel_ack 确认": "The host wants to travel together: type mp_travel_ack to confirm",
    "房主请求同步存档，正在确认...": "The host is syncing the save - confirming...",
    "房间密码错误": "Wrong room password",
    "房间状态已重置": "Room reset",
    "房间码: {}": "Room code: {}",
    "文件不存在: {}": "File not found: {}",
    "断开连接...": "Disconnecting...",
    "断开连接失败: {}": "Couldn't disconnect: {}",
    "旅行同步已发起，等待成员确认...": "Group travel started - waiting for players to confirm...",
    "旅行同步已发起：请所有成员在 10 秒内确认 (mp_travel_ack)": "Group travel started: everyone confirm within 10 seconds (mp_travel_ack)",
    "旅行自动确认: {}": "Auto-confirm travel: {}",
    "无": "none",
    "无启动器配置 (mp_launcher_config.json)": "No launcher settings found (mp_launcher_config.json)",
    "无法开始（未同步存档或成员未进图）": "Can't start yet (save not synced or players not loaded in)",
    "无（仅房主有）": "none (host only)",
    "时间同步: {} | 角色: {} | 当前速度: {}": "Time sync: {} | role: {} | current speed: {}",
    "时间同步已关闭": "Time sync off",
    "时间同步已开启（主机掌控时间）": "Time sync on (the host controls game speed)",
    "未找到 active sim": "No active Sim found",
    "未测量": "not measured",
    "未知模式: {}": "Unknown mode: {}",
    "未连接! 先 mp_host 或 mp_join": "Not connected! Host or join first (mp_host / mp_join)",
    "未连接房间": "Not in a room",
    "正在发送存档 {} ({:.1f}KB)...": "Sending save {} ({:.1f}KB)...",
    "正在连接 {}:{}": "Connecting to {}:{}",
    "游戏内旅行跟随: {}": "Follow the host when they travel: {}",
    "游戏开始!": "Game started!",
    "玩家": "Player",
    "玩家{}": "Player {}",
    "用法: mp_join <主机IP> [端口]": "Usage: mp_join <host IP> [port]",
    "用法: mp_kick <player_id>（mp_lobby 查看 ID）": "Usage: mp_kick <player_id>  (see IDs with mp_lobby)",
    "用法: mp_promote <player_id>": "Usage: mp_promote <player_id>",
    "用法: mp_reload <模块名>  (如 mp_reload clock_sync)": "Usage: mp_reload <module>  (e.g. mp_reload clock_sync)",
    "用法: mp_say <消息>": "Usage: mp_say <message>",
    "等待成员进入家庭: {}": "Waiting for players to load in: {}",
    "等待所有成员准备就绪后才能同步存档!": "Wait until everyone is ready before syncing the save!",
    "等待所有成员进入家庭后再开始游戏!": "Wait until everyone has loaded in before starting!",
    "读取存档目录失败: {}": "Couldn't read the Saves folder: {}",
    "踢人失败（ID 无效或为房主）": "Couldn't kick (invalid ID, or that's the host)",
    "转交失败": "Hand-over failed",
    "连接失败: {}": "Connection failed: {}",
    "重载中: {}": "Reloading: {}",
    "重载全部模块...": "Reloading all modules...",
    "重载错误: {}": "Reload error: {}",
    "金钱同步已停止": "Money sync stopped",
    "金钱同步已开始 (每 {}s 检查)": "Money sync started (checks every {}s)",
    "需求同步已停止": "Needs sync stopped",
    "需求同步已开始 (每 {}s 检查)": "Needs sync started (checks every {}s)",
    "🎯 专注": "🎯 Focused",
    "🏠 你已成为新房主！其他成员将自动重连": "🏠 You're the new host! Everyone else will reconnect automatically",
    "💕 心动": "💕 Flirty",
    "💪 自信": "💪 Confident",
    "🔴 差": "🔴 Poor",
    "😊 开心": "😊 Happy",
    "😖 不适": "😖 Uncomfortable",
    "😜 顽皮": "😜 Playful",
    "😠 生气": "😠 Angry",
    "😢 难过": "😢 Sad",
    "😣 紧张": "😣 Tense",
    "😳 尴尬": "😳 Embarrassed",
    "😵 眩晕": "😵 Dazed",
    "🟠 一般": "🟠 Fair",
    "🟡 良好": "🟡 Good",
    "🟢 优秀": "🟢 Excellent",
    "🤢 恶心": "🤢 Nauseous",
    "🥱 无聊": "🥱 Bored",
    "🧳 房主发起共同旅行：已自动确认 ✅": "🧳 The host started group travel: confirmed automatically ✅",
    "🧳 房主已出发旅行，正在自动跟随前往同一地点...": "🧳 The host is travelling - following them to the same place...",
    "🧳 检测到你的旅行，成员正在自动跟随...": "🧳 You're travelling - the other players are following you...",
}

CJK = re.compile(r"[　-鿿＀-￯]")


def literal(s, like):
    """Re-quote `s` using the prefix/quote style of the original token `like`."""
    prefix = re.match(r"^[rRbBuUfF]*", like).group(0).replace("r", "").replace("R", "")
    return prefix + repr(s)


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "multimod")
    missing = set()
    for path in sorted(glob.glob(os.path.join(root, "*.py"))):
        src = open(path, encoding="utf-8").read()
        lines = src.splitlines(keepends=True)
        edits = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            s = tok.string
            if tok.type != tokenize.STRING or not CJK.search(s) or s.lstrip("rbuRBU").startswith(('"""', "'''")):
                continue
            val = ast.literal_eval(s)
            if val not in EN:
                missing.add(val)
                continue
            edits.append((tok.start, tok.end, literal(EN[val], s)))
        for (sl, sc), (el, ec), new in reversed(edits):
            if sl != el:
                raise SystemExit("multi-line string in {} line {}".format(path, sl))
            line = lines[sl - 1]
            lines[sl - 1] = line[:sc] + new + line[ec:]
        out = "".join(lines)
        ast.parse(out)
        if edits:
            open(path, "w", encoding="utf-8").write(out)
            print("{}: {} strings".format(os.path.basename(path), len(edits)))
    if missing:
        print("UNTRANSLATED:", missing)


if __name__ == "__main__":
    main()
