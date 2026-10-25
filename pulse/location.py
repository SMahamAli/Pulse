"""Replaceable postcode lookup and approximate distance; no patient location storage."""

import json
from math import asin, cos, radians, sin, sqrt
import re
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


# Postcodes.io outcode response verified 24 October 2026. Keeps LS6 demo usable offline.
DEMO_AREAS = {"LS6": (53.820118247457614, -1.5708277435028253)}
OUTCODE = r"[A-Z]{1,2}[0-9][A-Z0-9]?"


def postcode_district(value):
    compact = re.sub(r"\s+", "", value.strip().upper())
    match = re.fullmatch(f"({OUTCODE})(?:[0-9][A-Z]{{2}})?", compact)
    if not match:
        raise ValueError("Enter a UK postcode district such as LS6, or a full UK postcode.")
    return match[1]


def lookup_area(value):
    district = postcode_district(value)
    if district in DEMO_AREAS:
        latitude, longitude = DEMO_AREAS[district]
        source = "Saved Postcodes.io district centre (24 October 2026); works without internet"
    else:
        try:
            with urlopen(f"https://api.postcodes.io/outcodes/{district}", timeout=4) as response:
                result = json.load(response).get("result")
            if not result:
                raise ValueError("Postcode district not found. Check it and try again.")
            latitude, longitude = float(result["latitude"]), float(result["longitude"])
        except HTTPError as error:
            if error.code == 404:
                raise ValueError("Postcode district not found. Check it and try again.") from error
            raise ValueError("Postcode lookup unavailable. Retry or use the LS6 demo.") from error
        except (URLError, TimeoutError, OSError, KeyError, TypeError, ValueError) as error:
            raise ValueError("Postcode lookup unavailable. Retry or use the LS6 demo.") from error
        source = "Postcodes.io district centre"
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Postcode coordinates unavailable. Please try again.")
    return dict(district=district, lat=latitude, lon=longitude, source=source)


def distance_miles(latitude, longitude, destination_latitude, destination_longitude):
    lat1, lat2 = radians(latitude), radians(destination_latitude)
    delta_lat = lat2 - lat1
    delta_lon = radians(destination_longitude - longitude)
    term = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 3958.8 * 2 * asin(sqrt(min(1, max(0, term))))


def nearby(hospitals, area, radius=30):
    results = []
    for hospital in hospitals:
        distance = distance_miles(area["lat"], area["lon"], hospital["lat"], hospital["lon"])
        if distance <= radius:
            results.append(dict(hospital, distance=round(distance, 1), sortDistance=distance))
    return sorted(results, key=lambda hospital: hospital["sortDistance"])
