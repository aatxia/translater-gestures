# PROJECT STATUS

Останнє оновлення: Phase 7 complete.

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

## PHASE 4 — Camera (COMPLETE)

Реалізовано робочий доступ до камери браузера:

- `hooks/useCamera.ts` — `getUserMedia`, стани (`idle` / `requesting_permission` /
  `streaming` / `stopped` / `error`), коректний permission/error handling
  (`NotAllowedError` → permission_denied, `NotFoundError` → no_camera_found,
  `NotReadableError` → camera_in_use, відсутність `mediaDevices` → unsupported),
  configurable FPS (clamp 10-15, за замовчуванням 12) і роздільна здатність (640×480 default,
  через `NEXT_PUBLIC_CAMERA_*` env vars), cleanup (зупинка треків) при unmount/stop.
- Вбудований, але поки не активований, controlled frame-capture loop (`onFrame` callback,
  canvas→JPEG dataURL) — за принципом "не відправляй кожен frame безконтрольно": він нічого
  нікуди не шле сам по собі, чекає підключення до WebSocket клієнта в Phase 5.
- `components/Camera/Camera.tsx` — preview, кнопки Увімкнути/Вимкнути, живий статус, помилки
  українською. Підключено до `/translator` замість плейсхолдера.
- `frontend/.env.example` — окремий env-файл для `npm run dev` (Next.js читає `.env.local` з
  директорії frontend, а не з кореня репо; докер-контейнер продовжує брати кореневий `.env`).

**Перевірено наживо:** `tsc --noEmit` — 0 помилок, `eslint` — 0 помилок/warnings,
`vitest run` — 10/10 passed (5 тестів hook'а: permission granted/denied/unsupported/stop/fps-clamp;
3 тести компонента: inactive/streaming/error стани; +2 старих ConnectionStatus), `next build` —
успішний.

**Known limitations:** frame-capture loop існує, але `onFrame` ніде ще не передається (Phase 5
підключить його до WebSocket клієнта). Реальну камеру в headless-пісочниці перевірити неможливо
(немає фізичного пристрою) — перевірено через мокнутий `getUserMedia` у тестах; **рекомендую
тобі підтвердити на своїй машині в браузері**, що камера реально вмикається на `/translator`.

## PHASE 5 — WebSocket (COMPLETE)

Реалізовано real-time WebSocket protocol між frontend і backend:

**Backend** (`backend/websocket/{protocol,manager,handler}.py`, розкладені за структурою з
розділу 4 ТЗ, окремо від `app/`):
- `protocol.py` — Pydantic-схеми `FrameMessage` (client→server), `PredictionMessage` /
  `ErrorMessage` / `ConnectionMessage` (server→client), `parse_client_message()` з чіткими
  помилками замість краху з'єднання.
- `manager.py` — `ConnectionManager`, трекає активні з'єднання, логує connect/disconnect
  (без сирих даних — тільки id/timestamp/count, за правилом приватності).
- `handler.py` — головний message loop: перевірка типу/розміру повідомлення
  (`WS_MAX_MESSAGE_SIZE_BYTES`, закриває з'єднання код 1009 при перевищенні), rate limiting
  (`WS_MAX_FPS`, зайві кадри відхиляються з чіткою помилкою, не тихо), і — оскільки ML pipeline
  ще не існує (Phase 6-10) — чесна `{"type": "error", "message": "...not implemented yet..."}`
  відповідь на кожен валідний кадр, БЕЗ фейкового prediction.
- Підключено в `app/main.py` через `app/api/websocket/routes.py` (`/ws` endpoint).

**Frontend**:
- `hooks/useWebSocket.ts` — підключення, статуси (`idle`/`connecting`/`open`/`closed`/`error`),
  `sendFrame()` (шле тільки коли `readyState === OPEN`), парсинг вхідних `ServerMessage` з
  безпечним ігноруванням некоректного JSON.
- `components/Camera/Camera.tsx` — додано опціональний `onFrame` проп (не ламає Phase 4 API).
- `components/Translator/TranslatorView.tsx` — новий client-компонент, який з'єднує камеру з
  WebSocket (`onFrame={sendFrame}`) і показує живий статус з'єднання + останнє повідомлення
  backend замість статичного плейсхолдера. `/translator` тепер рендерить саме його.

**Перевірено наживо:**
- Backend: `pytest` — 14/14 passed (включно з 8 новими WS-тестами: connect ack, чесна
  ML-помилка на валідний кадр, invalid JSON, unknown type, missing field, rate limiting,
  oversized message → закриття з'єднання), `ruff check` — чисто.
- Frontend: `vitest` — 17/17 passed (5 нових для `useWebSocket`), `eslint`/`tsc`/`next build` —
  чисто.
- **Реальний E2E-обмін** через живий `websockets` клієнт проти запущеного `uvicorn`: connection
  ack отримано, валідний frame → чесна ML-помилка (не фейковий "вода"), невідомий тип
  повідомлення → чітка помилка без розриву з'єднання.

**Known limitations:** кадри з камери зараз реально шлються на backend, але backend поки завжди
відповідає "ML pipeline not implemented" — це очікувано і зникне в Phase 9-10.

## PHASE 6 — MediaPipe preprocessing (COMPLETE)

Реалізовано робочий CV preprocessing pipeline (`ml/preprocessing/`), використовуючи сучасний
**MediaPipe Tasks API** (`HandLandmarker`/`PoseLandmarker`/`FaceLandmarker`) — стара
`mp.solutions` більше не постачається у поточних релізах mediapipe (перевірено: pip встановив
mediapipe 1.0.1, `mp.solutions` відсутній).

- `video_reader.py` — декодування base64 JPEG (з WebSocket `frame` message, включно з
  `data:image/jpeg;base64,...` префіксом від `canvas.toDataURL()`) у BGR numpy-масив; плюс
  читання відеофайлів кадр-за-кадром для майбутнього dataset pipeline (Phase 8).
- `landmarks.py` — `LandmarkExtractor` з lazy-завантаженням лише увімкнених за `FeatureToggles`
  детекторів (hands/pose/face, розділ 9 ТЗ), чесний `ModelNotFoundError` з інструкцією, якщо
  `.task` модель не завантажена. Жодних fake-детекцій: якщо MediaPipe не бачить руку/позу/обличчя
  в кадрі — відповідне поле `None`, а не вигадане значення.
- `normalization.py` — нормалізація координат відносно тіла: hand center = wrist, pose center =
  середина плечей (індекси 11/12) + масштаб = ширина плечей (invariant до відстані до камери,
  перевірено тестом), face center = центроїд. `normalize_frame()` дає fixed-shape вивід із нулями
  там, де модальність відсутня, ПЛЮС окремий `present` dict, щоб відрізнити "0,0,0" від
  "не виявлено".
- `augmentation.py` — geometric/temporal аугментації для тренування (rotate/scale/translate/
  gaussian noise/temporal frame dropout), детерміновані через seeded `numpy.random.Generator`.
- `scripts/download_mediapipe_models.sh` — завантажує `.task` бандли (Apache 2.0, від Google) з
  офіційного джерела, з fallback на GitHub-дзеркало для hand/face, якщо `storage.googleapis.com`
  заблоковано в мережі.

**Перевірено наживо (справжній MediaPipe, не мок):**
- `hand_landmarker.task` (7.8MB) і `face_landmarker.task` (3.7MB) реально завантажені й
  перевірені: детектори завантажуються, `.detect()` на порожньому/синтетичному кадрі чесно
  повертає 0 виявлень (не fabricated result).
- `pose_landmarker.task` **не вдалося завантажити в цій пісочниці** (офіційний Google Storage
  заблокований мережевими правилами середовища, і для pose дзеркала поки не існує) — тест на
  pose коректно `SKIPPED` з чіткою причиною, а не falsely passed. **На твоїй машині/в Colab з
  нормальним доступом до інтернету офіційний URL спрацює без проблем.**
- `pytest`: 22 passed, 1 skipped (pose, з задокументованої причини), `ruff check` — чисто.

**Known limitations:** pose-детекція не верифікована наживо в цій пісочниці (лише hands/face);
код ідентичний для всіх трьох модальностей, тож ризик низький, але варто перевірити на своїй
машині після `scripts/download_mediapipe_models.sh`.

## PHASE 7 — Landmark extraction (COMPLETE)

Feature-вектори та повне підключення реального CV pipeline у WebSocket:

- `ml/features/{hands,pose,face}.py` — фіксовані feature-вектори з *обраного підмножини*
  landmarks (не всі 33/478 точок, а лише релевантні: hands — усі 21×2, pose — 8 верхньої
  частини тіла (плечі/лікті/зап'ястя/стегна), face — 24 точки для non-manual grammar markers:
  брови, очі, рот).
- `ml/features/feature_vector.py` — `FeatureConfig` + `build_feature_vector()`/
  `feature_vector_size()`, що реалізує розділ 9 ТЗ: hands-only / hands+pose / hands+pose+face
  вибирається виключно конфігом, розмір вектора змінюється автоматично (перевірено тестом).
- `configs/model.yaml` — єдине джерело для camera/model/features конфігурації експериментів.
- **`backend/websocket/handler.py` тепер реально викликає CV pipeline**: decode кадру →
  `LandmarkExtractor.extract()` (в окремому потоці через `asyncio.to_thread`, щоб не блокувати
  event loop) → `normalize_frame()` → `build_feature_vector()`. ML-помилка залишається чесною
  (Phase 9-10 ще попереду), але тепер містить РЕАЛЬНІ дані: які модальності виявлено і розмір
  feature-вектора — підготовка до debug mode (розділ 41).
- `backend/app/core/config.py` — sys.path bootstrap, щоб backend міг імпортувати сусідній `ml/`
  пакет незалежно від робочої директорії; `mediapipe_models_dir` налаштування.
- `backend/requirements.txt` тепер підключає `ml/requirements.txt` (mediapipe/opencv/numpy) —
  backend реально імпортує CV pipeline при старті.

**Перевірено наживо (справжній E2E, не мок):**
- `pytest`: ml — 29 passed/1 skipped, backend — 15/15 passed (WS-тести тепер шлють РЕАЛЬНИЙ
  JPEG замість фейкового "AAAA", перевіряють що на порожньому кадрі чесно `left_hand=False`
  тощо). `ruff check` — чисто в обох пакетах.
- Живий WebSocket-клієнт проти запущеного `uvicorn`: реальний кадр → `FRAME RESPONSE:
  {"type":"error","message":"...Landmarks were extracted: left_hand=False, right_hand=False,
  pose=False, face=False (feature vector size: 198/198)."}` — 198 = 126 (hands) + 72 (face);
  pose вимкнено локально через `FEATURES_POSE=false` (модель недоступна в цій пісочниці, див.
  Phase 6 known limitations).

**Known limitations:** локальний `.env` у цій пісочниці має `FEATURES_POSE=false`, оскільки
`pose_landmarker.task` не вдалось завантажити (Google Storage заблокований мережею sandbox).
**У `.env.example` значення за замовчуванням лишається `true`** — на твоїй машині після
`scripts/download_mediapipe_models.sh` (де офіційний URL не заблокований) все запрацює з усіма
трьома модальностями без додаткових змін.

## Наступна фаза

**PHASE 8 — Dataset pipeline**: `data/{raw,processed,annotations,splits}/`, `scripts/
create_dataset_split.py` (signer-independent train/val/test split, розділ 11 ТЗ — суворо
заборонено, щоб один signer_id був і в train, і в test), формат анотацій (розділ 10). Це
зовнішня залежність — потрібен реальний відеодатасет УЖМ з розміткою signer_id, якого поки
немає; buде створено інфраструктуру + synthetic/debug dataset лише для перевірки pipeline,
чітко позначений як DEMO MODE (розділ 40 ТЗ), doки реальний датасет не з'явиться.
