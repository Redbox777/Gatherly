FIELD_ALIASES = {
    "название": "title",
    "имя": "title",
    "дата": "date_str",
    "время": "date_str",
    "место": "place",
    "локация": "place",
    "заметка": "note",
    "примечание": "note",
    "напомнить": "remind_at",
    "напоминание": "remind_at",
}

def parse_event_message(text):
    result = {"title": None, "date_str": None, "place": None, "note": None, "remind_at": None}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    matched_any = False
    for line in lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key_norm = key.strip().lower()
        value = value.strip()
        if key_norm in FIELD_ALIASES and value:
            result[FIELD_ALIASES[key_norm]] = value
            matched_any = True

    if not matched_any and lines:
        result["title"] = lines[0]

    return result


def format_example():
    return (
        "📅 <b>Новая встреча</b>\n\n"
        "Напиши всё одним сообщением, например:\n\n"
        "<code>Название: Днюха у Саши\n"
        "Дата: 15 июля 18:00\n"
        "Место: Кафе Central\n"
        "Заметка: не забыть подарок\n"
        "Напомнить: 15 июля 17:00</code>\n\n"
        "Обязательно только «Название» — остальное можно не писать."
    )
