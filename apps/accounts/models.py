from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Initial account shape; username and recovery email are unique."""

    email = models.EmailField("email address", unique=True)
