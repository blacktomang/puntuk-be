import json
from typing import Any, cast

import pytest
from django.http import HttpResponse
from django.test import Client


@pytest.mark.django_db
def test_healthz_returns_ok() -> None:
    client = cast(Any, Client())
    response = cast(HttpResponse, client.get("/healthz"))

    assert response.status_code == 200
    assert json.loads(response.content) == {"status": "ok"}
