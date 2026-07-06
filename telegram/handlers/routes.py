from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core import routes_service
from telegram.keyboards import main_kb, cancel_kb, inline_grid
from telegram.states import RouteForm
from telegram.utils import safe_edit, cb_answer, pick_event_kb

def register(dp: Dispatcher):

    @dp.message(F.text == "🗺 Маршруты")
    async def btn_routes(m: Message):
        kb, events = pick_event_kb(m.from_user.id, "route:list")
        if not events:
            await m.answer("Сначала создай встречу — нажми 📅 Встречи"); return
        await m.answer("🗺 <b>Маршруты</b>\nВыбери встречу:", parse_mode="HTML", reply_markup=kb)

    @dp.message(RouteForm.title)
    async def fsm_title(m: Message, state: FSMContext):
        await state.update_data(title=m.text)
        await state.set_state(RouteForm.points)
        await m.answer(
            "📍 Точки маршрута — каждая с новой строки:\n\n<code>Парковка\nПарк\nКафе</code>",
            reply_markup=cancel_kb(), parse_mode="HTML"
        )

    @dp.message(RouteForm.points)
    async def fsm_points(m: Message, state: FSMContext):
        points = [p.strip() for p in m.text.split("\n") if p.strip()]
        if not points:
            await m.answer("Напиши хотя бы одну точку:"); return
        data = await state.get_data()
        await state.clear()
        routes_service.create_route(data['event_id'], m.from_user.id, data['title'], points)
        lines = [f"🗺 <b>{data['title']}</b>\n"]
        for i, pt in enumerate(points, 1):
            lines.append(f"{i}. 📍 {pt}")
        await m.answer("\n".join(lines), reply_markup=main_kb(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("route:list:"))
    async def cb_list(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        routes = routes_service.list_routes(eid)
        btns = [(f"🗺 {r['title']}", f"route:view:{r['id']}") for r in routes]
        btns.append(("➕ Создать маршрут", f"route:new:{eid}"))
        await safe_edit(cb, "🗺 <b>Маршруты</b>", reply_markup=inline_grid(btns, 1))

    @dp.callback_query(F.data.startswith("route:new:"))
    async def cb_new(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(RouteForm.title)
        await state.update_data(event_id=eid)
        await cb.message.answer("🗺 Название маршрута:", reply_markup=cancel_kb())

    @dp.callback_query(F.data.startswith("route:view:"))
    async def cb_view(cb: CallbackQuery):
        await cb_answer(cb)
        rid = int(cb.data.split(":")[2])
        data = routes_service.get_route_with_points(rid)
        if not data: return
        lines = [f"🗺 <b>{data['route']['title']}</b>\n"]
        for pt in data['points']:
            lines.append(f"{pt['order_num']}. 📍 {pt['name']}")
        await safe_edit(cb, "\n".join(lines))
