"""
TOON DSL Parser and Validator.

Responsibilities:
- Parse TOON DSL text
- Validate syntax
- Validate station references
- Return structured config dict compatible with run_simulation()
"""


class ToonParseError(Exception):
    """Raised when TOON DSL parsing fails."""
    pass


def _extract_from_fences(script: str) -> str:
    """Use the first markdown code block if present; otherwise return script as-is."""
    script = (script or "").strip()
    if "```" not in script:
        return script
    try:
        start = script.index("```") + 3
        rest = script[start:].lstrip()
        # optional lang id, e.g. "toon\n"
        if rest.lower().startswith("toon"):
            rest = rest[4:].lstrip()
        end = rest.find("```")
        block = rest[:end] if end >= 0 else rest
        return block.strip()
    except Exception:
        return script


def parse_toon_script(script: str, station_catalog: set[str]) -> dict:
    """
    Parse TOON DSL script into structured configuration.
    
    Args:
        script: Raw TOON DSL text
        station_catalog: Set of valid station IDs for validation
        
    Returns:
        Dictionary with structure:
        {
            "base": {...},
            "stations": {...},
            "demand": {...},
            "constraints": {...}
        }
        
    Raises:
        ToonParseError: If parsing fails or validation fails
    """
    config = {
        "base": {},
        "stations": {},
        "demand": {},
        "constraints": {}
    }
    
    script = _extract_from_fences(script)
    lines = [l.strip() for l in script.splitlines() if l.strip()]
    
    for line in lines:
        # Remove any markdown code fences that Gemini might add
        if line.startswith("```"):
            continue
            
        parts = line.split()
        
        if len(parts) < 2:
            continue  # Skip empty or malformed lines
        
        if parts[0] == "BASE":
            if len(parts) < 3:
                raise ToonParseError(f"Invalid BASE command: {line}")
            key = parts[1].lower()
            # Handle multi-word values (e.g., city names with spaces)
            value = " ".join(parts[2:])
            
            # Convert numeric values
            if key == "seed" or key == "duration":
                try:
                    value = int(value)
                except ValueError:
                    raise ToonParseError(f"Invalid numeric value in BASE {key}: {value}")
            
            config["base"][key] = value
        
        elif parts[0] == "STATION":
            if len(parts) < 2:
                raise ToonParseError(f"Invalid STATION command: {line}")
            
            station_id = parts[1]
            if station_id not in station_catalog:
                raise ToonParseError(f"Invalid station: {station_id}")
            
            if station_id not in config["stations"]:
                config["stations"][station_id] = {}
            
            # "STATION <id>" alone: include station with no overrides
            if len(parts) < 4:
                continue
            
            field = parts[2].lower()
            value_str = parts[3]
            
            # Parse relative values (+int or -int)
            if value_str.startswith("+") or value_str.startswith("-"):
                try:
                    value = int(value_str)
                except ValueError:
                    raise ToonParseError(f"Invalid STATION value: {value_str}")
            else:
                # Absolute value
                try:
                    value = int(value_str)
                except ValueError:
                    raise ToonParseError(f"Invalid STATION value: {value_str}")
            
            config["stations"][station_id][field] = value
        
        elif parts[0] == "DEMAND":
            if len(parts) < 3:
                raise ToonParseError(f"Invalid DEMAND command: {line}")
            
            key = parts[1].lower().replace("multipli.er", "multiplier")
            # Handle multi-word values (e.g., "rush hour" profile)
            value = " ".join(parts[2:])
            
            # Convert numeric values
            if key == "multiplier":
                try:
                    value = float(value)
                except ValueError:
                    raise ToonParseError(f"Invalid DEMAND MULTIPLIER value: {value}")
            
            config["demand"][key] = value
        
        elif parts[0] == "CONSTRAINT":
            if len(parts) < 3:
                raise ToonParseError(f"Invalid CONSTRAINT command: {line}")
            
            key = parts[1].lower()
            value = parts[2]
            
            # Convert numeric values
            try:
                value = int(value)
            except ValueError:
                raise ToonParseError(f"Invalid CONSTRAINT value: {value}")
            
            config["constraints"][key] = value
        
        else:
            # Skip unknown commands (might be explanations from Gemini)
            # Only raise error for clearly malformed lines
            if len(parts) > 0 and not line.startswith("#"):
                # Log but don't fail - Gemini might add comments
                continue
    
    return config
