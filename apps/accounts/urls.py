from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("register", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("session", views.SessionView.as_view(), name="session"),
    path("password-reset", views.PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/<str:uidb64>/<str:token>",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
