import requests
from datetime import date, timedelta, datetime, timezone

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TIMEOUT = 45


class ElexonAPIError(Exception):
    """Raised when Elexon cannot provide valid data."""


def fetch_json(dataset, params):
    url = f"{BASE_URL}/{dataset}/stream"

    try:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            raise ElexonAPIError(
                f"Unexpected response from {dataset}"
            )

        return data

    except requests.RequestException as exc:
        raise ElexonAPIError(
            f"Failed to retrieve {dataset} from Elexon"
        ) from exc

    except ValueError as exc:
        raise ElexonAPIError(
            f"Invalid JSON from {dataset}"
        ) from exc


def date_range(start, end):
    """Yield dates from start through end, inclusive."""
    current = date.fromisoformat(start)
    last = date.fromisoformat(end)

    while current <= last:
        yield current
        current += timedelta(days=1)


def fetch_actuals(month_start, next_month):
    """
    Fetch national WIND actuals one settlement date at a time.
    Settlement-date parameters are not mixed with publication filters.
    """
    end_date = (
        date.fromisoformat(next_month) - timedelta(days=1)
    ).isoformat()

    rows = []

    for day in date_range(month_start, end_date):
        data = fetch_json(
            "FUELHH",
            {
                "settlementDateFrom": day.isoformat(),
                "settlementDateTo": day.isoformat(),
                "fuelType": "WIND",
            },
        )

        for row in data:
            if row.get("fuelType") != "WIND":
                continue

            if not row.get("startTime"):
                continue

            try:
                generation = float(row["generation"])
            except (KeyError, TypeError, ValueError):
                continue

            rows.append({
                "startTime": row["startTime"],
                "generation": generation,
            })

    # Deduplicate actuals by delivery timestamp.
    unique = {
        row["startTime"]: row
        for row in rows
    }

    return list(unique.values())


def fetch_forecasts(month_start, next_month):
    """
    Fetch forecasts using publication-time filters only.
    Smaller publication windows reduce the size of each request.
    """
    start = date.fromisoformat(month_start)
    end = date.fromisoformat(next_month)

    publish_start = start - timedelta(days=1)
    publish_end = end

    rows = []
    current = publish_start

    while current < publish_end:
        window_end = min(
            current + timedelta(days=1),
            publish_end,
        )

        publish_from = (
            datetime.combine(
                current, datetime.min.time(), tzinfo=timezone.utc
            ).isoformat().replace("+00:00", "Z")
        )

        publish_to = (
            datetime.combine(
                window_end, datetime.min.time(), tzinfo=timezone.utc
            ).isoformat().replace("+00:00", "Z")
        )

        data = fetch_json(
            "WINDFOR",
            {
                "publishDateTimeFrom": publish_from,
                "publishDateTimeTo": publish_to,
            },
        )

        for row in data:
            if not row.get("startTime") or not row.get("publishTime"):
                continue

            try:
                generation = float(row["generation"])
            except (KeyError, TypeError, ValueError):
                continue

            rows.append({
                "startTime": row["startTime"],
                "publishTime": row["publishTime"],
                "generation": generation,
            })

        current = window_end

    # Deduplicate repeated boundary records.
    unique = {}

    for row in rows:
        key = (row["startTime"], row["publishTime"])
        unique[key] = row

    return list(unique.values())