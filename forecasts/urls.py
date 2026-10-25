from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("forecasts/", views.forecasts_list, name="forecasts"),
    path("accuracy/", views.accuracy, name="accuracy"),
]