import calendar
import os
import re
from datetime import date, timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .services.elexon import (
    fetch_actuals,
    fetch_forecasts,
    ElexonAPIError,
)
from .services.analytics import build_forecast_comparison


def get_month_range(month):
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("month must use YYYY-MM format")

    year, month_number = map(int, month.split("-"))

    if not 1 <= month_number <= 12:
        raise ValueError("Invalid month")

    first_day = date(year, month_number, 1)
    last_day = date(
        year,
        month_number,
        calendar.monthrange(year, month_number)[1],
    )

    return first_day.isoformat(), (
        last_day + timedelta(days=1)
    ).isoformat()


def load_dashboard(month):
    cache_key = f"wind-dashboard-{month}"

    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    month_start, next_month = get_month_range(month)

    actuals = fetch_actuals(month_start, next_month)
    forecasts = fetch_forecasts(month_start, next_month)

    lead_hours = int(os.getenv("DECISION_LEAD_HOURS", "24"))

    if not 0 <= lead_hours <= 168:
        raise ValueError(
            "DECISION_LEAD_HOURS must be between 0 and 168"
        )

    data = build_forecast_comparison(
        actuals,
        forecasts,
        month_start,
        next_month,
        decision_lead_hours=lead_hours,
    )

    cache.set(cache_key, data, 60 * 60)
    return data
def api_error(exc):
    return Response(
        {"error": str(exc)},
        status=status.HTTP_502_BAD_GATEWAY,
    )


@api_view(["GET"])
def health(request):
    return Response({
        "status": "ok",
        "service": "wind-forecast-api",
    })


@api_view(["GET"])
def dashboard(request):
    month = request.query_params.get("month", "2026-01")

    try:
        data = load_dashboard(month)

        try:
            limit = int(request.query_params.get("limit", "100"))
        except ValueError:
            return Response(
                {"error": "limit must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 1 <= limit <= 1000:
            return Response(
                {"error": "limit must be between 1 and 1000"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = data.copy()
        response_data["rows"] = data["rows"][:limit]
        response_data["returnedRows"] = len(response_data["rows"])

        return Response(response_data)

    except ValueError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ElexonAPIError as exc:
        return api_error(exc)
@api_view(["GET"])
def forecasts_list(request):
    month = request.query_params.get("month", "2026-01")

    try:
        data = load_dashboard(month)

        return Response({
            "month": data["month"],
            "count": len(data["rows"]),
            "results": data["rows"],
        })
    except ValueError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ElexonAPIError as exc:
        return api_error(exc)


@api_view(["GET"])
def accuracy(request):
    month = request.query_params.get("month", "2026-01")

    try:
        data = load_dashboard(month)

        return Response({
            "month": data["month"],
            "decisionLeadHours": data["decisionLeadHours"],
            "intervalCount": data["intervalCount"],
            "scoredIntervalCount": data["scoredIntervalCount"],
            "missingForecastCount": data["missingForecastCount"],
            "metrics": data["metrics"],
        })
    except ValueError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ElexonAPIError as exc:
        return api_error(exc)