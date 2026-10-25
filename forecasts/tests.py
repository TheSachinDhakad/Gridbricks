from django.test import SimpleTestCase
from .services.analytics import build_forecast_comparison


class ForecastAnalyticsTests(SimpleTestCase):

    def test_uses_latest_forecast_before_cutoff(self):
        actuals = [{
            "startTime": "2026-01-02T12:00:00Z",
            "generation": 100,
        }]

        forecasts = [
            {
                "startTime": "2026-01-02T12:00:00Z",
                "publishTime": "2026-01-01T10:00:00Z",
                "generation": 90,
            },
            {
                "startTime": "2026-01-02T12:00:00Z",
                "publishTime": "2026-01-01T11:00:00Z",
                "generation": 95,
            },
            {
                "startTime": "2026-01-02T12:00:00Z",
                "publishTime": "2026-01-01T13:00:00Z",
                "generation": 110,
            },
        ]

        result = build_forecast_comparison(
            actuals,
            forecasts,
            "2026-01-01",
            "2026-02-01",
        )

        row = result["rows"][0]

        self.assertEqual(row["forecastGeneration"], 95)
        self.assertEqual(row["actualGeneration"], 100)
        self.assertEqual(row["errorMW"], -5)
        self.assertEqual(result["scoredIntervalCount"], 1)

    def test_missing_forecast(self):
        result = build_forecast_comparison(
            [{
                "startTime": "2026-01-02T12:00:00Z",
                "generation": 100,
            }],
            [],
            "2026-01-01",
            "2026-02-01",
        )

        self.assertEqual(result["missingForecastCount"], 1)
        self.assertIsNone(result["metrics"]["maeMW"])