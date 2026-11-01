import requests

from django.conf import settings


def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ua",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        weather = {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "feels_like": data["main"]["feels_like"],
            "wind_speed": data["wind"]["speed"],
            "pressure": data["main"]["pressure"],
        }

        return weather

    except requests.exceptions.RequestException:
        return None

    except (KeyError, IndexError, ValueError, TypeError):
        return None
