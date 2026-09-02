"""Address formatting shared by the map and location endpoints."""
from typing import Any

# HSDS address fields in display order. address_2 carries floor / suite detail
_DISPLAY_PARTS = ("address_1", "address_2", "city", "state_province", "postal_code")


def format_address(fields: dict[str, Any]) -> str:
    """Join an Airtable address record's fields into one display string.

    Missing and empty parts are skipped. Values are whitespace-normalised
    because `city`, `state_province` and `postal_code` are multilineText in the
    base and can carry stray newlines that would break a one-line address.
    """
    parts = []
    for key in _DISPLAY_PARTS:
        value = fields.get(key)
        if value is None:
            continue
        text = " ".join(str(value).split())
        if text:
            parts.append(text)
    return ", ".join(parts)
