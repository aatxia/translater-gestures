# PROJECT STATUS

Останнє оновлення: Phase 11 complete.

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

## PHASE 8 — Dataset pipeline (COMPLETE)

**Дослідження реального датасету УЖМ (перед кодом, як і планувалось):** перевірено три основні
реєстри sign-language датасетів — `sign-language-processing/datasets` (HuggingFace/TFDS),
PyPI `sign-language-datasets`, `SignLanguage-Dataset-Hub` — **жоден не містить УЖМ**. Знайдено
один реальний, свіжий (травень 2026) ресурс — **UkrSL** ("Towards a Ukrainian Continuous Sign
Language Dataset", UNLP 2026, Sobetskyi/Kosse/Kyslyi/Savchenko): 1456 кліпів (~2 години) з 6
відео Суспільного мовлення. Але це **continuous signing**, вирівняний до українського тексту
переклад дикторської мови (не ізольовані жести з gloss-міткою для класифікації), сигнерів
ймовірно лише кілька (перекладачі каналу) — не той рівень signer-різноманіття, що потрібен для
signer-independent split. Посилання на завантаження/ліцензію **не вдалось перевірити** —
`aclanthology.org` заблокований мережевою політикою цього sandbox-середовища. Висновок:
готового isolated-sign датасету УЖМ з `signer_id` для класифікації публічно не існує — це
підтверджена відсутність ресурсу, а не пропущений пошук.

Створено інфраструктуру датасету (`ml/datasets/`, `scripts/`, `docs/dataset_format.md`):

- `ml/datasets/annotation.py` — `SampleAnnotation` (sample_id/clip_path/signer_id/gloss/
  start_frame/end_frame/fps/source, розділ 10), JSONL load/write з чіткими помилками (файл +
  рядок) на некоректний рядок або дублікат `sample_id` — жоден поганий рядок не пропускається
  мовчки.
- `ml/datasets/split.py` — `signer_independent_split()` (розділ 11): призначає **цілого
  сигнера**, а не окремий семпл, в один зі spliits (greedy group-balancing за ratio,
  детерміновано за `seed`); кидає явну помилку, якщо унікальних сигнерів менше, ніж потрібно
  спліттів, замість мовчазного порожнього спліту.
- `scripts/create_dataset_split.py` — CLI, пише `data/splits/{train,val,test}.txt` +
  `split_manifest.json` (ratio/seed/signer→split, для аудиту).
- `ml/datasets/synthetic.py` (**DEMO MODE ONLY**) — генерує невеликий повністю штучний датасет
  (6 фейкових сигнерів × 5 gloss-міток), псевдовипадкові feature-послідовності з
  класо-залежним зсувом (НЕ з реального відео/MediaPipe), кожен семпл позначений
  `source="demo_synthetic"`.
- `ml/datasets/dataset.py::load_feature_sequence()` — завантажує `.npy` для
  `source="demo_synthetic"`; для будь-якого іншого `source` **явно кидає
  `NotImplementedError`** (реальні відео поки нема як декодувати — Phase 9 підключить
  `ml/preprocessing`+`ml/features` до цього шляху, коли з'явиться реальний датасет) — жодної
  фейкової підтримки.
- `scripts/generate_demo_dataset.py` — CLI-обгортка, друкує явне попередження
  "[DEMO MODE] ... This is NOT real Ukrainian Sign Language data".
- `docs/dataset_format.md` — повний опис формату анотацій, signer-independent split, і чому
  зараз лише DEMO MODE.
- `.gitignore` — `data/annotations/*` і `data/splits/*` тепер ігноруються (як і
  `data/raw`/`data/processed`): вміст завжди або згенерований локально, або з зовнішнього
  датасету, і не повинен коммітитись як частина репозиторію.

**Перевірено наживо:**
- `pytest` (`ml/`): 54 passed, 4 skipped (ті самі pose-skip з Phase 6, з задокументованої
  причини — не пов'язано з Phase 8).
- Живий E2E через CLI: `generate_demo_dataset.py` → 90 семплів (6 сигнерів × 5 gloss × 3 takes),
  `create_dataset_split.py` на них → `train: 60 (4 сигнери), val: 15 (1 сигнер), test: 15
  (1 сигнер)` — рівно 0.7/0.15/0.15 при 6 рівних сигнерах, жоден сигнер не перетнув спліти.

**Known limitations:** synthetic-датасет існує лише для перевірки інфраструктури — модель,
натренована на ньому, не розпізнає жодного реального жесту УЖМ. Реальний датасет лишається
зовнішньою залежністю; `load_feature_sequence()` для реального відео свідомо не реалізовано
(Phase 9).

## PHASE 9 — Baseline model training (COMPLETE)

Реалізовано повний тренувальний pipeline (`ml/models/`, `ml/training/`), однаково запускний
локально й у Google Colab, без Colab-специфічних хаків:

- `ml/models/lstm.py` — `LSTMSignClassifier`: стековий LSTM (`nn.LSTM`, `batch_first`) над
  feature-вектором кадру (Phase 7) + лінійний класифікатор над фінальним hidden state.
  Єдина реалізована архітектура на Phase 9 (`configs/model.yaml` лишає місце для
  transformer/video_jepa на майбутнє — `ml/training/config.py` **явно кидає
  `NotImplementedError`** для будь-якого нереалізованого `model.type`, а не мовчки навчає
  щось інше).
- `ml/training/config.py` — `load_training_config()` читає `configs/model.yaml`
  (`model.type`/`sequence_length`, `features.*`, новий розділ `training:` з
  hidden_size/num_layers/epochs/batch_size/learning_rate) в один `TrainingConfig` — єдине
  джерело гіперпараметрів експерименту (розділ 31), CLI-флаги лише перевизначають конкретний
  запуск.
- `ml/training/dataset.py` — `SignSequenceDataset` (torch `Dataset`): бере `SampleAnnotation` +
  `ml.datasets.dataset.load_feature_sequence()`, паддить/обрізає до фіксованої довжини
  (`pad_or_truncate`, нулями — узгоджено з тим, як `normalize_frame()` вже позначає
  "не виявлено").
- `ml/training/train.py` — CLI: signer-independent split (Phase 8) на train/val/test →
  тренувальний цикл (Adam, cross-entropy) → оцінка на val щоепохи → зберігає **найкращий**
  checkpoint у `models/checkpoints/<experiment-name>/latest.pt` (gitignored — build artifact,
  не вихідний код). Checkpoint містить усе, що знадобиться Phase 10 inference: ваги моделі,
  `model_config`/`feature_config`/`sequence_length`, мапу `label_to_index`, і — критично для
  правила "НЕ РОБИ FAKE AI" — `source_tags` + `demo_mode`, щоб checkpoint, натренований лише
  на `demo_synthetic`, ніколи не можна було сплутати з таким, що розпізнає реальну УЖМ.
  `test`-спліт рахується (для майбутнього `ml/evaluation/`), але цим скриптом не
  використовується — про це чесно пишеться в консоль.
- `ml/requirements-training.txt` — torch окремо від `ml/requirements.txt` (щоб backend/CV
  pipeline не тягнув важку GPU/CPU-специфічну залежність); заголовок файлу explicитно
  попереджає: **у Colab torch вже стоїть з GPU — не перевстановлювати цим файлом**, інакше
  втратиш GPU-доступ.

**Перевірено наживо:**
- `pytest` (`ml/`): 66 passed, 4 skipped (ті самі pose-skip з Phase 6). `ruff check` — чисто.
- **Реальний E2E через CLI** (не мок): `scripts/generate_demo_dataset.py` (180 семплів, 6
  сигнерів × 5 gloss × 6 takes) → `python -m ml.training.train` з кореня репо → live-навчання
  на CPU (torch 2.14, встановлено з дефолтного PyPI, бо `download.pytorch.org` заблоковано
  мережею sandbox — на твоїй машині/в Colab звичайний `pip install torch` спрацює так само) →
  15 епох, val_accuracy сходиться до 1.0 (очікувано: demo-класи навмисно тривіально
  розділювані), checkpoint збережено і перевірено `torch.load()` — усі поля (`model_type`,
  `model_config`, `feature_config`, `sequence_length`, `label_to_index`, `source_tags`,
  `demo_mode=True`, `val_accuracy`, `trained_at`) присутні й коректні.

**Known limitations:** val_accuracy=1.0 на demo-датасеті нічого не каже про реальну точність
розпізнавання УЖМ — це навмисно тривіальні синтетичні класи, лише перевірка, що
split→train→checkpoint pipeline коректний end-to-end. Реальне тренування чекає на реальний
датасет (Phase 8: досі не існує публічно). `ml/evaluation/` (held-out test-спліт, метрики) — не
в скоупі Phase 9, лишається на майбутнє.

## PHASE 10 — Real-time inference (COMPLETE)

Натренований checkpoint (Phase 9) тепер реально керує WebSocket-відповіддю замість чесної
заглушки:

- `ml/inference/recognizer.py` — `SignRecognizer` (framework-agnostic, без FastAPI-імпортів):
  завантажує checkpoint один раз, реконструює `LSTMSignClassifier` з `model_config`, тримає
  `label_to_index`⁻¹ мапу. `predict()` приймає рівно `sequence_length` feature-векторів (інакше
  чітка `ValueError` — краще явна відмова, ніж мовчки згодувати моделі щось інше, ніж вона
  бачила на тренуванні).
- `backend/app/services/lstm_inference_service.py` — тонкий адаптер: `LSTMSignRecognizer`
  реалізує `InferenceService` (Phase 2 інтерфейс), обгортаючи `SignRecognizer`. Для
  `demo_mode` checkpoint префіксує текст `"[DEMO] "` — щоб демо-передбачення ніколи не
  сплутати з реальним розпізнаванням УЖМ.
- `backend/app/services/inference_provider.py` — процесно-глобальний lazy-loader
  (`get_inference_service()`), той самий патерн кешування успіху/невдачі, що і
  `_get_landmark_extractor()` у WebSocket handler'і; спільний для `/health` і WS, щоб checkpoint
  не завантажувався двічі.
- `backend/websocket/handler.py` — кожне з'єднання тримає власний sliding window
  (`collections.deque(maxlen=sequence_length)`) feature-векторів. Поки вікно не заповнене —
  чесне `{"type":"error","message":"Buffering: X/Y frames..."}`; після заповнення — реальний
  `PredictionMessage` щокадру (sliding window). Сегментації меж жесту ще нема, тож усі
  передбачення позначені `is_final=false` (`"prediction"`, ніколи `"final_prediction"`) — чесно,
  а не вигадана впевненість.
- `backend/app/api/routes/health.py` — `ml_pipeline_status`: `not_implemented` (checkpoint не
  знайдено) / `demo_mode` (checkpoint є, але `demo_mode=true`) / `ready` (реальні дані, коли
  з'являться).
- `backend/app/core/config.py` — новий `model_checkpoint_path_resolved` (як і
  `mediapipe_models_dir`): виправлено приховану проблему — `MODEL_CHECKPOINT_PATH` у
  `.env.example` завжди був відносним шляхом без прив'язки до `REPO_ROOT`, тож при запуску
  `uvicorn` з `backend/` (як і документує README) резолвився б у неіснуючий
  `backend/models/checkpoints/...`. Раніше це не спливало, бо checkpoint ніде не завантажувався.
- `backend/requirements.txt` — додано `torch` (backend тепер реально виконує forward pass, не
  лише CV pipeline).
- `docker/backend.Dockerfile` — додано системні бібліотеки (`libgl1`/`libglib2.0-0`/`libegl1`/
  `libgles2`), яких потребує mediapipe для `dlopen()` нативної бібліотеки; `python:3.12-slim` їх
  не має, і без цього контейнер впав би з `OSError: libEGL.so.1: cannot open shared object
  file` при першому реальному кадрі — знайдено й виправлено саме зараз, бо Phase 10 вперше
  реально прогнав inference у контейнеризованому сценарії.

**Перевірено наживо:**
- `pytest`: `ml/` — 73 passed (додано `ml/tests/test_recognizer.py`); `backend/` — 19 passed
  (додано `test_lstm_inference_service.py`, `test_websocket_inference.py` — WS-рівень з
  замоканим landmark extractor, щоб ізолювати НОВУ buffering/inference-логіку від Phase 6-7 CV
  pipeline, який має власне покриття; `test_health.py` — новий `demo_mode` кейс). `ruff check` —
  чисто в обох пакетах.
- **Реальний E2E, не мок**: натреновано demo-checkpoint → піднято `uvicorn` з
  `MODEL_CHECKPOINT_PATH` на нього → `GET /health` → `ml_pipeline_status: "demo_mode"` →
  живий `websockets`-клієнт шле 35 РЕАЛЬНИХ JPEG-кадрів через справжній MediaPipe (не мок) →
  кадри 1-31: `Buffering: N/32 frames...`, кадр 32+: реальний
  `{"type":"prediction","text":"[DEMO] DYAKUYU","confidence":0.229...,"is_final":false}`,
  стабільно на наступних кадрах (sliding window).

**Known limitations:** на момент Phase 10 не було сегментації меж жесту — модель просто
класифікувала поточне вікно щокадру, тому `is_final` був завжди `false` (виправлено в Phase 11,
нижче). Реальна точність розпізнавання УЖМ = 0, поки нема реального датасету (Phase 8) і
реального тренування (Phase 9 на ньому). `model_type` підтримує лише `lstm` —
transformer/video_jepa залишаються заявленими в конфігу, але нереалізованими (чесна
`NotImplementedError`, не мовчазний fallback).

## PHASE 11 — Gloss-sequence aggregation (COMPLETE)

Сирий потік per-frame передбачень (Phase 10: одне слово щокадру, поки жест утримується) тепер
перетворюється на стабільну послідовність gloss:

- `ml/inference/aggregator.py` — `GlossSequenceAggregator`: **не** справжня лінгвістична
  сегментація (без детекції фаз рух/утримання) — детермінований debounce-евристик, чесно
  так і задокументований. Жест має бути передбачений `stability_frames` разів поспіль (вище
  `confidence_threshold`), щоб бути "підтвердженим" і доданим у `.sequence`; той самий
  утримуваний жест повторно не підтверджується. Низька впевненість перериває серію, а не
  мовчки в ній рахується.
- `backend/websocket/handler.py` — кожне з'єднання тримає власний `GlossSequenceAggregator`
  (як і sliding window). Більшість кадрів лишаються `"prediction"` (`is_final=false`);
  `"final_prediction"` (`is_final=true`) відправляється рівно один раз у момент підтвердження.
  Підтверджена послідовність логується (мітки gloss — це метадані, не сирі дані, дозволено
  правилом приватності).
- `backend/app/core/config.py` + `.env.example` — `WS_GLOSS_STABILITY_FRAMES` (default 5),
  `WS_GLOSS_CONFIDENCE_THRESHOLD` (default 0.5) — нічого не захардкожено.

**Перевірено наживо:**
- `pytest`: `ml/` — 81 passed (+8 `ml/tests/test_aggregator.py`: поріг стабільності,
  неповторне підтвердження того самого жесту, переривання серії низькою впевненістю, reset);
  `backend/` — 20 passed (+1 WS-рівня: `WS_GLOSS_CONFIDENCE_THRESHOLD=0` ізолює агрегацію від
  калібрування впевненості recognizer'а, яке вже покрито в Phase 10 тестах). `ruff check` —
  чисто.
- **Реальний E2E, не мок**: натренований demo-checkpoint + живий `websockets`-клієнт через
  справжній `uvicorn` (`WS_GLOSS_CONFIDENCE_THRESHOLD=0.0`, `stability_frames=5` за
  замовчуванням): кадри 31-34 → `"prediction"` (`is_final=false`), кадр 35 (5-те однакове
  передбачення поспіль) → рівно один `"final_prediction"` (`is_final=true`), кадри 36-39 →
  знову `"prediction"` (жест утримується далі, повторно не підтверджується).

**Known limitations:** евристика стабільності — не справжнє розпізнавання меж жестів
(рух→утримання→рух); коротко утримані або швидко пов'язані жести можуть підтвердитись не там,
де лінгвістично мала б бути межа. Послідовність `agg.sequence` наразі лише логується на
бекенді, не передається клієнту окремим WS-повідомленням (client бачить лише
`is_final=true`/`"final_prediction"` per-подію) — повний список поки не потрібен нікому, крім
майбутнього Phase 12.

## Наступна фаза

**PHASE 12 — Gloss-to-text NLP**: `backend/app/services/translation_service.py::gloss_to_text()`
(вже заявлено в docstring цього файлу як Phase 12) — rule-based переклад послідовності gloss
(`GlossSequenceAggregator.sequence`, тепер реально накопичується в Phase 11) у природне
українське речення (відмінки/число/рід/порядок слів, розділ 14/17 ТЗ), а не наївний
`' '.join()`. `RuleBasedTranslationService` замінить `NotConfiguredTranslationService`.
