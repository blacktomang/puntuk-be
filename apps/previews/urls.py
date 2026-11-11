from django.urls import path

from apps.previews.views import PreviewView

urlpatterns = [path("previews", PreviewView.as_view(), name="preview")]
