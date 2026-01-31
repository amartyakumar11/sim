from typing import Dict, Any, List
import math

class CoverageAnalyzer:
    """
    Analyzes network coverage and identifies gaps.
    """
    
    def __init__(self, city_config: Dict[str, Any]):
        self.stations = city_config.get("stations", [])
        self.zones = city_config.get("zones", [])
        self.COVERAGE_RADIUS_KM = 2.0  # 2km service radius
        
    def calculate_zone_coverage(self) -> Dict[str, float]:
        """
        Calculate approx coverage % for each zone.
        
        This uses a simplified 'point sampling' approach:
        1. Define zone centers (hardcoded for Lucknow MVP).
        2. Generate grid points around center.
        3. Check if point is within COVERAGE_RADIUS of any station.
        """
        results = {}
        
        # Approximate Zone Centers for Lucknow (Lat/Lon)
        # In a real system, these would come from polygon definitions
        zone_centers = {
            "central_lucknow": {"lat": 26.8467, "lon": 80.9462, "radius_km": 5},
            "gomti_nagar": {"lat": 26.8656, "lon": 80.9990, "radius_km": 6},
            "alambagh": {"lat": 26.8144, "lon": 80.9022, "radius_km": 4},
            "hazratganj": {"lat": 26.8542, "lon": 80.9448, "radius_km": 2},
            "indira_nagar": {"lat": 26.8900, "lon": 80.9800, "radius_km": 4},
            "mahanagar": {"lat": 26.8700, "lon": 80.9500, "radius_km": 3}
        }
        
        for zone_data in self.zones:
            # Extract ID and Centroid
            if isinstance(zone_data, dict):
                zone_id = zone_data.get("zone_id")
                centroid = zone_data.get("centroid", {})
                lat = centroid.get("latitude") or centroid.get("lat")
                lon = centroid.get("longitude") or centroid.get("lon")
                
                # Estimate radius (default 2km if likely explicit data missing)
                # Some configs might have explicit radius
                radius = zone_data.get("radius_km", 2.0)
            else:
                # Fallback for simple string list (simplified legacy mode)
                zone_id = zone_data
                fallback_center = zone_centers.get(zone_id)
                if not fallback_center:
                    results[zone_id] = 0.0
                    continue
                lat = fallback_center["lat"]
                lon = fallback_center["lon"]
                radius = fallback_center["radius_km"]

            if not lat or not lon:
                results[zone_id] = 0.0
                continue
                
            covered_points = 0
            total_points = 15  # Optimization: slightly fewer sample points for speed
            
            # Generate sample points in a circle around zone center
            for i in range(total_points):
                # Simple spiral distribution
                angle = 2.4 * i
                dist = math.sqrt(i / total_points) * radius
                
                # Convert km offset to lat/lon (approx)
                d_lat = (dist * math.cos(angle)) / 111.0
                d_lon = (dist * math.sin(angle)) / (111.0 * math.cos(math.radians(lat)))
                
                point_lat = lat + d_lat
                point_lon = lon + d_lon
                
                if self._is_covered(point_lat, point_lon):
                    covered_points += 1
            
            coverage_pct = (covered_points / total_points) * 100
            results[zone_id] = round(coverage_pct, 1)
            
        return results

    def _is_covered(self, lat: float, lon: float) -> bool:
        """Check if a location is within service radius of ANY station."""
        for station in self.stations:
            s_lat = station.get("latitude") or station.get("lat")
            s_lon = station.get("longitude") or station.get("lon")
            
            dist = self._haversine(lat, lon, s_lat, s_lon)
            if dist <= self.COVERAGE_RADIUS_KM:
                return True
        return False

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

def get_network_health(city_config: Dict[str, Any]) -> Dict[str, Any]:
    analyzer = CoverageAnalyzer(city_config)
    zone_stats = analyzer.calculate_zone_coverage()
    
    # Calculate overall health score
    avg_coverage = sum(zone_stats.values()) / len(zone_stats) if zone_stats else 0
    
    return {
        "overall_score": round(avg_coverage, 1),
        "zone_coverage": zone_stats,
        "underserved_zones": [z for z, score in zone_stats.items() if score < 60.0]
    }
