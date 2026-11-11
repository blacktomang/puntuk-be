"""Development-only OpenAPI document and Swagger UI shell."""

from __future__ import annotations

import json

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse

OPENAPI_DOCUMENT: dict[str, object] = {
    "openapi": "3.0.3",
    "info": {
        "title": "puntuk-be preview API",
        "version": "0.1.0",
        "description": "Optional authenticated metadata enrichment for stop-tumpuk.",
    },
    "servers": [{"url": "/"}],
    "tags": [
        {"name": "health", "description": "Operational health checks."},
        {"name": "auth", "description": "Local session and account access."},
        {"name": "previews", "description": "Authenticated URL preview enrichment."},
    ],
    "paths": {
        "/healthz": {
            "get": {
                "tags": ["health"],
                "summary": "Health check",
                "responses": {"200": {"description": "Service is healthy."}},
            }
        },
        "/v1/auth/csrf": {
            "get": {
                "tags": ["auth"],
                "summary": "Issue a CSRF token for browser session requests",
                "responses": {"200": {"$ref": "#/components/responses/CsrfToken"}},
            }
        },
        "/v1/auth/register": {
            "post": {
                "tags": ["auth"],
                "summary": "Create a local account and start a session",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/RegisterRequest"}
                        }
                    },
                },
                "responses": {
                    "201": {"$ref": "#/components/responses/UserSession"},
                    "400": {"$ref": "#/components/responses/ValidationError"},
                },
            }
        },
        "/v1/auth/login": {
            "post": {
                "tags": ["auth"],
                "summary": "Start a username/password session",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/LoginRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {"$ref": "#/components/responses/UserSession"},
                    "400": {"$ref": "#/components/responses/ValidationError"},
                },
            }
        },
        "/v1/auth/logout": {
            "post": {
                "tags": ["auth"],
                "summary": "End the current session",
                "security": [{"sessionCookie": []}],
                "responses": {
                    "204": {"description": "Session ended."},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                },
            }
        },
        "/v1/auth/session": {
            "get": {
                "tags": ["auth"],
                "summary": "Read current session state",
                "responses": {"200": {"$ref": "#/components/responses/SessionState"}},
            }
        },
        "/v1/auth/google/link": {
            "get": {
                "tags": ["auth"],
                "summary": "Start explicit Google account linking",
                "security": [{"sessionCookie": []}],
                "responses": {
                    "302": {"description": "Redirect to Google OAuth."},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                },
            }
        },
        "/v1/auth/password-reset": {
            "post": {
                "tags": ["auth"],
                "summary": "Request a password-reset email",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PasswordResetRequest"}
                        }
                    },
                },
                "responses": {
                    "204": {"description": "Request accepted."},
                    "400": {"$ref": "#/components/responses/ValidationError"},
                },
            }
        },
        "/v1/auth/password-reset/{uidb64}/{token}": {
            "post": {
                "tags": ["auth"],
                "summary": "Confirm a password reset",
                "parameters": [
                    {
                        "name": "uidb64",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {"name": "token", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PasswordResetConfirm"}
                        }
                    },
                },
                "responses": {
                    "204": {"description": "Password changed."},
                    "400": {"$ref": "#/components/responses/ValidationError"},
                },
            }
        },
        "/v1/previews": {
            "post": {
                "tags": ["previews"],
                "summary": "Extract safe metadata and an optional duration estimate",
                "security": [{"sessionCookie": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PreviewRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {"$ref": "#/components/responses/PreviewResponse"},
                    "400": {"$ref": "#/components/responses/ValidationError"},
                    "403": {"$ref": "#/components/responses/Forbidden"},
                    "429": {"description": "Rate limit exceeded."},
                },
            }
        },
    },
    "components": {
        "securitySchemes": {
            "sessionCookie": {"type": "apiKey", "in": "cookie", "name": "sessionid"}
        },
        "schemas": {
            "RegisterRequest": {
                "type": "object",
                "required": ["username", "email", "password"],
                "properties": {
                    "username": {"type": "string", "maxLength": 150},
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string", "format": "password"},
                },
            },
            "LoginRequest": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string", "format": "password"},
                },
            },
            "PasswordResetRequest": {
                "type": "object",
                "required": ["email"],
                "properties": {"email": {"type": "string", "format": "email"}},
            },
            "PasswordResetConfirm": {
                "type": "object",
                "required": ["password"],
                "properties": {"password": {"type": "string", "format": "password"}},
            },
            "PreviewRequest": {
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "pattern": "^https?://",
                        "maxLength": 2048,
                    }
                },
            },
            "User": {
                "type": "object",
                "required": ["username", "email"],
                "properties": {
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                },
            },
            "SessionState": {
                "type": "object",
                "required": ["authenticated"],
                "properties": {
                    "authenticated": {"type": "boolean"},
                    "user": {"$ref": "#/components/schemas/User"},
                },
            },
            "Duration": {
                "type": "object",
                "required": ["seconds", "provenance", "completeness"],
                "properties": {
                    "seconds": {"type": ["integer", "null"], "minimum": 0},
                    "provenance": {
                        "type": "string",
                        "enum": ["api-runtime", "publisher-estimate", "word-count", "unknown"],
                    },
                    "completeness": {"type": "string", "enum": ["full", "partial", "unknown"]},
                },
            },
            "PreviewResponse": {
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {"type": "string", "enum": ["available", "unavailable"]},
                    "finalUrl": {"type": "string", "format": "uri"},
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "thumbnailUrl": {"type": ["string", "null"], "format": "uri"},
                    "type": {"type": "string", "enum": ["article", "video"]},
                    "duration": {"$ref": "#/components/schemas/Duration"},
                    "reason": {"type": "string"},
                },
            },
        },
        "responses": {
            "CsrfToken": {
                "description": "CSRF token issued and stored in the csrftoken cookie.",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["csrfToken"],
                            "properties": {"csrfToken": {"type": "string"}},
                        }
                    }
                },
            },
            "UserSession": {
                "description": "Authenticated user session.",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["user"],
                            "properties": {"user": {"$ref": "#/components/schemas/User"}},
                        }
                    }
                },
            },
            "SessionState": {
                "description": "Current browser session.",
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/SessionState"}}
                },
            },
            "PreviewResponse": {
                "description": "Safe partial preview or stable unavailable result.",
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/PreviewResponse"}}
                },
            },
            "ValidationError": {"description": "Request validation failed."},
            "Forbidden": {"description": "Authentication or CSRF required."},
        },
    },
}


def _development_only() -> None:
    if not settings.DEBUG:
        raise Http404


def openapi_json(_: object) -> JsonResponse:
    _development_only()
    return JsonResponse(OPENAPI_DOCUMENT)


def swagger_ui(_: object) -> HttpResponse:
    _development_only()
    document_url = "/swagger/openapi.json"
    config = json.dumps(document_url)
    html = f"""<!doctype html>
<html><head><title>puntuk-be Swagger UI</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></head>
<body><div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>window.onload = () => SwaggerUIBundle({{url: {config}, dom_id: '#swagger-ui'}});</script>
</body></html>"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")
