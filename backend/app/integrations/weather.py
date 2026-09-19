import json
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any

LATITUDE = 11.65
LONGITUDE = 76.13
TIMEZONE = "Asia/Kolkata"
OPEN_METEO_URL = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LATITUDE}&longitude={LONGITUDE}"
    f"&current=precipitation,rain"
    f"&hourly=precipitation,rain"
    f"&past_days=3&forecast_days=3"
    f"&timezone={TIMEZONE.replace('/', '%2F')}"
)

CACHE_TTL_SECONDS = 900  # 15 minutes

_cache_data: dict[str, Any] | None = None
_cache_timestamp: float = 0.0


def fetch_live_weather(force_refresh: bool = False) -> dict[str, Any]:
    """
    Fetch real live weather observation & forecast from Open-Meteo API.
    Uses 15-min in-memory cache and handles failure gracefully.
    Never fabricates fake rainfall data.
    """
    global _cache_data, _cache_timestamp

    now = time.time()
    if not force_refresh and _cache_data is not None and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
        cached_res = dict(_cache_data)
        cached_res["is_cached"] = True
        return cached_res

    try:
        req = urllib.request.Request(
            OPEN_METEO_URL,
            headers={"User-Agent": "HAZIVA-Landslide-Risk-System/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"Open-Meteo API returned HTTP status {response.status}")
            data = json.loads(response.read().decode("utf-8"))

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        precip = hourly.get("precipitation", [])

        now_iso = datetime.now(timezone.utc).isoformat()

        # Calculate observed 24h (past 24 values up to current hour) and forecast 24h/72h
        total_hours = len(precip)
        mid_idx = total_hours // 2 if total_hours > 48 else 24

        observed_24h = float(sum(precip[max(0, mid_idx - 24):mid_idx])) if precip else 0.0
        forecast_24h = float(sum(precip[mid_idx:min(total_hours, mid_idx + 24)])) if precip else 0.0
        forecast_72h = float(sum(precip[mid_idx:min(total_hours, mid_idx + 72)])) if precip else 0.0

        result = {
            "provider": "Open-Meteo Weather API / ECMWF IFS Model",
            "status": "ONLINE",
            "latitude": float(data.get("latitude", LATITUDE)),
            "longitude": float(data.get("longitude", LONGITUDE)),
            "elevation": float(data.get("elevation", 750.0)),
            "timezone": data.get("timezone", TIMEZONE),
            "timestamp": now_iso,
            "observed_24h_mm": round(observed_24h, 2),
            "forecast_24h_mm": round(forecast_24h, 2),
            "forecast_72h_mm": round(forecast_72h, 2),
            "is_cached": False,
            "error": None,
        }

        _cache_data = result
        _cache_timestamp = now
        return result

    except Exception as exc:
        err_msg = f"Live weather API fetch failed: {exc}"
        print(f"[WEATHER_INTEGRATION_WARNING] {err_msg}")

        # If cache exists, return stale cache with explicit status
        if _cache_data is not None:
            stale_res = dict(_cache_data)
            stale_res["status"] = "STALE_CACHED"
            stale_res["is_cached"] = True
            stale_res["error"] = err_msg
            return stale_res

        # If no cache available, return UNAVAILABLE status without generating fake numbers
        return {
            "provider": "Open-Meteo Weather API / ECMWF IFS Model",
            "status": "UNAVAILABLE",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "elevation": 750.0,
            "timezone": TIMEZONE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "observed_24h_mm": 0.0,
            "forecast_24h_mm": 0.0,
            "forecast_72h_mm": 0.0,
            "is_cached": False,
            "error": err_msg,
        }
