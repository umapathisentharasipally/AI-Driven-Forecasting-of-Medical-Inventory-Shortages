from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def parse_date(s: str) -> datetime:
    parsed = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def days_until(future: datetime) -> int:
    if future.tzinfo is None:
        future = future.replace(tzinfo=timezone.utc)
    delta = future.astimezone(timezone.utc) - utc_now()
    return delta.days


def date_range_filter(from_str: str | None, to_str: str | None) -> dict:
    query: dict = {}

    if from_str:
        query["$gte"] = parse_date(from_str)

    if to_str:
        query["$lte"] = parse_date(to_str)

    return query