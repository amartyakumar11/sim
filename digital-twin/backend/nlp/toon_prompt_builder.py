"""
TOON Prompt Builder for Gemini Translation.

Responsibilities:
- Construct strict system prompt
- Inject station catalog and city metadata
- Inject TOON grammar
- Prevent hallucinations
- Force output into DSL format only
"""


def build_toon_prompt(
    user_text: str,
    station_catalog: list[str],
    city: str
) -> str:
    """
    Build strict system prompt for Gemini TOON translation.
    
    Args:
        user_text: Natural language scenario description
        station_catalog: List of valid station IDs
        city: City name for context
        
    Returns:
        Complete system prompt string
    """
    station_list = ", ".join(station_catalog)
    
    return f"""
You are a TOON DSL compiler. Output nothing except the TOON script: one command per line, no explanations, no markdown, no code fences.

VALID STATION IDs (use only these): {station_list}

OUTPUT FORMAT — one line per command, e.g.:
BASE CITY {city}
BASE SEED 42
BASE DURATION 3600
STATION CP_01 SWAP_BAYS 2
STATION DWK_03 SWAP_BAYS 1
DEMAND PROFILE high
DEMAND MULTIPLIER 1.5
CONSTRAINT MAX_QUEUE 10
CONSTRAINT MAX_WAIT 300

COMMANDS YOU MAY USE:
BASE CITY <city_name>
BASE SEED <int>
BASE DURATION <seconds>
STATION <id> SWAP_BAYS <+int|-int>
STATION <id> CHARGERS <+int|-int>
STATION <id> INVENTORY <+int|-int>
DEMAND PROFILE <name>
DEMAND MULTIPLIER <float>
CONSTRAINT MAX_QUEUE <int>
CONSTRAINT MAX_WAIT <seconds>

Interpret the user's scenario and output a complete TOON script. If they mention "N stations" or specific stations, include that many STATION lines from the valid list. If they say "high demand", use DEMAND PROFILE high and DEMAND MULTIPLIER > 1. Always include BASE CITY and at least one STATION when the user describes a network.

User input:
\"\"\"{user_text}\"\"\"

City context: {city}
""".strip()
