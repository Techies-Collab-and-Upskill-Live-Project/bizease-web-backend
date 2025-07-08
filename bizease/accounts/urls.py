from accounts import views
from django.urls import path

urlpatterns = [
	path('', views.ProfileView.as_view(), name="user-account-details"),
	path('signup', views.SignUpView.as_view(), name="signup"),
	path('login', views.LoginView.as_view(), name="login"),
    path('logout', views.LogoutView.as_view()),
    path('profile', views.ProfileView.as_view()),
    path('verify-email/<uidb64>/<token>/', views.EmailVerificationView.as_view()),
    path('password-reset', views.PasswordResetRequestView.as_view()),
    path('password-reset-confirm', views.PasswordResetConfirmView.as_view()),
    path('google-login/',views.GoogleAuthView.as_view()),  # Optional
]