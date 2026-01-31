from typing import Dict, Any, List
import math
import random
from .coverage import CoverageAnalyzer

class StationRecommender:
    """
    Identifies optimal locations for new stations based on coverage gaps.
    """
    
    def __init__(self, city_config: Dict[str, Any]):
        self.city_config = city_config
        self.analyzer = CoverageAnalyzer(city_config)
        self.existing_stations = city_config.get("stations", [])
        
    def generate_recommendations(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate a list of recommended station locations.
        """
        # 1. Analyze current coverage
        coverage_stats = self.analyzer.calculate_zone_coverage()
        
        # 2. Identify underserved zones (coverage < 60%)
        underserved_zones = [
            zone for zone, score in coverage_stats.items() 
            if score < 70.0 # Higher threshold to ensure we always have suggestions for MVP
        ]
        
        # If all zones are well covered, pick the lowest scoring ones
        if not underserved_zones:
            sorted_zones = sorted(coverage_stats.items(), key=lambda x: x[1])
            underserved_zones = [z[0] for z in sorted_zones[:3]]
            
        recommendations = []
        
        # 3. Generate candidates in underserved zones
        candidates = []
        for zone_id in underserved_zones:
            # Find zone definition
            zone_def = {}
            for z in self.city_config.get("zones", []):
                # Handle both dict and string formats
                zid = z.get("zone_id") if isinstance(z, dict) else z
                if zid == zone_id:
                     if isinstance(z, dict):
                         cent = z.get("centroid", {})
                         zone_def = {
                             "lat": cent.get("latitude") or cent.get("lat"),
                             "lon": cent.get("longitude") or cent.get("lon"),
                             "r": z.get("radius_km", 2.0) * 0.01 # Convert km to approx lat/lon degrees (rough fallback)
                         }
                         # Better degree conversion: 1 deg lat ~= 111km
                         km_to_deg = 1 / 111.0
                         zone_def["r"] = z.get("radius_km", 2.0) * km_to_deg
                     else:
                          # Hardcoded fallback
                          zone_definitions = {
                                "central_lucknow": {"lat": 26.8467, "lon": 80.9462, "r": 0.04},
                                "gomti_nagar": {"lat": 26.8656, "lon": 80.9990, "r": 0.05}
                                # ... add more if needed
                          }
                          zone_def = zone_definitions.get(zone_id)
                     break
            
            if not zone_def or not zone_def.get("lat"):
                continue
                
            # Generate 10 candidates per underserved zone
            for _ in range(10):
                # Random point within zone radius
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0.2 * zone_def["r"], zone_def["r"]) # Avoid exact center
                
                cand_lat = zone_def["lat"] + dist * math.sin(angle)
                cand_lon = zone_def["lon"] + dist * math.cos(angle)
                
                score = self._score_location(cand_lat, cand_lon)
                candidates.append({
                    "lat": cand_lat, 
                    "lon": cand_lon, 
                    "score": score,
                    "zone": zone_id
                })
        
        # 4. Select top candidates
        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Pick top 'count', ensuring min distance between selected ones
        selected = []
        for cand in candidates:
            if len(selected) >= count:
                break
                
            # Check overlap with already selected
            is_far_enough = True
            for s in selected:
                if self._dist(cand["lat"], cand["lon"], s["lat"], s["lon"]) < 1.0: # 1km separation
                    is_far_enough = False
                    break
            
            if is_far_enough:
                selected.append(cand)
                
        # Format output
        return [
            {
                "latitude": s["lat"],
                "longitude": s["lon"],
                "type": "new_station",
                "score": round(s["score"], 2),
                "reason": f"High demand gap in {s['zone'].replace('_', ' ').title()}",
                "zone_id": s["zone"]
            }
            for s in selected
        ]

    def _score_location(self, lat: float, lon: float) -> float:
        """
        Score a location: Higher is better.
        Reward distance from existing stations (fill gaps).
        """
        min_dist = float('inf')
        for s in self.existing_stations:
            s_lat = s.get("latitude") or s.get("lat")
            s_lon = s.get("longitude") or s.get("lon")
            d = self._dist(lat, lon, s_lat, s_lon)
            if d < min_dist:
                min_dist = d
        
        # Cap useful distance benefit at 3km (don't reward being in the middle of nowhere)
        capped_dist = min(min_dist, 3.0)
        
        # Score is primarily based on distance from nearest neighbor
        return capped_dist * 10
        
    def _dist(self, lat1, lon1, lat2, lon2):
        # Haversine distance in km
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

def get_station_recommendations(city_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    recommender = StationRecommender(city_config)
    return recommender.generate_recommendations()
