from aiogram.types import CallbackQuery

async def safe_edit(cb: CallbackQuery, text: str, reply_markup=None):
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        await cb.message.answer(text, parse_mode="HTML", reply_markup=reply_markup)

async def cb_answer(cb: CallbackQuery, text: str = "", alert: bool = False):
    try:
        await cb.answer(text, show_alert=alert)
    except Exception:
        pass

def fmt_event(ev: dict, parts: list = None) -> str:
    lines = [f"📅 <b>{ev['title']}</b>"]
    if ev.get('date_str'): lines.append(f"🗓 {ev['date_str']}")
    if ev.get('place'):    lines.append(f"📍 {ev['place']}")
    if ev.get('note'):     lines.append(f"📝 {ev['note']}")
    if parts:
        going = [p['username'] or f"user{p['user_id']}" for p in parts if p['status']=='going']
        maybe = [p['username'] or f"user{p['user_id']}" for p in parts if p['status']=='maybe']
        if going: lines.append(f"\n✅ Идут ({len(going)}): {', '.join(going)}")
        if maybe: lines.append(f"🤔 Может ({len(maybe)}): {', '.join(maybe)}")
    return "\n".join(lines)

def pick_event_kb(user_id: int, action_prefix: str):
    from core.events_service import list_user_events
    from telegram.keyboards import inline_grid
    events = list_user_events(user_id, limit=8)
    if not events:
        return None, []
    return inline_grid([(f"📅 {e['title']}", f"{action_prefix}:{e['id']}") for e in events], 1), events
