# PROJECT STATUS

Останнє оновлення: Phase 14 complete.

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

## PHASE 12 — Gloss-to-text NLP (COMPLETE)

`backend/app/services/translation_service.py::gloss_to_text()` тепер реальна (не наївний
`' '.join()`) rule-based логіка, розділ 14/17 ТЗ:

- `ml/nlp/gloss_to_text.py` — `compose_sentence()`: framework-agnostic граматичний рушій.
  Відмінює іменники за відмінком, який вимагає дієслово (напр. `WANT` керує родовим
  партитивом: "хочу **води**", `LIKE`/`HAVE` — знахідним), відмінює дієслово за особою
  займенника (1sg/2sg/1pl), вставляє заперечення `не` перед дієсловом у правильній позиції
  (незалежно від того, де в gloss-послідовності стояв gloss заперечення) — składає стандартний
  укр. порядок слів, а не порядок жестів. Лексикон навмисно малий: реального gloss-словника
  УЖМ ще нема (Phase 8), тож кожен gloss і кожен паттерн, які рушій приймає, явно перелічені в
  модулі. Невідомий gloss → `UnknownGlossError`; відомі gloss, але непідтримана комбінація →
  `UnsupportedPatternError` (обидва — `ValueError`) — чесна відмова замість вгадування.
- `backend/app/services/translation_service.py` — `RuleBasedTranslationService` реалізує
  `gloss_to_text()` через рушій; `text_to_gloss()` лишається `NotConfigured` до Phase 14.
- `backend/websocket/handler.py` — для щойно **підтвердженого** (Phase 11, `is_final=true`)
  жесту тепер намагається перекласти саме цей один gloss через `RuleBasedTranslationService`;
  якщо лексикон його покриває (всі 5 demo-gloss — стендалон-слова, тож завжди покриває) —
  клієнт бачить справжнє речення (`[DEMO] Привіт.`) замість сирої мітки (`[DEMO] PRIVIT`);
  якщо `ValueError` (gloss/паттерн не в лексиконі) — тихо лишається сирий gloss-текст, без
  падіння з'єднання.

**Перевірено наживо:**
- `pytest`: `ml/` — 97 passed (+16 `ml/tests/test_gloss_to_text.py`: усі 5 demo-стендалонів,
  приклад `["I","WANT","WATER"]` → `"Я хочу води."` з докстрінга самого інтерфейсу, різні
  займенники/дієслова/відмінки, заперечення, невідомий gloss, невідомий паттерн, порожня
  послідовність, monkeypatch-тести на неповну відміну/дієвідміну); `backend/` — 23 passed
  (+3 `test_translation_service.py`, оновлено WS-тест на реальний композиційний текст).
  `ruff check` — чисто в обох пакетах.
- **Реальний E2E, не мок**: натренований demo-checkpoint + живий `websockets`-клієнт проти
  справжнього `uvicorn` (реальний MediaPipe, не stub): кадри 1-31 → `Buffering`, 31-34 →
  interim `[DEMO] PRIVIT`, кадр 35 (підтвердження) → `{"type":"final_prediction",
  "text":"[DEMO] Привіт.","is_final":true}` — справжнє речення замість сирого gloss.

**Known limitations:** переклад працює лише для **одного** щойно підтвердженого gloss, не для
всієї накопиченої `GlossSequenceAggregator.sequence` — переклад реальних багатослівних речень
("Я хочу води.") через живий WS-потік ще не підключено: для цього потрібні (а) реальний
багатослівний gloss-словник (Phase 8 — досі не існує) і (б) спосіб визначити межу **речення**,
а не лише окремого жесту (окрема майбутня евристика, аналогічна Phase 11 для меж жесту).
Лексикон — 3 займенники, 3 дієслова, 3 іменники + 5 demo-стендалонів; будь-який реальний gloss
поза цим списком чесно відхиляється, а не вгадується.

## PHASE 13 — Voice input (browser STT) (COMPLETE)

Знайдено точне підтвердження в уже наявному коді: `backend/app/services/speech_service.py`
(написаний завчасно в Phase 2) явно документує "SpeechRecognizer... Implemented in Phase 13
only if/when a server-side STT provider... is configured" — за замовчуванням
(`STT_PROVIDER=browser`) весь STT відбувається в браузері, backend узагалі не займається аудіо.
Реальна робота Phase 13 — саме frontend:

- `frontend/hooks/useSpeechRecognition.ts` — обгортка над браузерним Web Speech API
  (`SpeechRecognition`/`webkitSpeechRecognition`), `lang="uk-UA"`, чесні стани
  (`idle`/`listening`/`stopped`/`error`) з розпізнаванням конкретних причин помилки
  (`not-allowed`→permission_denied, `no-speech`, `network`, `unsupported` якщо API взагалі
  нема) — той самий підхід чесної обробки помилок, що і в `useCamera.ts` (Phase 4).
- `frontend/components/VoiceInput/` — кнопка 🎤, статус, викликає `onTranscript(text)` при
  фінальному розпізнаному тексті.
- Підключено в `TranslatorView`: голосовий транскрипт заповнює те саме текстове поле, що й
  ручне введення (Phase 14).

**Перевірено наживо:** `vitest` — 34/34 passed (нові: `useSpeechRecognition.test.ts` (5),
`VoiceInput.test.tsx` (2)), `tsc --noEmit` — 0 помилок, `eslint` — 0 помилок/warnings,
`next build` — успішний production build.

**Known limitations:** сервер-сайд STT (реальний `SpeechRecognizer` для `STT_PROVIDER != browser`)
залишається `NotConfigured` — за дизайном, доки не з'явиться конкретний провайдер, який
дійсно потрібно підключити.

## PHASE 14 — Text-to-gloss NLP + UI (COMPLETE)

Зворотний напрямок до Phase 12, і повне UI-підключення "Текст / Голос → Жести":

- `ml/nlp/lexicon.py` — спільний словник (займенники/дієслова/іменники/стендалони) винесено
  окремо від `gloss_to_text.py`, щоб Phase 12 (gloss→текст) і Phase 14 (текст→gloss) читали
  **той самий** словник і ніколи не розійшлись у лексиці.
- `ml/nlp/text_to_gloss.py` — `parse_gloss_sequence()`: реальний (не заглушка) парсер.
  Будує reverse-index (кожна відмінена/дієвідмінена форма слова → gloss) один раз при
  імпорті; заперечувальна частка "не" мапиться на `NOT` **на тому самому місці**, де вона
  стояла (українське заперечення вже препозитивне, так само як і в gloss-конвенції Phase 12
  — тож обидва напрямки узгоджені без додаткового реордерингу). Стендалон-фрази (напр.
  "будь ласка") розпізнаються як ціла фраза перед пословним розбором. Невідоме слово →
  `UnrecognizedWordError` з точним словом і повним текстом — чесна відмова, не вгадування.
  **Round-trip тест**: усе, що `parse_gloss_sequence` розбирає, `compose_sentence` збирає
  назад в ідентичний текст — гарантія, що два напрямки узгоджені за побудовою.
- `backend/app/services/translation_service.py` — `RuleBasedTranslationService.text_to_gloss()`
  тепер реальний виклик рушія (замість `NotConfiguredError`).
- `backend/app/api/routes/translate.py` + `app/schemas/translate.py` — новий
  `POST /translate/text-to-gloss`: `{"text": "..."}` → `{"gloss_sequence": [...]}`, або
  `422` з чітким `detail`, якщо слово не розпізнано.
- Frontend: `components/TextInput/` (поле + кнопка "Перекласти"), `components/Transcript/`
  (показує gloss-послідовність як токени, з чесним поясненням "аватар — Phase 15, поки лише
  текст"), обидва підключені в `TranslatorView` разом з `VoiceInput` (Phase 13) — голос і
  текст ведуть в одне поле, кнопка викликає `POST /translate/text-to-gloss` через
  `lib/api.ts::textToGloss()`.

**Перевірено наживо:**
- `pytest`: `ml/` — 124 passed (+26: `test_text_to_gloss.py` включно з round-trip тестами
  для кожного підтримуваного речення); `backend/` — 28 passed (+5: `test_translate_route.py`,
  оновлений `test_translation_service.py`). `ruff check` — чисто.
- `vitest`: 34/34 passed (+10 нових: `TextInput.test.tsx`, `Transcript.test.tsx`, плюс
  інтеграційний тест у `TranslatorView.test.tsx`, що вводить текст, тисне "Перекласти" і
  бачить реальні gloss-токени). `tsc --noEmit`, `eslint`, `next build` — усі чисті.
- **Реальний E2E через живий `uvicorn`, не мок**: `curl POST /translate/text-to-gloss`:
  `"Я хочу води."` → `{"gloss_sequence":["I","WANT","WATER"]}`; `"Привіт."` →
  `{"gloss_sequence":["PRIVIT"]}`; `"Я не хочу води."` → `{"gloss_sequence":["I","NOT","WANT","WATER"]}`;
  `"Я хочу кавун."` → `422 {"detail":"Unrecognized word 'кавун'..."}`.

**Known limitations:** той самий вузький лексикон, що й Phase 12 (3 займенники, 3 дієслова,
3 іменники, 5 стендалонів) — реальний широкий словник чекає на реальний датасет УЖМ (Phase 8).
Порядок gloss = порядок слів у введеному тексті, без переупорядкування в граматику жестової
мови (topic-comment тощо) — задокументоване обмеження, не помилка.

## PHASE 15 — 3D Avatar (COMPLETE)

Three.js-аватар, що анімує gloss-послідовність з Phase 14 (`POST /translate/text-to-gloss`)
у видимі рухи процедурної ляльки. Замінив плейсхолдер "буде доданий у Phase 15" в `TranslatorView`.

- `frontend/components/Avatar/poses.ts` — `JointRotations` (голова, плечі, лікті),
  `NEUTRAL_POSE`, та `GLOSS_POSES`: рукописні (hand-authored) демо-жести лише для 5 glosses
  демо-датасету (`PRIVIT`→хвиля рукою, `TAK`→кивок, `NI`→похитування головою,
  `DYAKUYU`/`BUD_LASKA`→руки разом). **Це НЕ справжні жести УЖМ** — жодного motion-capture чи
  референсних даних для реальних жестів немає (Phase 8: публічного датасету УЖМ не знайдено).
  `poseForGloss()` для будь-якого іншого gloss повертає `null` (чесна відсутність анімації),
  а не вгадану позу.
- `frontend/components/Avatar/player.ts` — `GlossPlayer`: чиста (без Three.js/DOM) логіка
  послідовного відтворення поз — лерп-перехід (`TRANSITION_SECONDS=0.35s`) до цільової пози,
  утримання (`HOLD_SECONDS=1.1s`, з синусоїдним "wobble" для жестів на кшталт хвилі рукою),
  перехід до наступного gloss. `unanimatedGlosses` — список glosses без визначеної пози
  (утримують `NEUTRAL_POSE`, а не вигадану анімацію).
- `frontend/components/Avatar/puppet.ts` — `buildPuppet()`: процедурна лялька з примітивів
  Three.js (сфера-голова, циліндри тулуб/руки), без rigged/skinned GLTF-моделі. Ієрархія
  `Object3D`-груп для шарнірів (плече → лікоть, вкладені) — `applyRotations()` мапить
  `JointRotations` на обертання відповідних pivot-груп.
- `frontend/components/Avatar/Avatar.tsx` — React-компонент: `detectWebglSupport()` одноразово
  перевіряє підтримку WebGL через одноразовий throwaway `<canvas>` (без setState в ефекті —
  визначається лінивим ініціалізатором `useState`), і якщо непідтримується — чесне
  повідомлення "WebGL не підтримується цим браузером" замість порожнього/зламаного canvas.
  Інакше: `THREE.WebGLRenderer` на реальному `<canvas>`, `requestAnimationFrame`-цикл викликає
  `GlossPlayer.update(delta)` щокадру, показує видиму позначку "⚠ DEMO — умовні жести, не
  справжня УЖМ" і (якщо є) список glosses без анімації.
- `frontend/components/Translator/TranslatorView.tsx` — `<Avatar glossSequence={...}>`
  підключено: показує послідовність з останнього успішного `text-to-gloss` перекладу
  (Phase 14), порожній масив у стані idle/loading/error.

**Перевірено наживо:**
- `vitest`: 52/52 passed (+18 нових: `poses.test.ts`, `player.test.ts` — таймінг переходу/
  утримання/wobble/переходу між glosses, `puppet.test.ts` — ієрархія шарнірів і мапінг
  обертань, `Avatar.test.tsx` — WebGL-fallback у jsdom, де немає реального GL-контексту).
  `tsc --noEmit`, `eslint`, `next build` — усі чисті.
- `three@0.185.1` + `@types/three@0.185.4` додані в `frontend/package.json`.

**Known limitations:** пози — лише 5 рукописних демо-жестів (не справжня УЖМ, задокументовано
в коді і в UI через позначку "DEMO"); реальні жести жестової мови вимагають або справжнього
motion-capture/анімаційного датасету, або rigged 3D-моделі з реальними даними про рухи рук —
жодного з них ще немає (Phase 8). `GlossSequenceAggregator.sequence` (Phase 11, розпізнавання
з камери) поки не підключено до аватара — тільки напрямок Phase 14 (текст/голос → жести).

## Наступна фаза

Наступна фаза ще не визначена — розпізнана з камери gloss-послідовність (Phase 11) поки не
анімує аватар (лише напрямок текст/голос → жести підключено), і немає реального датасету УЖМ
для повноцінного розпізнавання чи анімації (Phase 8).
