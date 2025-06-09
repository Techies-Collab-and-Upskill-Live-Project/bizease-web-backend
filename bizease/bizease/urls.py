from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
  path('admin/', admin.site.urls),
  re_path(r'^(?P<version>(v1))/accounts/', include('accounts.urls')),
  re_path(r'^(?P<version>(v1))/orders/', include('orders.urls')),
  re_path(r'^(?P<version>(v1))/inventory/', include('inventory.urls')),
  re_path(r'^(?P<version>(v1))/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh')
]
