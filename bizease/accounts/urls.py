from accounts import views
from django.urls import path
from .views import (
    SignUpView, LoginView, LogoutView, ProfileView,
    PasswordResetRequestView, PasswordResetConfirmView)

urlpatterns = [
	path('', views.ProfileView.as_view()),
	path('signup', views.SignUpView.as_view(), name='signup'),
	path('login', views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('password-reset/', PasswordResetRequestView.as_view()),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view()),
    path('google-login/',views.GoogleAuthView.as_view()),  # Optional
	
]