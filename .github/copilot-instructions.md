# Project Guidelines

## Code Style
- Use Python 3.10.12 features only. Do not introduce syntax that requires newer Python versions.
- Follow existing style in the repo: clear type hints, small focused functions, and logging through the standard `logging` module.
- Keep user-facing Chinese text and robot-domain terminology consistent with existing files.

## Architecture
- Keep HTTP concerns in `src/api/` and core logic in `src/services/`.
- `src/main.py` is the app composition root:
  - App startup creates exactly one `SemanticToolRouter` and stores it in `app.state`.
  - API routes are mounted under `/api/v1`.
- `src/core/config.py` is the source of truth for tool metadata:
  - `ROBOT_TOOLS_REGISTRY` defines tool schema and retrieval text.
  - `STATIC_TOOL_NAMES` defines tools that must always be available.
- Keep semantic retrieval behavior in `src/services/semantic_router.py`; do not move embedding/index logic into API handlers.

## Build and Test
- Install dependencies: `uv sync`
- Run API locally: `python src/main.py`
- Run all tests: `pytest`
- Run semantic router tests: `pytest tests/test_semantic_router.py`
- When changing retrieval logic or tool registry behavior, update/add tests in `tests/test_semantic_router.py`.

## Conventions
- Tool records in `ROBOT_TOOLS_REGISTRY` should include: `id`, `name`, `description`, `parameters`, `search_keywords`.
- API dependency providers should remain in `src/api/dependencies.py` and be wired with FastAPI `Depends`.
- Preserve the current hybrid routing contract:
  - Semantically matched tools are selected by threshold/top-k.
  - Static safety tools are always included in final prompt tools.

## Known Gotchas
- `SentenceTransformer` model loading happens at startup and may download model weights on first run; avoid re-initializing per request.
- Keep heavy initialization in lifespan startup, not endpoint functions.
- `src/services/llm_service.py` is currently empty and should be implemented before relying on end-to-end chat behavior.
- `src/models/schemas.py` is imported by `src/api/v1_chat.py`; ensure schema definitions exist and match endpoint usage.
