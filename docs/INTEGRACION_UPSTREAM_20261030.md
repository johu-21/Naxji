# Integración del repositorio original en Leonardo-2-1/NAXJI

Fecha: 2026-10-30. Destino solicitado: rama `main` de
`https://github.com/Leonardo-2-1/NAXJI.git`.

Se integra `origin/main` (`246b9f5`) sobre la versión local `d1c8a2c`,
conservando ambos historiales. Respaldo local: `respaldo/antes-pmv2-20261030`.
Los cuatro commits entrantes aportan validaciones PMV1, trazabilidad y evaluación
del predictor, documentación de auditoría y PMV2 documental/RAG.

## Resolución y compatibilidad

- `.env.example`, `src/infrastructure/configuration/settings.py` y `src/main.py`:
  conflictos resueltos conservando la configuración RAG y las protecciones locales.
- `src/infrastructure/configuration/container.py` y
  `src/adapters/out/ai/embeddings_ollama.py`: BasicAuth del backend también se
  transmite a `/api/embed`. Se exige el par completo, se rechazan credenciales
  en la URL y no se siguen redirecciones. Sin credenciales se mantiene Ollama local.
- `tests/test_embeddings_auth.py`: 13 casos comprueban inyección desde el
  contenedor, ausencia/presencia de autenticación, configuración incompleta,
  URL inválida, errores sanitizados y redirecciones sin acceso a servicios reales.
- `requirements.txt` incluye PDF y multipart, además de las dependencias previas;
  `requirements-pmv2.txt` lo referencia para evitar instalaciones divergentes.
  Se instalaron únicamente `pypdf` y `python-multipart` en `.venv`.
- `docs/PMV2_GUIA_EJECUCION.md`: instalación coherente con Railway, BasicAuth
  para ambos adaptadores y cookie `SameSite=None; Secure; HttpOnly` para el
  despliegue temporal Pages + Railway. Se mantienen controles Origin,
  X-NAXJI-Client y CORS explícito. Los módulos originales de Auth no cambian.

## Verificación de esta integración

Comandos ejecutados desde la raíz con `.venv/Scripts/python.exe` y npm local.
Para pytest se usó un directorio temporal único dentro de `venv`:

```powershell
$testTemp = Join-Path 'venv' ('pytest-pmv2-final-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m pytest -q -rs -p no:cacheprovider --basetemp $testTemp
npm.cmd run test:frontend
npm.cmd run lint
npm.cmd run build
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Resultados reales:

- Pytest final: `298 passed, 76 skipped, 1 warning in 24.40s` (salida 0).
  Advertencia de deprecación de Starlette TestClient con httpx.
- La primera ejecución produjo `6 failed, 292 passed, 76 skipped`: la prueba nueva
  intentaba leer `ErrorServicio.mensaje_publico`, atributo que solo existe en
  `ErrorGeneracion`. Se corrigió para comprobar `str(error)`, que es el detalle
  público usado por FastAPI, y se repitió toda la suite con el resultado anterior.
- Frontend: `tests 52`, `pass 52`, `fail 0`, `skipped 0`,
  `duration_ms 207793.8774` (salida 0). Incluye carga documental, error recuperable,
  reintento y fuentes por versión mediante dobles HTTP.
- ESLint: salida 0, sin errores.
- Vite: salida 0, `109 modules transformed`, `built in 1.46s`.
- Dependencias: `No broken requirements found.`
- `git diff --check` sin incidencias. No hay marcadores de conflicto en código.
- Revisión de 93 archivos del cambio: sin coincidencias con secretos privados
  locales ni patrones de tokens/llaves revisados. `.env`, `.env.local` y
  `.env.auth-test` están ignorados y no versionados. No se modificaron.

## Alcance de las evidencias

Las 76 pruebas omitidas requieren servicios reales u opciones explícitas. Esta
sesión no ejecutó migraciones, semillas, operaciones institucionales, login real,
Storage real ni llamadas a Ollama/ngrok. No acredita activación de RAG en Railway.

RAG permanece desactivado por defecto (`NAXJI_RAG_ENABLED=false`). La activación
requiere revisar y aplicar las migraciones en el entorno elegido, habilitar un
bucket privado, configurar el modelo de embeddings y validar permisos. En
particular, la migración PMV2 revoca SELECT directo de `versiones_informe` a los
roles anon/authenticated; debe revisarse antes de aplicarla a una base compartida.

Los archivos de `docs/evidencias/pmv2` y `docs/evidencias/auditoria-final` llegan
del repositorio original y describen ejecuciones anteriores del autor. No son
ejecuciones nuevas de esta integración; los resultados nuevos figuran arriba.
