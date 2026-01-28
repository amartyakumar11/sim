"""
Natural Language to TOON DSL Translation Orchestrator.

Responsibilities:
- Orchestrate translation flow
- Call prompt builder
- Call Gemini client
- Parse and validate output
- Return structured scenario config
"""

import logging

from .gemini_client import GeminiClient
from .toon_prompt_builder import build_toon_prompt
from .toon_parser import parse_toon_script, ToonParseError

logger = logging.getLogger(__name__)


def translate_nl_to_toon(
    user_text: str,
    station_catalog: list[str],
    city: str
) -> tuple[dict, str]:
    """
    Translate natural language scenario to TOON DSL configuration.
    
    Args:
        user_text: Natural language scenario description
        station_catalog: List of valid station IDs
        city: City name for context
        
    Returns:
        (scenario_config, raw_toon_text) – parsed config and raw Gemini output
        
    Raises:
        RuntimeError: If Gemini API fails
        ToonParseError: If TOON parsing fails
        ValueError: If validation fails
    """
    # Build prompt
    prompt = build_toon_prompt(user_text, station_catalog, city)
    
    # Call Gemini
    client = GeminiClient()
    toon_text = client.generate_toon(prompt)
    
    # Parse TOON script
    scenario_config = parse_toon_script(toon_text, set(station_catalog))
    
    if not scenario_config.get("stations"):
        logger.warning(
            "Parsed TOON has no STATION lines. Raw Gemini output (first 1500 chars): %s",
            (toon_text or "")[:1500],
        )
    
    # Validate required fields
    validate_toon_config(scenario_config, station_catalog)
    
    return scenario_config, (toon_text or "")


def validate_toon_config(config: dict, station_catalog: list[str]) -> None:
    """
    Validate parsed TOON configuration.
    
    Args:
        config: Parsed configuration dictionary
        station_catalog: List of valid station IDs
        
    Raises:
        ValueError: If validation fails
    """
    # Enforce defaults
    base = config.get("base", {})
    
    # Set defaults if missing
    if "seed" not in base:
        base["seed"] = 42
    else:
        base["seed"] = int(base["seed"])
    
    if "duration" not in base:
        base["duration"] = 3600
    else:
        base["duration"] = int(base["duration"])
    
    if "city" not in base:
        raise ValueError("Missing BASE CITY in TOON script")
    
    # Validate station references
    stations = config.get("stations", {})
    for station_id in stations.keys():
        if station_id not in station_catalog:
            raise ValueError(f"Invalid station ID: {station_id}")
        
        # Validate no negative swap bays after diff
        station_config = stations[station_id]
        if "swap_bays" in station_config:
            # Note: We can't validate final value without base config,
            # but we can validate the diff is reasonable
            swap_bays_diff = station_config["swap_bays"]
            if isinstance(swap_bays_diff, int) and swap_bays_diff < -100:
                raise ValueError(f"Station {station_id} has unreasonable swap_bays diff: {swap_bays_diff}")
