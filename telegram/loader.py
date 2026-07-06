import importlib, logging
from aiogram import Dispatcher

log = logging.getLogger(__name__)

HANDLERS = [
    "telegram.handlers.events",
    "telegram.handlers.places",
    "telegram.handlers.checklists",
    "telegram.handlers.polls",
    "telegram.handlers.expenses",
    "telegram.handlers.routes",
    "telegram.handlers.links",
    "telegram.handlers.weather",
    "telegram.handlers.sun",
    "telegram.handlers.statistics",
    "telegram.handlers.help",
]

def load_handlers(dp: Dispatcher):
    for path in HANDLERS:
        try:
            module = importlib.import_module(path)
            if hasattr(module, "register"):
                module.register(dp)
                log.info(f"✅ Загружен: {path}")
            else:
                log.warning(f"⚠️ Нет register() в {path}")
        except Exception as e:
            log.error(f"❌ Ошибка загрузки {path}: {e}")
