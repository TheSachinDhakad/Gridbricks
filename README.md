# UK Wind Forecast Analytics

A Django REST Framework API for analysing UK national wind generation
forecasts and actual generation using Elexon BMRS data.

## Features

- Wind generation actuals from FUELHH
- Wind generation forecasts from WINDFOR
- Latest forecast available before the configured decision cutoff
- Forecast versus actual comparison
- MAE, RMSE, mean bias error and percentage MAE
- REST APIs for a React dashboard
- Docker support

## Technology

- Python
- Django REST Framework
- Elexon BMRS API
- Docker
- SQLite for Django's default database

## API Endpoints

- GET /api/health/
- GET /api/dashboard/?month=2026-01
- GET /api/forecasts/?month=2026-01
- GET /api/accuracy/?month=2026-01

## Run Locally

Install dependencies using your preferred Python installation method,
then run:

    python3 manage.py migrate
    python3 manage.py runserver 8000

## Run with Docker

    docker compose up --build

## Forecast Accuracy

Error = forecast generation - actual generation.

- MAE: average absolute forecast error
- RMSE: root mean squared error
- MBE: mean forecast bias

The initial implementation assumes a 24-hour decision lead time.
Confirm the exact cutoff with the client before using the output
for real procurement decisions.

## Data Sources

FUELHH:
https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream

WINDFOR:
https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream

## AI Disclosure

AI tools were used to assist with the initial backend structure,
API integration code, analytics implementation and documentation.
The implementation and API results must be validated before production use.

## Deployment

Frontend: Add your Vercel URL here.
Backend: Add your deployed API URL here.
GitHub: Add your public repository URL here.
Demo video: Add your unlisted YouTube URL here.