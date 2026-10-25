from datetime import datetime, timedelta, timezone
import math


def parse_datetime(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def build_forecast_comparison(
    actuals,
    forecasts,
    month_start,
    next_month,
    decision_lead_hours=24,
):
    start = parse_datetime(month_start + "T00:00:00Z")
    end = parse_datetime(next_month + "T00:00:00Z")

    actual_by_time = {}

    for row in actuals:
        try:
            target = parse_datetime(row["startTime"])
            generation = float(row["generation"])
        except (KeyError, TypeError, ValueError):
            continue

        if start <= target < end:
            actual_by_time[target] = generation

    forecasts_by_time = {}

    for row in forecasts:
        try:
            target = parse_datetime(row["startTime"])
            published = parse_datetime(row["publishTime"])
            generation = float(row["generation"])
        except (KeyError, TypeError, ValueError):
            continue

        if not start <= target < end:
            continue

        cutoff = target - timedelta(hours=decision_lead_hours)

        if published > cutoff:
            continue

        existing = forecasts_by_time.get(target)

        if existing is None or published > existing["published"]:
            forecasts_by_time[target] = {
                "published": published,
                "generation": generation,
            }

    rows = []

    for target in sorted(actual_by_time):
        actual = actual_by_time[target]
        selected = forecasts_by_time.get(target)

        forecast = selected["generation"] if selected else None
        error = forecast - actual if forecast is not None else None

        rows.append({
            "startTime": target.isoformat(),
            "forecastPublishTime": (
                selected["published"].isoformat()
                if selected else None
            ),
            "forecastGeneration": forecast,
            "actualGeneration": actual,
            "errorMW": error,
            "absoluteErrorMW": (
                abs(error) if error is not None else None
            ),
        })

    scored = [row for row in rows if row["errorMW"] is not None]
    errors = [row["errorMW"] for row in scored]
    count = len(scored)

    if count:
        mae = sum(abs(error) for error in errors) / count
        rmse = math.sqrt(
            sum(error * error for error in errors) / count
        )
        mbe = sum(errors) / count

        mean_actual = sum(
            row["actualGeneration"] for row in scored
        ) / count

        mae_percent = (
            mae / mean_actual * 100 if mean_actual else None
        )
    else:
        mae = rmse = mbe = mae_percent = None

    return {
        "month": month_start[:7],
        "decisionLeadHours": decision_lead_hours,
        "intervalCount": len(rows),
        "scoredIntervalCount": count,
        "missingForecastCount": len(rows) - count,
        "metrics": {
            "maeMW": mae,
            "rmseMW": rmse,
            "meanBiasErrorMW": mbe,
            "maePercentOfMeanActual": mae_percent,
        },
        "rows": rows,
    }