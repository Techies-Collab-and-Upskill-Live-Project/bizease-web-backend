from accounts import views
from django.urls import path

urlpatterns = [
	path('', views.ProfileView.as_view(), name="user-account-details"),
	path('signup', views.SignUpView.as_view(), name="signup"),
	path('login', views.LoginView.as_view(), name="login"),
	# path('logout', views.LogoutView.as_view())
]