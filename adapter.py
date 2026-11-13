from datetime import datetime


def _to_unix(value) -> int:
    """Превращает что угодно в Unix-время."""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(value, fmt).timestamp())
            except ValueError:
                continue
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def from_tradingview(bars: list) -> list:
    """TradingView (tvkit) → единый формат."""
    result = []
    for b in bars:
        result.append({
            'time': _to_unix(b.timestamp),
            'open': float(b.open),
            'high': float(b.high),
            'low': float(b.low),
            'close': float(b.close),
        })
    return result