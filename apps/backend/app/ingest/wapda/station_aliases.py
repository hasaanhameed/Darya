# Station names as written in column A of a WAPDA day sheet → our node ids.
# Gomal Zam is left out on purpose (ADR-017). "tarbela_t4" is not a node: its turbine
# flow is only used to check Tarbela's total outflow.
STATION_ALIASES = {
    "TARBELA": "tarbela",
    "T-4 EXT": "tarbela_t4",
    "GHAZI BAROTHA": "ghazi_barotha",
    "G/BAROTHA": "ghazi_barotha",
    "MANGLA": "mangla",
    "WARSAK": "warsak",
    "CHASHMA": "chashma",
    "JINNAH": "jinnah",
}


def station_id_for(name: str) -> str | None:
    """Return our id for a station name from the sheet, or None if it isn't a station we use."""
    normalised = name.strip().upper().rstrip(":").strip()
    return STATION_ALIASES.get(normalised)
