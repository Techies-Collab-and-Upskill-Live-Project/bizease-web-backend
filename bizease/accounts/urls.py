from accounts import views
from django.urls import path

urlpatterns = [
	path('signup', views.signup),
	path('login', views.login)
]