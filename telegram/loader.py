import importlib, logging
from aiogram import Dispatcher

log = logging.getLogger(__name__)

HANDLERS = [
    "telegram.handlers.meet",
    "telegram.handlers.places",
    "telegram.handlers.expenses",
    "telegram.handlers.weather",
    "telegram.handlers.sun",
    "telegram.handlers.links",
    "telegram.handlers.statistics",
    "telegram.handlers.people",
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
