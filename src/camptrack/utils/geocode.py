import httpx

async def geocode_place(query: str, limit: int = 5):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
    }

    headers = {"User-Agent": "camptrack-cli"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
    except httpx.RequestError:
        return None     # network error
    except httpx.HTTPStatusError:
        return None     # server responded with 4xx or 5xx

    try:
        data = response.json()
    except ValueError:
        return None     # bad JSON

    results = []
    for item in data:
        try:
            results.append({
                "name": item["display_name"],
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
            })
        except (KeyError, ValueError):
            continue

    return results
