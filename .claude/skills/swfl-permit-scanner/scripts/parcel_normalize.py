"""
parcel_normalize.py
Normalize SWFL parcel/folio/STRAP numbers for consistent deduplication.

SWFL formats vary by county:
  Lee County STRAP:  26-46-25-00-00001.0000  (dashes + dot)
  Collier folio:     00123456789              (digits only)
  Charlotte:         412101001001             (digits, sometimes with dashes)
  Sarasota PIN:      2030120004               (10-digit numeric Parcel ID Number)
  Manatee Parcel ID: 1234567890               (numeric; the county UI displays/accepts it with spaces)

Normalization rule: strip all non-alphanumeric characters and lowercase.
This ensures "26-46-25-00-00001.0000" == "2646250000010000" for matching purposes,
and likewise normalizes the spaces in a Manatee parcel ID away.

Usage:
    from parcel_normalize import normalize_parcel
    key = normalize_parcel("26-46-25-00-00001.0000")  # -> "264625000001000"
"""

import re


def normalize_parcel(parcel: str) -> str:
    """Strip all non-alphanumeric characters and lowercase the result."""
    if not parcel:
        return ""
    return re.sub(r"[^a-z0-9]", "", parcel.lower())


def parcels_match(a: str, b: str) -> bool:
    """Return True if two parcel strings normalize to the same value."""
    return bool(normalize_parcel(a) and normalize_parcel(a) == normalize_parcel(b))


if __name__ == "__main__":
    # Quick smoke test
    examples = [
        ("26-46-25-00-00001.0000", "26462500000010000"),  # Lee STRAP with dashes vs digits-only
        ("0041-2101-001001", "0041 2101 001001"),          # Charlotte with dashes vs spaces
        ("12345-678-9", "123456789"),                      # dashes stripped
        ("1234 5678 90", "1234567890"),                    # Manatee parcel ID with spaces vs digits-only
    ]
    for a, b in examples:
        na, nb = normalize_parcel(a), normalize_parcel(b)
        print(f"{a!r:35} -> {na}")
        print(f"{b!r:35} -> {nb}")
        print(f"  match: {na == nb}\n")
