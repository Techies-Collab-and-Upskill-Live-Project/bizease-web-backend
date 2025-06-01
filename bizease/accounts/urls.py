from accounts import views
from django.urls import path

urlpatterns = [
	path('', views.ProfileView.as_view()),
	path('signup', views.SignUpView.as_view()),
	path('login', views.LoginView.as_view()),
	# path('logout', views.LogoutView.as_view())
]