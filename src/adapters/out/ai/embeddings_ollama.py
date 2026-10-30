import math

import httpx

from src.domain.services.errores import ErrorServicio
from src.infrastructure.configuration.settings import validar_conexion_ollama


class EmbeddingsOllama:
    def __init__(self, base_url, modelo="bge-m3:567m", dimension=1024, timeout=120, transport=None,
                 *, username=None, password=None):
        validar_conexion_ollama(base_url, username, password)
        self._auth = httpx.BasicAuth(username, password) if username and password else None
        self.base_url, self.modelo, self.dimension = base_url.rstrip("/"), modelo, dimension
        self.timeout, self.transport = timeout, transport

    def codificar(self, textos):
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport, follow_redirects=False,
                              trust_env=False, auth=self._auth) as client:
                response = client.post(self.base_url + "/api/embed",
                                       json={"model": self.modelo, "input": textos, "truncate": False})
                response.raise_for_status()
                vectores = response.json()["embeddings"]
            if len(vectores) != len(textos):
                raise ValueError()
            resultado = []
            for vector in vectores:
                if len(vector) != self.dimension or any(isinstance(x, bool) or not isinstance(x, (int, float))
                                                       or not math.isfinite(x) for x in vector):
                    raise ValueError()
                norma = math.sqrt(sum(x*x for x in vector))
                if norma <= 0:
                    raise ValueError()
                resultado.append([x/norma for x in vector])
            return resultado
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise ErrorServicio("EMBEDDINGS_NO_DISPONIBLES",
                                "No se pudieron obtener embeddings válidos. Verifique Ollama, modelo y dimensión; reintente.") from None
