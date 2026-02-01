from typing import Dict, Any, List
import pandas as pd
import numpy as np

class DemandForecaster:
    """
    Predicts future demand and stockout risks using historical simulation data.
    Uses a Simple Moving Average (SMA) approach suitable for real-time aggregation.
    """
    
    def __init__(self, station_history: Dict[str, Any]):
        """
        :param station_history: Dict mapping station_id to timeline data
        """
        self.station_history = station_history
        self.FORECAST_HORIZON_MINUTES = 60
        self.BUCKET_SIZE_MINUTES = 10
        
    def predict_demand(self, station_id: str, current_minute: int) -> Dict[str, Any]:
        """
        Predict demand for the next hour for a specific station.
        """
        if station_id not in self.station_history:
            return {"error": "Station not found in history"}
            
        timeline = self.station_history[station_id]
        
        # Need at least 30 mins of history to make a decent guess
        if current_minute < 30:
            return {
                "forecast": [], 
                "risk_level": "unknown",
                "message": " Insufficient history"
            }
            
        # 1. Extract recent demand trend
        # We look at the 'states' log to calculate swap rate
        # Simplified: We treat the timeline as a series of minutes
        
        # Aggregating demand into buckets
        # In a real DB, this is a SQL query. Here we iterate the memory log.
        recent_states = [s for s in timeline.get("states", []) if s["minute"] <= current_minute]
        
        # Create a basic time series of queues/swaps
        # We use queue length changes as a proxy for demand intensity if direct swap logs aren't explicit
        # Better: use the 'swaps_completed' counter if available, else infer from queue/inventory delta
        
        # Quick heuristic: Average queue length over last 30 mins
        last_30_states = [s for s in recent_states if s["minute"] > current_minute - 30]
        if not last_30_states:
            avg_queue = 0
        else:
            avg_queue = sum(s.get("queue", 0) for s in last_30_states) / len(last_30_states)
            
        # Slope of inventory change (batteries/min)
        # Take point A (30 mins ago) and point B (now)
        start_inv = last_30_states[0].get("inventory", 0) if last_30_states else 10
        end_inv = last_30_states[-1].get("inventory", 0) if last_30_states else 10
        
        # Consumption rate (batteries consumed per minute)
        # Note: This accounts for charging too, so it's Net Inventory Change
        # If negative, we are losing batteries faster than charging
        net_change_rate = (end_inv - start_inv) / 30.0
        
        # 2. Project Future Inventory
        current_inv = end_inv
        predictions = []
        risk_level = "low"
        
        for i in range(10, self.FORECAST_HORIZON_MINUTES + 1, 10):
            future_minute = current_minute + i
            
            # Linear projection
            predicted_inv = current_inv + (net_change_rate * i)
            
            # Floor at 0
            predicted_inv = max(0, predicted_inv)
            
            # Cap at max capacity (assuming ~12 for standard stations)
            predicted_inv = min(20, predicted_inv)
            
            predictions.append({
                "minute": future_minute,
                "predicted_inventory": round(predicted_inv, 1),
                "net_flow_rate": round(net_change_rate, 2)
            })
            
            if predicted_inv < 1.0:
                risk_level = "critical"
            elif predicted_inv < 3.0 and risk_level != "critical":
                risk_level = "high"
                
        return {
            "station_id": station_id,
            "current_inventory": current_inv,
            "net_flow_rate": round(net_change_rate, 2),
            "risk_level": risk_level,
            "forecast": predictions
        }

def generate_station_forecast(station_id: str, current_minute: int, city_manager_ref) -> Dict[str, Any]:
    """
    Helper to bridge API and Forecaster.
    Refereces the global city_manager to get timelines.
    """
    # In a proper architecture, we'd inject the repo. 
    # Here we access the memory store directly via the passed reference.
    
    if not city_manager_ref or not hasattr(city_manager_ref, "timelines"):
        return {}
        
    forecaster = DemandForecaster(city_manager_ref.timelines)
    return forecaster.predict_demand(station_id, current_minute)
