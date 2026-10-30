import base64
import logging
from unittest.mock import Mock

import httpx
import pytest

from src.adapters.out.ai.embeddings_ollama import EmbeddingsOllama
from src.domain.services.errores import ErrorServicio
from src.infrastructure.configuration import database
from src.infrastructure.configuration.container import Container
from src.infrastructure.configuration.rag import RagSettings
from src.infrastructure.configuration.settings import Settings


@pytest.mark.parametrize("authenticated", [False, True])
def test_embeddings_auth_inyectada_desde_contenedor(monkeypatch, authenticated, caplog):
    # Solo valores ficticios; ninguna conexion real a PostgreSQL/Storage/Ollama.
    username = "TEST_USER" if authenticated else None
    password = "TEST_PASSWORD" if authenticated else None
    monkeypatch.setattr(database, "environment", lambda: {
        "NAXJI_SUPABASE_URL": "https://storage.example.invalid",
        "NAXJI_STORAGE_SERVICE_KEY": "TEST_STORAGE_KEY",
    })
    db = Mock()
    container = Container(Settings(persistence_mode="postgres", auth_mode="disabled",
        ollama_base_url="https://tunnel.example.invalid", ollama_username=username,
        ollama_password=password, rag=RagSettings(enabled=True)),
        database_settings=db, predictor=Mock())
    adapter = container.documentos.embeddings
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"embeddings": [[1.0] + [0.0] * 1023]})

    adapter.transport = httpx.MockTransport(respond)
    caplog.set_level(logging.DEBUG)
    assert adapter.codificar(["texto"])[0][0] == 1.0
    request, = requests
    assert str(request.url) == "https://tunnel.example.invalid/api/embed"
    if authenticated:
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        assert request.headers["authorization"] == "Basic " + encoded
        public = str(request.url) + request.content.decode() + caplog.text + repr(adapter)
        assert all(secret not in public for secret in (username, password, encoded))
    else:
        assert "authorization" not in request.headers
    db.connect.assert_not_called()


@pytest.mark.parametrize("username,password", [("TEST_USER", None), (None, "TEST_PASSWORD"),
                                              ("TEST_USER", ""), ("", "TEST_PASSWORD")])
def test_embeddings_auth_incompleta(username, password):
    with pytest.raises(ValueError, match="deben configurarse juntas") as error:
        EmbeddingsOllama("https://tunnel.example.invalid", username=username, password=password)
    assert "TEST_" not in str(error.value)


def test_embeddings_rechaza_credenciales_en_url():
    with pytest.raises(ValueError, match="sin credenciales") as error:
        EmbeddingsOllama("https://TEST_USER:TEST_PASSWORD@tunnel.example.invalid")
    assert "TEST_" not in str(error.value)


@pytest.mark.parametrize("status", [401, 403, 302, 307, 308, "network"])
def test_embeddings_errores_sanitizados_y_sin_redirecciones(status, caplog):
    requests = []
    username, password = "TEST_PRIVATE_USER", "TEST_PRIVATE_PASSWORD"
    encoded = base64.b64encode(f"{username}:{password}".encode()).decode()

    def respond(request):
        requests.append(request)
        private = f"{username} {password} {encoded}"
        if status == "network":
            raise httpx.ConnectError(private)
        return httpx.Response(status, text=private,
                              headers={"Location": "https://other.example.invalid/api/embed"})

    adapter = EmbeddingsOllama("https://tunnel.example.invalid", username=username,
                              password=password, transport=httpx.MockTransport(respond))
    caplog.set_level(logging.DEBUG)
    with pytest.raises(ErrorServicio) as error:
        adapter.codificar(["texto"])
    assert error.value.codigo == "EMBEDDINGS_NO_DISPONIBLES"
    assert len(requests) == 1
    public = str(error.value) + caplog.text
    assert all(secret not in public for secret in (username, password, encoded))
