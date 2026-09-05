import math
from typing import Tuple


def haversine_distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate great circle distance between two decimal degree points in kilometers."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def bbox_polygon(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    """Generate GeoJSON Polygon coordinates for a bounding box."""
    return [
        [
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],
        ]
    ]
