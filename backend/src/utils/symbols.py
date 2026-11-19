import re

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,15}/[A-Z0-9]{2,15}$")


def normalize_pair(raw_symbol: str, default_quote: str = "USDT") -> str:
    cleaned = raw_symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol darf nicht leer sein.")

    # Trennzeichen wie '-' oder '_' Vereinheitlichen und Leerzeichen um '/' entfernen
    cleaned = re.sub(r"\s*/\s*", "/", cleaned)
    cleaned = cleaned.replace("-", "/").replace("_", "/")

    # Kein Slash vorhanden -> Standard-Quote anhängen (z. B. "xrp" -> "XRP/USDT")
    if "/" not in cleaned:
        pair = f"{cleaned}/{default_quote.upper()}"
    else:
        parts = cleaned.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Ungültiges Trading-Pair: '{raw_symbol}'")
        pair = f"{parts[0]}/{parts[1]}"

    if not SYMBOL_PATTERN.match(pair):
        raise ValueError(f"Ungültiges Trading-Pair-Format: '{pair}'")

    return pair