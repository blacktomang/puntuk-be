from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("csrf", views.CsrfTokenView.as_view(), name="csrf"),
    path("register", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("session", views.SessionView.as_view(), name="session"),
    path("google/link", views.GoogleLinkStartView.as_view(), name="google-link"),
    path("password-reset", views.PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/<str:uidb64>/<str:token>",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
