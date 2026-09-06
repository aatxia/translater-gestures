# PROJECT STATUS

Останнє оновлення: Phase 3 complete.

## Що вже є

- Репозиторій `aatxia/translater-gestures` — на момент старту був **порожнім** (без коду).
- Тепер створено:
  - повне дерево директорій monorepo (`frontend/`, `backend/`, `ml/`, `avatar/`, `data/`,
    `models/`, `scripts/`, `tests/`, `docs/`, `docker/`, `configs/`, `experiments/`);
  - `README.md` з інструкціями встановлення та roadmap;
  - `docs/architecture.md` з детальною архітектурою і принципами взаємозамінності компонентів;
  - `.env.example` з усіма конфігурованими параметрами (camera, WS, ML, NLP, TTS/STT, privacy);
  - `.gitignore` (виключає venv/node_modules/checkpoints/сирі відео/секрети);
  - `docker-compose.yml` — мінімальний skeleton (backend+frontend), без GPU/production
    ускладнень, поки локальний pipeline не запрацює.

## Чого не вистачає (наступні кроки)

- Робочого коду немає — жодного backend endpoint, жодного frontend компонента, жодної ML моделі.
  Це очікувано: Phase 1 = тільки repo + architecture, за правилами майстер-промпту.
- Немає ще:
  - FastAPI застосунку (Phase 2);
  - Next.js застосунку (Phase 3);
  - camera hook (Phase 4);
  - WebSocket protocol implementation (Phase 5);
  - MediaPipe pipeline (Phase 6-7);
  - dataset (Phase 8) — **зовнішня залежність**: потрібен реальний відео-датасет УЖМ з
    signer_id розміткою; без нього тренування baseline моделі неможливе. Буде використано
    synthetic/debug dataset лише для перевірки інфраструктури, чітко позначений як DEMO MODE.

## Технології (зафіксовано)

- Frontend: Next.js + TypeScript + Tailwind + WebSocket + WebRTC + Three.js
- Backend: Python 3.12 + FastAPI + Pydantic + WebSocket
- ML: MediaPipe + PyTorch (BiLSTM/GRU → Transformer) + HF Transformers + Video-JEPA (experimental)
- Середовище розробки: локальна машина (Cursor) для коду; Google Colab (GPU) для тренування моделей,
  checkpoint переноситься в `models/checkpoints/`.

## Environment audit (виконано при старті)

| Компонент | Статус |
|---|---|
| OS | Ubuntu 24.04 LTS |
| Python | 3.12.3 |
| Node.js | 22.22.2 |
| npm | 10.9.7 |
| Git | 2.43.0 |
| GPU / CUDA | відсутній у поточному dev-середовищі — тренування виноситься в Google Colab |
| PyTorch | не встановлений локально (буде встановлено в Phase 6/9 разом з ml/requirements.txt) |
| Docker | відсутній у поточному sandbox; Dockerfile'и готуються заздалегідь для локальної машини користувача |

## PHASE 2 — Backend FastAPI (COMPLETE)

Створено робочий FastAPI застосунок:

- `backend/app/main.py` — FastAPI app, CORS, lifespan logging, router registration.
- `backend/app/core/config.py` — Pydantic Settings, читає `.env`, нічого не захардкожено.
- `backend/app/core/logging.py` — structured logging; за дизайном ЗАБОРОНЕНО логувати сирі
  відео/фрейми (тільки метадані: FPS, latency, confidence, connection events, errors).
- `backend/app/api/routes/health.py` + `backend/app/schemas/health.py` — `/health` endpoint,
  чесно повертає `ml_pipeline_status: "not_implemented"` (жодної фейкової готовності).
- `backend/app/services/{inference,translation,speech,avatar}_service.py` — абстрактні
  інтерфейси (`InferenceService`, `TranslationService`, `TextToSpeech`, `SpeechRecognizer`,
  `AvatarService`) для майбутньої взаємозамінності реалізацій. Кожен має
  "NotConfigured"-реалізацію, яка **явно кидає типізовану помилку** замість фейкового
  результату — відповідно до правила "НЕ РОБИ FAKE AI".
- `backend/tests/test_health.py`, `backend/tests/test_services_honesty.py` — 7 тестів,
  включно з перевіркою, що сервіси чесно відмовляють у роботі, поки немає реального ML/NLP.
- `docker/backend.Dockerfile`.

**Перевірено наживо:**
- `pytest`: 7 passed, 0 failed, 0 warnings.
- `ruff check`: All checks passed.
- Сервер піднятий (`uvicorn app.main:app`), `GET /health` → `200 OK` з коректним JSON,
  `GET /docs` (OpenAPI) → `200 OK`.

**Known limitations:** `/health` навмисно показує `ml_pipeline_status: not_implemented` —
це очікувано і буде змінено на `demo_mode`/`ready` у Phase 9-10.

## PHASE 3 — Frontend Next.js (COMPLETE)

Створено робочий Next.js застосунок (App Router, TypeScript strict, Tailwind):

- `app/layout.tsx` — shared header/nav, `app/page.tsx` — головна, `app/translator/page.tsx` —
  каркас екрану перекладача (камера / переклад / текст→жести / avatar блоки, кожен чітко
  позначений, у якій фазі буде підключений — без фейкової функціональності).
- `components/ConnectionStatus/` — живий health-check до backend `/health` кожні 5с, з тестами
  (успіх/недоступність backend), 2/2 passed.
- `lib/api.ts`, `types/api.ts` — типізований API-клієнт; `ServerMessage`/`FrameMessage` типи для
  WebSocket protocol вже описані наперед (Phase 5 їх використає, single source of truth).
- `docker/frontend.Dockerfile`.

**Перевірено наживо:**
- `tsc --noEmit`: 0 помилок.
- `eslint`: 0 помилок, 0 warnings (виправлено конфлікт `eslint-config-next` 16.x з flat-config —
  прибрано застарілий `FlatCompat`, `<a>` замінено на `next/link`).
- `vitest run`: 2 passed.
- `next build`: успішний production build (`/`, `/translator`, `/_not-found` — усі static).
- **E2E наживо**: backend (`uvicorn`, порт 8000) + frontend (`next dev`, порт 3000) підняті
  одночасно, `/` і `/translator` віддають `200 OK`, ConnectionStatus реально показує
  `Connected · model: lstm · ML pipeline: not_implemented` через живий `/health` запит.

**Known limitations:** камера, WebSocket-стрім, розпізнавання, avatar — усі UI-блоки для них
є, але позначені як "буде підключено в Phase N" (не приховано, чітко видно користувачу).

## Наступна фаза

**PHASE 4 — Camera**: `useCamera` hook (getUserMedia, preview, start/stop, permission/error
handling, configurable FPS 10-15 та роздільна здатність 640x480), підключений до
`components/Camera/` на сторінці `/translator` замість поточного плейсхолдера.
