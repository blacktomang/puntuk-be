# pyright: basic

from rest_framework import serializers


class PreviewRequestSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=2_048)
