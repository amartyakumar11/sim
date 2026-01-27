"""
Test script for Natural Language to TOON translation.

Usage:
    python -m backend.nlp.test_translation
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.nl_to_toon import translate_nl_to_toon


def test_translation():
    """Test the translation function."""
    print("Testing Natural Language to TOON translation...")
    print("-" * 60)
    
    # Test case from spec
    user_text = "Add 2 chargers at CP_01 and increase rush hour demand by 1.5x"
    station_catalog = ["CP_01", "DWK_03", "INA_02"]
    city = "Bangalore"
    
    try:
        result = translate_nl_to_toon(
            user_text,
            station_catalog,
            city
        )
        
        print("✓ Translation successful!")
        print("\nResult:")
        import json
        print(json.dumps(result, indent=2))
        
        # Validate structure
        assert "base" in result, "Missing 'base' section"
        assert "stations" in result, "Missing 'stations' section"
        assert "demand" in result, "Missing 'demand' section"
        assert "constraints" in result, "Missing 'constraints' section"
        
        print("\n✓ Structure validation passed!")
        return True
        
    except RuntimeError as e:
        if "GEMINI_API_KEY" in str(e):
            print("⚠ GEMINI_API_KEY not set - skipping test")
            print("  Set GEMINI_API_KEY environment variable to test")
            return False
        else:
            print(f"✗ Runtime error: {e}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_translation()
    sys.exit(0 if success else 1)
