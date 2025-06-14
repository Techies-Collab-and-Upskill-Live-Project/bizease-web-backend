from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponseNotFound, HttpResponseServerError

urlpatterns = [
  path('admin/', admin.site.urls),
  re_path(r'^(?P<version>(v1))/accounts/', include('accounts.urls')),
  re_path(r'^(?P<version>(v1))/orders/', include('orders.urls')),
  re_path(r'^(?P<version>(v1))/inventory/', include('inventory.urls')),
  re_path(r'^(?P<version>(v1))/dashboard/', include('dashboard.urls')),
  re_path(r'^(?P<version>(v1))/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh')
]

def custom_404_view(request, exception):
  return HttpResponseNotFound('{"detail": "Resource not found"}', content_type="application/json")

def custom_500_view(request):
  return HttpResponseServerError('{"detail": "Something went wrong while trying to process your request"}', content_type="application/json")

handler404 = custom_404_view
handler500 = custom_500_view