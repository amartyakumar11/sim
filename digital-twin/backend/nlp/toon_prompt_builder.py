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
You are a TOON DSL compiler.

Your job is to convert a user's natural language scenario into a valid TOON script.

STRICT RULES:
- Output ONLY TOON DSL
- Do NOT include explanations
- Do NOT include markdown
- Do NOT invent stations
- Only use station IDs from this list:
  {station_list}
- Use only these commands:

VALID COMMANDS:
BASE CITY <city_name>
BASE SEED <int>
BASE DURATION <seconds>

STATION <station_id> SWAP_BAYS <+int|-int>
STATION <station_id> CHARGERS <+int|-int>
STATION <station_id> INVENTORY <+int|-int>

DEMAND PROFILE <profile_name>
DEMAND MULTIPLIER <float>

CONSTRAINT MAX_QUEUE <int>
CONSTRAINT MAX_WAIT <seconds>

If user intent is unclear, make the smallest safe change.

User Input:
\"\"\"{user_text}\"\"\"

City: {city}
""".strip()
