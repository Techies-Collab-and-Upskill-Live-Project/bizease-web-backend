from django.urls import path
from .views import ReportsOverview


urlpatterns = [
    path('', ReportsOverview.as_view(), name='report'),
]
