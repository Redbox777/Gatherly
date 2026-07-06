import aiohttp
from datetime import datetime

WEATHER_CODES = {
    0:"☀️ Ясно", 1:"🌤 Преимущественно ясно", 2:"⛅️ Переменная облачность",
    3:"☁️ Пасмурно", 45:"🌫 Туман", 48:"🌫 Изморозь",
    51:"🌦 Морось", 61:"🌧 Дождь", 63:"🌧 Сильный дождь",
    71:"🌨 Снег", 73:"🌨 Сильный снег", 75:"❄️ Метель",
    80:"🌦 Ливень", 95:"⛈ Гроза",
}

async def geocode(city: str):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
        results = data.get("results")
        return results[0] if results else None
    except Exception:
        return None

async def get_weather(city: str):
    loc = await geocode(city)
    if not loc:
        return None
    try:
        w_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={loc['latitude']}&longitude={loc['longitude']}"
            f"&current=temperature_2m,apparent_temperature,weathercode,windspeed_10m,relativehumidity_2m"
            f"&timezone=auto"
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(w_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
        cur = data["current"]
        return {
            "name": loc.get("name", city), "country": loc.get("country", ""),
            "temp": round(cur["temperature_2m"]), "feels": round(cur["apparent_temperature"]),
            "desc": WEATHER_CODES.get(cur.get("weathercode", 0), "🌡"),
            "wind": round(cur["windspeed_10m"]), "humidity": cur.get("relativehumidity_2m", "—"),
        }
    except Exception:
        return None

async def get_sun(city: str):
    loc = await geocode(city)
    if not loc:
        return None
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={loc['latitude']}&longitude={loc['longitude']}"
            f"&daily=sunrise,sunset&timezone=auto&start_date={today}&end_date={today}"
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
        daily = data.get("daily", {})
        sunrises, sunsets = daily.get("sunrise", []), daily.get("sunset", [])
        if not sunrises or not sunsets:
            return None
        sunrise = sunrises[0].split("T")[1][:5] if "T" in sunrises[0] else sunrises[0]
        sunset  = sunsets[0].split("T")[1][:5]  if "T" in sunsets[0]  else sunsets[0]
        return {
            "name": loc.get("name", city), "country": loc.get("country", ""),
            "sunrise": sunrise, "sunset": sunset, "date": today
        }
    except Exception:
        return None
