# PROJECT STATUS

Останнє оновлення: розширення лексикону (54 слова) + UI/UX-оновлення + landmarks-індикатор
(позапланово, після Phase 17).

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
  підключено до **обох** джерел gloss-послідовності: результату `text-to-gloss` перекладу
  (Phase 14, текст/голос → жести) **і** підтверджених знаків з камери (Phase 11
  `final_prediction`, накопичуються в один список по мірі надходження) — яке джерело
  спрацювало останнім, те й анімує аватар.
- `backend/websocket/protocol.py` + `handler.py` — `PredictionMessage` отримало нове поле
  `gloss` (сирий передбачений label, напр. `"TAK"`), окремо від `text` (composed-речення з
  Phase 12). Це те, що фронтенд тепер програє на аватарі при кожному `final_prediction`
  — ніколи не проміжний (`is_final=false`) здогад.
- Видалено `backend/app/services/avatar_service.py` (`AvatarService`/`NotConfiguredAvatarService`,
  заскафолжено ще до Phase 15 в очікуванні *бекенд*-сервісу gloss→animation-ID) разом з
  тестом `test_avatar_service_refuses_mapping_before_phase_15` — мапінг виявився простими
  статичними даними без потреби в мережевому виклику, тож живе повністю на клієнті
  (`components/Avatar/poses.ts`), а не як окремий бекенд-ендпоінт.

**Перевірено наживо:**
- `vitest`: 53/53 passed (+19 нових: `poses.test.ts`, `player.test.ts` — таймінг переходу/
  утримання/wobble/переходу між glosses, `puppet.test.ts` — ієрархія шарнірів і мапінг
  обертань, `Avatar.test.tsx` — WebGL-fallback у jsdom, `TranslatorView.test.tsx` — новий тест
  на `final_prediction` → аватар). `tsc --noEmit`, `eslint`, `next build` — усі чисті.
- `three@0.185.1` + `@types/three@0.185.4` додані в `frontend/package.json`.
- `pytest`: `backend/` — 27 passed (−1 обсолетний тест `avatar_service`, +0 нових — існуючі
  тести вже покривали `PredictionMessage`). `ruff check` — чисто.

**Known limitations:** пози — лише 5 рукописних демо-жестів (не справжня УЖМ, задокументовано
в коді і в UI через позначку "DEMO"); реальні жести жестової мови вимагають або справжнього
motion-capture/анімаційного датасету, або rigged 3D-моделі з реальними даними про рухи рук —
жодного з них ще немає (Phase 8). Коли обидва джерела (камера і текст/голос) активні одночасно,
аватар показує лише те, що прийшло останнім, а не окрему чергу для кожного джерела.

## PHASE 16 — Fingerspelling / дактилологія (COMPLETE)

Реальні глухі мовці не просто відмовляються від слова поза словником — вони розкладають
його по літерах стандартною дактильною абеткою. Це саме те, чого не вистачало Phase 12/14:
раніше будь-яке слово поза крихітним лексиконом (3 займенники, 3 дієслова, 3 іменники, 5
стендалонів) викликало жорстку відмову (`UnrecognizedWordError`/422).

- `ml/nlp/fingerspelling.py` (NEW) — усі 33 літери сучасної української абетки, кожна →
  gloss-токен `FS_<ЛІТЕРА>`. `spell_word()` (слово → список токенів), `despell()` (зворотне),
  `is_fingerspell_gloss()`. Апостроф/дефіс/цифри/латиниця навмисно виключені (немає дактильного
  жесту) — `UnspellableCharacterError` з точним символом.
- `ml/nlp/text_to_gloss.py` — коли слово не знайдено в reverse-index лексикону, замість
  негайної `UnrecognizedWordError` тепер намагається `spell_word()`; помилка лишається, але
  тільки якщо слово має символ без дактильного жесту (латиниця, цифри тощо).
- `ml/nlp/gloss_to_text.py` — `_group_units()` згортає послідовний прогін `FS_`-токенів в один
  "fingerspell"-юніт перед композицією: як окреме слово-речення (`compose_sentence(["FS_О",
  ...]) == "Оксана."`), так і як об'єкт у SVO-патерні (`["I","LIKE",<FS...>]`) — вставляється
  як є, капіталізовано, **без** відмінювання під керований дієсловом відмінок (немає реальних
  даних про відмінювання довільних імен — задокументоване й протестоване обмеження).
- Frontend: `frontend/lib/glossDisplay.ts` (NEW) — `groupGlossesForDisplay()` згортає прогін
  `FS_`-токенів в один читабельний чіп "🔤 Слово" замість шереги окремих літер; використано в
  `components/Transcript` (кольором відрізняється від звичайних gloss-чіпів) і
  `components/Avatar`'s рядку "Немає анімації для: ...".
- **Аватар НЕ анімує дактилологію**: лялька (Phase 15) не має геометрії пальців, тож не може
  показати 33 візуально різні хендшейпи — вигадування їх порушило б те саме правило "no fake
  AI", що й сфабрикована ML-модель. `FS_`-glosses просто не мають визначеної пози (як і
  будь-який інший немапований gloss) — аватар чесно тримає нейтральну позу.
- Виправлено застарілий рядок у `components/Transcript` ("Three.js avatar (Phase 15) ще не
  реалізований") — не оновлювався відколи Phase 15 фактично завершився.

**Перевірено наживо:**
- `pytest`: `ml/` — 130+ passed (Phase 12/14 тести без torch/yaml залежностей; +12 нових у
  `test_fingerspelling.py`, +6 у `test_text_to_gloss.py`, +3 у `test_gloss_to_text.py`, разом з
  оновленим round-trip параметром для "Оксана."/"Я люблю Оксану."). `backend/` — тести
  `test_translation_service.py`/`test_translate_route.py` оновлено: приклад `"Я хочу кавун."`
  тепер повертає `200` з дактильним fallback замість `422` (документована зміна поведінки);
  новий приклад `"Я хочу pizza."` (латиниця — справді нерозпізнавано) демонструє `422`. `ruff
  check` — чисто.
- `vitest`: 58/58 passed (+5 нових: `glossDisplay.test.ts`, +1 у `Transcript.test.tsx`).
  `tsc --noEmit`, `eslint`, `next build` — усі чисті.

**Known limitations:** дактилологія не анімується на аватарі (вище); капіталізація для
fingerspell-слова завжди "перша літера велика" при композиції назад (типова конвенція для
власних імен) — для звичайного (не власного) слова поза лексиконом, введеного з малої літери
(напр. "кавун"), зворотна композиція поверне "Кавун" з великої, що НЕ ідентично оригінальному
тексту символ-у-символ — задокументована й протестована відома різниця, не тиха помилка.
Дактильний fallback працює тільки в `text_to_gloss` (текст → gloss); `gloss_to_text` для
одиничного підтвердженого знаку з камери (Phase 10-11 WebSocket) все ще не викликає
fingerspelling — там немає багатослівного речення для розбору.

## PHASE 17 — Face/facial grammar (COMPLETE)

Немануальні компоненти УЖМ: сигнер несе граматичне значення на обличчі, не лише руками —
питальне речення "так/ні" позначається піднятими бровами, "хто/що/де" — насупленими, **без
окремого ручного жесту "?"**. Без цієї фази розпізнане питання виглядало б у `gloss_to_text`
точнісінько як звичайне речення.

- `ml/features/facial_grammar.py` (NEW) — `eyebrow_eye_gap()`: реальний, вимірюваний сигнал
  (вертикальна відстань брова↔око) на вже витягнутих MediaPipe FaceMesh landmarks
  (`ml/features/face.py`'s канонічні індекси, нічого нового не додається до CV pipeline).
  `BaselineCalibrator` — калібрується під **власне** нейтральне обличчя сигнера за перші N
  кадрів (пропорції брова↔око різняться між людьми й кадруванням камери — єдиний поріг для
  всіх був би безглуздим), потім класифікує подальші кадри відносно цього base line за
  relative ratio-порогом (не абсолютна величина).
  **Детермінований геометричний евристик, не натренований класифікатор** — жодного розміченого
  датасету мімічної граматики не існує для тренування чи валідації (Phase 8 й досі не знайшов
  жодного реального датасету УЖМ). Пороги (`WS_FACIAL_RAISED_RATIO`/`WS_FACIAL_FURROWED_RATIO`,
  `.env`) — задокументована відправна точка, не емпірично каліброва на реальних даних.
- `ml/nlp/gloss_to_text.py` — `compose_sentence(..., is_question=True)` міняє кінцеву "." на
  "?" — оскільки жестова мова не має окремого gloss-токена для питання, викликач сам вирішує,
  чи застосовувати це на основі мімічного маркера.
- `backend/websocket/handler.py` — кожен кадр із виявленим обличчям годує per-connection
  `BaselineCalibrator` **незалежно** від готовності ML-інференсу (Phase 9-10) — це окрема
  функція. Маркер їде в кожному `PredictionMessage` (`"facial_grammar"`), і коли gloss щойно
  **підтверджено** (Phase 11) одночасно з активним маркером, `gloss_to_text(..., is_question=...)`
  перетворює `[DEMO] Так.` на `[DEMO] Так?`. `text_to_gloss` (Phase 14, текст→gloss) не
  потребує змін — він вже відкидає кінцеву пунктуацію, бо у введеному тексті немає мімічного
  каналу для виявлення.
- `backend/websocket/protocol.py` — `PredictionMessage.facial_grammar: str = "NONE"` (нове
  поле; `"NONE"` покриває і "обличчя не виявлено", і "ще калібрується", і "нейтральне").
- Frontend: `types/api.ts` (`FacialGrammarMarker`), `TranslatorView.tsx` показує невеликий
  бейдж ("Брови підняті...") біля живого перекладу, коли останнє WebSocket-повідомлення несе
  маркер, відмінний від `"NONE"`.

**Перевірено наживо:**
- `pytest`: `ml/` — +9 нових у `test_facial_grammar.py` (калібрування, класифікація,
  reset, крайові випадки), +5 нових у `test_gloss_to_text.py` (`is_question` для всіх
  композиційних патернів). `backend/` — новий `test_facial_grammar_websocket.py` (2 тести:
  `facial_grammar` = `"NONE"` без обличчя; підтверджений gloss стає питанням при піднятих
  бровах — детерміновано через baseline=0 трюк, не залежить від точного масштабу
  `normalize_face()`). `ruff check` — чисто.
- `vitest`: 59/59 passed (+2 нових у `TranslatorView.test.tsx`). `tsc --noEmit`, `eslint`,
  `next build` — усі чисті.

**Known limitations:** евристик виявляє лише позицію брів (не увесь спектр немануальних
маркерів — топікалізація, заперечення головою, форма рота тощо, свідомо не додано, аби
не вигадувати граматику без лінгвістичного обґрунтування). Пороги не валідовані
на реальному відео реальних сигнерів (Phase 8). `is_question` застосовується лише до
**одиничного** підтвердженого gloss на WebSocket-стрімі — багатослівні речення (Phase 11's
`GlossSequenceAggregator.sequence`) все ще не транслюються повністю (те саме обмеження, що
й у Phase 12), тож "питальність" багатослівного речення поки не композиться.

## UI/UX-оновлення + landmarks-індикатор (позапланово)

Користувач знайшов і опрацював **перший реальний (не синтетичний) датасет** цього проєкту:
два Kaggle-датасети статичних зображень української дактильної абетки (33 літери,
~40 783 зображень у 200×200 версії) + власний ноутбук, що вже конвертує їх у реальні
MediaPipe hand landmarks (CSV). Це закриває Phase 16 (fingerspelling) реальним візуальним
розпізнаванням літер — окрема задача, в очікуванні завантаження файлів (CSV і/або zip).
Заразом виконано частину супутніх запитів, не пов'язаних із даними:

- **Прибрано сторінку "Головна"** — `frontend/app/page.tsx` тепер сам є перекладачем
  (`TranslatorView`), `/translator` видалено як окремий маршрут, nav-посилання в
  `layout.tsx` прибрано (лишилась тільки одна сторінка).
- **UI-редизайн без емодзі**: усі емодзі (🔤, ⚠, 🎤, 🤨) замінено на `lucide-react`
  SVG-іконки (`CaseSensitive`, `Info`, `Mic`/`Square`, `HelpCircle`), палітра бейджів
  звужена й уніфікована (менше "кричущих" кольорів — amber лишився тільки для справді
  живих/уваги-вартих сигналів, решта — нейтральний slate).
- **Індикатор видимості рук/пози** (нове повідомлення `landmarks_status` у WS-протоколі,
  `backend/websocket/protocol.py` + `handler.py`): backend і раніше рахував
  `normalized.present` щокадру — тепер це реальне значення (не здогад) їде окремим
  повідомленням **перед** prediction/error, незалежно від готовності ML-чекпоінта, тож
  індикатор працює з першого кадру. Фронтенд: `components/LandmarkIndicator/` — opt-in
  перемикач (вимкнено за замовчуванням), показує ліва рука/права рука/поза зеленою/сірою
  крапкою. `hooks/useWebSocket.ts` тримає `landmarksStatus` окремо від `lastMessage`
  (усередині `onmessage`, не через ефект, що читає `lastMessage`, — уникає
  react-hooks/set-state-in-effect і коректно переживає наступне prediction/error
  повідомлення того самого кадру).

**Перевірено наживо:**
- `pytest`: `backend/` — 32/32 (+2 нових: `test_landmarks_status_reflects_actual_per_modality_detection`,
  плюс оновлені існуючі WS-тести, що тепер споживають зайве `landmarks_status`-повідомлення
  на кожен кадр). `ruff check` — чисто.
- `vitest`: 64/64 (+5 нових: `LandmarkIndicator.test.tsx` ×4, `useWebSocket.test.ts` — sticky
  `landmarksStatus` переживає наступне повідомлення). `tsc --noEmit`, `eslint`, `next build` —
  усі чисті (0 маршрутів окрім `/`).

**В очікуванні від користувача:**
- CSV/zip з Kaggle-датасетів дактильної абетки — реальний класифікатор + accuracy/confusion
  matrix для звіту.
- Дані для переробки 3D-аватара: користувач обрав зовнішню rigged 3D-модель (не процедурний
  риг) — потрібне конкретне джерело/файл моделі з rigged пальцями.

## Розширення лексикону: 50 слів, речення замість одного слова (позапланово)

`ml/nlp/lexicon.py` виріс з 9 слів (3 займенники, 3 дієслова, 3 іменники) до **54**: 7
займенників (я/ти/він/вона/ми/ви/вони — усі особи й числа), 15 дієслів, 24 іменники, 8
стендалонів. Це не просто більше слів — це ~2400 різних граматично коректних речень
підмет×присудок×додаток (7×15 сполучень без додатка + ще більше з ним), кожне з яких
`compose_sentence()`/`parse_gloss_sequence()` реально відмінює/дієвідмінює, а не `join()`.

- Українська теперішній час не розрізняє рід — "він хоче"/"вона хоче" однакова форма
  дієслова, тож `HE` і `SHE` навмисно діляться одним `person_key="3sg"` замість дублювання.
  Тваринний (animate) `FRIEND`: accusative = genitive ("бачу друга"), не nominative — реальне
  українське правило, не помилка.
- **Свідоме розділення відмінків** (задокументовано в docstring `lexicon.py`): іменники-маси
  (вода/чай/кава/молоко/сік/суп/м'ясо/цукор) мають і `genitive_partitive` ("хочу води"), і
  `accusative` ("п'ю воду") — обидва ідіоматичні. Лічильні іменники (книга/телефон/будинок/...)
  мають лише `accusative` — поєднання з дієсловом, що керує `genitive_partitive` (напр.
  `WANT`+`MONEY`), навмисно й чесно викликає `UnsupportedPatternError`, а не вигадує сумнівне
  речення.
- Нові дієслова без прямого додатка (`GO`, `WORK`, `LIVE`, `SLEEP`, `SPEAK`) підтримують лише
  двотокенний патерн `[ЗАЙМЕННИК, ДІЄСЛОВО]` (вже існуючий патерн з Phase 12, напр. "Я маю.").

**Перевірено наживо:** `ml/tests/test_lexicon_expansion.py` (новий) — вичерпний перебір
**усіх** валідних комбінацій займенник×дієслово (105) та займенник×дієслово×іменник (2310) —
кожна композиція round-trip перевірена через `compose_sentence` → `parse_gloss_sequence` →
той самий gloss-список, разом із іменованими тестами на 3-ю особу, animate accusative,
негацію з новим дієсловом і чесну відмову для невідповідного відмінка. `ruff check` — чисто.
Існуючі `test_gloss_to_text.py`/`test_text_to_gloss.py` (57 тестів) не зламані — старі
1sg/2sg/1pl форми для WANT/LIKE/HAVE не змінились, лише додані нові person_keys.

## Швидший перекладач, без "сирих" підкреслень, покращений 3D-аватар (позапланово)

- **Lazy-loading аватара**: `Avatar` (найважча залежність фронтенду — Three.js, ~540 КБ) тепер
  підключається через `next/dynamic({ ssr: false })` у `TranslatorView.tsx` замість статичного
  імпорту, з видимим індикатором завантаження ("Завантаження 3D-аватара..."). Перевірено не на
  слово, а фактично: `.next/server/app/page/build-manifest.json`'s `rootMainFiles` (файли, які
  реально блокують перший рендер) більше не містить Three.js-чанк — він завантажується окремо,
  лише коли компонент реально монтується.
- **Без "сирих" gloss-токенів у UI**: розширення лексикону (54 слова, позапланова секція вище)
  додало багатослівні токени на кшталт `WORK_N`, `YOU_PL`, `DO_POBACHENNYA` — підкреслення в них
  чисто програмна конвенція найменування, не мало сенсу для читача UI. `lib/glossDisplay.ts`:
  нова `formatGlossLabel()` (підкреслення → пробіл, суто косметично, той самий ідентифікатор,
  нічого не перекладається/не вгадується), застосована і в `Avatar.tsx`'s статусі поточного
  gloss, і в `groupGlossesForDisplay()`'s звичайних (не fingerspell) чіпах.
- **Аватар: повтор жесту, швидкість, контраст, обертання** (не заблоковано на завантаження
  зовнішньої rigged-моделі — реалізовано над існуючою процедурною лялькою, Phase 15):
  - `groupGlossesForDisplay()` тепер повертає й `tokens: string[]` для кожного display-item'а
    (сирі gloss-токени, що стоять за чіпом — один для звичайного gloss, ціла літерна послідовність
    для fingerspell-слова) — дає `Avatar.tsx` змогу передати точний під-список назад у
    `GlossPlayer.play()` без повторного виведення.
  - **Повтор конкретного жесту**: кожен чіп під 3D-канвасом — кнопка (з іконкою) з `title`
    "Повторити жест «...»", активна лише якщо хоч один з її `tokens` має визначену позу
    (`poseForGloss() !== null`) — чіпи без анімації (напр. fingerspell-літери, які ще не мають
    визначених поз) чесно неактивні, а не мовчки нічого не роблять.
  - **Швидкість відтворення**: 0.5×/1×/1.5×/2× кнопки; множник тримається в `useRef` (не
    перезапускає `useEffect`, що будує сцену/рендерер) і множить `deltaSeconds`, який щокадру
    йде в `GlossPlayer.update()` — сама `player.ts` логіка незмінна, лише крок часу масштабується
    ззовні.
  - **Контраст**: замінено плоске 1-точкове освітлення (ambient + один directional) на
    3-точкову схему (яскравіший key light, холодний dim fill з протилежного боку, rim light
    ззаду для відділення силуету від фону) + темний (`bg-slate-800`) в'юпорт замість світлого
    `bg-slate-100` — лялька тепер контрастно виділяється, а не зливається з тлом.
  - **Обертання моделі**: `OrbitControls` (`three/examples/jsm/controls/OrbitControls.js`,
    вже доступний у встановленому `three@0.185.1`) — перетягування обертає камеру навколо
    лялька, прокрутка наближає/віддаляє (`minDistance=1.8`, `maxDistance=5`), панорамування
    вимкнено (немає сенсу для одиночної фігури в центрі), `enableDamping` для плавності;
    `controls.update()` щокадру, `controls.dispose()` при unmount. Підказка "Перетягніть, щоб
    обертати модель — прокрутіть, щоб наблизити" під канвасом.

**Перевірено наживо:**
- `vitest`: 66/66 passed (+2 нових у `lib/glossDisplay.test.ts`: підкреслення → пробіл,
  кожен звичайний item отримує власний однотокенний `tokens`). `tsc --noEmit`, `eslint` — чисті.
- `next build`: успішний, `rootMainFiles` (Turbopack build manifest) підтверджено **не**
  містить Three.js-чанк.
- **Реальний браузерний рендер (не jsdom)**: Playwright + Chromium зі SwiftShader (`--use-gl=
  swiftshader`) проти `next start` — на відміну від `vitest`/jsdom (де WebGL відсутній і
  Avatar.tsx завжди показує чесний fallback), тут WebGL реально доступний: canvas рендериться
  (WebGL-fallback НЕ показано), кнопки швидкості видимі на сторінці, скріншот підтверджує темний
  контрастний в'юпорт і підказку про обертання. Chip-рядок з кнопками повтору не перевірено
  візуально наживо (потребує активного backend для реальної gloss-послідовності) — логіка
  покрита юніт-тестами (`groupGlossesForDisplay`, `poseForGloss`) і тим самим патерном, що вже
  верифікований у `TranslatorView.test.tsx`'s `final_prediction`-тесті.

**Known limitations:** повтор конкретного жесту скидає плеєр на один-елементну послідовність —
після відтворення аватар переходить у стан "завершено" (нейтральна поза), а не повертається до
відтворення повної попередньої послідовності; це узгоджено з очікуваною поведінкою "показати
цей жест ще раз", а не задумане як безшовне продовження. Обертання/наближення — суто
презентаційні (не впливають на самі пози/анімацію).

## Редизайн UI: червоний акцент, ілюстрація, велика картка (позапланово)

Користувач надіслав два референс-зображення (маркетинговий лендинг перекладача в
чорно-червоній палітрі, і окрему ілюстрацію "жест → мовлення" в тому ж стилі) з проханням
адаптувати UI під цей стиль, використавши другу ілюстрацію праворуч. **Важливо**: зображення,
вставлені прямо в чат (не завантажені як файл), недоступні на диску цього середовища — жодного
шляху до них не існує (перевірено: `find` по всій файловій системі не знайшов жодного нового
`.png`/`.jpg`/`.webp` за час сесії, окрім вже відомого скріншота з попереднього кроку). Тому
замість спроби (неможливого) прямого копіювання чужого stock-зображення, намальовано
оригінальну SVG-ілюстрацію в тому ж стилі (лінійна графіка, один акцентний колір), що зображує
саме функцію застосунку — жест → бульбашка з рукою → стрілка → бульбашка з текстом і
іконкою звуку — а не просто копію референсу.

- `tailwind.config.ts` — єдиний токен `brand` (раніше синій) тепер аліас на `tailwindcss/colors`'
  `red`-палітру. Оскільки кожен компонент вже послідовно використовував лише `brand-*` класи
  (жодного хардкодженого `blue-`/`indigo-` в кнопках/фокусах), ця одна зміна переафарбувала
  весь застосунок без правок по місцях. Залишки хардкодженого `indigo-*` (кнопки швидкості й
  чіпи повтору жесту в `Avatar.tsx`) і `amber-*` (бейдж мімічної граматики в `TranslatorView.tsx`)
  замінено на `brand-*` для повної узгодженості палітри; матеріали 3D-ляльки (`puppet.ts`)
  перефарбовано з індиго на червоні відтінки з тієї ж причини.
- `components/Illustration/SignToSpeech.tsx` (NEW) — оригінальна inline SVG-ілюстрація
  (людина з піднятою рукою в жесті → бульбашка-рука → стрілка → бульбашка з текстом і
  іконкою гучномовця, невеликий горщик з рослиною для духу референсу), намальована власноруч
  для цього проєкту (не сторонній stock-актив).
- `app/layout.tsx` — новий header з лого-міткою (червоне коло з іконкою `Hand` з
  `lucide-react` + текстовий wordmark), весь контент тепер всередині великої заокругленої
  картки (`rounded-[32px]`, `ring-1 ring-slate-200`) на світло-сірому тлі сторінки — той самий
  прийом "card-in-page", що й у першому референсі.
- `components/Translator/TranslatorView.tsx` — нова hero-секція над функціональною частиною:
  заголовок + короткий опис зліва, `SignToSpeech`-ілюстрація справа (адаптивно складається в
  одну колонку на мобільних).
- Побічний фікс: `components/TextInput/TextInput.tsx` — додано `min-w-0` до `<input>` у
  flex-рядку (класична flexbox-помилка: `flex-1` без `min-w-0` не дає полю стискатись нижче
  intrinsic-ширини) — на вузьких екранах (мобільний viewport, реально перевірено скріншотом
  390px) поле вводу й кнопка "Перекласти" вилазили за межі картки; не пов'язано напряму з
  кольоровим редизайном, але виявлено саме під час його living-перевірки.

**Перевірено наживо:**
- `vitest`: 66/66 passed (без регресій — кольорові/розміткові зміни не займають тестові
  запити за текстом/роллю). `tsc --noEmit`, `eslint` — чисті.
- `next build` — успішний.
- **Реальний браузерний рендер** (Playwright + Chromium, не jsdom): `next start` + скріншоти
  на 1280px (десктоп) і 390px (мобільний) — підтверджено вживу: заголовок з лого, ілюстрація
  праворуч від заголовка (складається під заголовком на мобільному), усі кнопки/акценти
  червоні, 3D-лялька і бейджі також перефарбовані, текстове поле більше не вилазить за
  межі картки на 390px після фіксу `min-w-0`.

**Known limitations:** ілюстрація — намальована в коді (не растрове зображення), тож деталізація
навмисно проста (геометричні форми, не freehand-мистецтво); якщо користувач хоче використати
саме те зображення, яке він бачив у референсі, треба завантажити його як файл (не вставляти
прямо в чат) — тоді буде доступний реальний шлях на диску для вбудовування як растрового asset.

## Кращий процедурний аватар: руки з пальцями, ноги, кращий кадр (позапланово)

Користувач: "3D-аватар зроби кращим, зараз вона хуйова" — не блокуючись далі на завантаження
зовнішньої rigged-моделі (все ще не надано), процедурна лялька (Phase 15) суттєво доопрацьована.

- `components/Avatar/puppet.ts` — повний рерайт геометрії:
  - Циліндри-примітиви (тулуб/руки) замінено на `THREE.CapsuleGeometry` — заокруглені кінці
    замість плоских торців, значно менш "коробковий" силует.
  - **Руки з пальцями**: кожна кисть (`buildHand()`) — долоня (box) + 4 пальці + відхилений
    великий палець (`CapsuleGeometry`), жорстко прикріплені до зап'ястка (кінець передпліччя).
    Окремого суглоба зап'ястка/пальців у `JointRotations` (poses.ts) немає, тож кисть рухається
    разом із передпліччям як одне ціле — не "оживлені" пальці per se, але вперше взагалі
    впізнавана кисть, а не голий стрижень.
  - **Ноги**: `buildLeg()` — стегно+гомілка (капсули) + черевик (box), додані для завершеного
    силуету (раніше тулуб буквально висів у повітрі без низу). Не анімуються (жестова мова не
    потребує рухів ніг, статичні за дизайном).
  - **Волосся й очі**: часткова сфера (`thetaLength`) поверх голови (темний матеріал) + дві малі
    сфери-очі — обличчя тепер читається як обличчя, не гола куля.
  - **Матеріали**: піджак (червоний, торс+плечі) відокремлено від шкіри (персиковий, голова +
    передпліччя + кисті — "закочені рукави"), штани (темний slate) окремо від взуття (майже
    чорний) — узгоджено з кольоровою мовою `SignToSpeech`-ілюстрації з попереднього кроку.
  - Уся геометрія побудована навколо талії як `y=0`, потім `root.position.y = 0.75` зсуває всю
    фігуру вгору так, щоб стопи опинились біля рівня "землі" — простіше, ніж перераховувати
    кожен офсет під нову систему координат.
  - Публічний API (`Puppet` interface, `applyRotations()`) **не змінився** — `poses.ts`/`player.ts`
    підключаються без правок, існуючі pose-дані (WAVE/NOD/SHAKE/HANDS_TOGETHER) працюють як і
    раніше на новому скелеті.
- `components/Avatar/Avatar.tsx` — кадрування камери й `OrbitControls` перераховано під нову,
  набагато вищу фігуру (~2.4 одиниці, ноги+волосся замість голого торса ~1.1): `camera.position`/
  `lookAt`/`controls.target` тепер орієнтовані на вертикальний центр фігури (`y≈1.2`), відстань
  збільшена, щоб голова й стопи не обрізались (перевірено емпірично скріншотами — перша спроба з
  розрахунку "на око" таки обрізала волосся зверху, виправлено після виміру реальних world-space
  координат геометрії). Канвас: `h-56` → `h-72` (менш екстремальне widescreen-співвідношення
  для тепер вищої фігури); `TranslatorView.tsx`'s `next/dynamic`-плейсхолдер синхронізовано на ту
  саму висоту, щоб уникнути стрибка лейауту під час завантаження.

**Перевірено наживо:**
- `vitest`: 66/66 passed — `puppet.test.ts` перевіряє лише структуру ієрархії/мапінг обертань
  (не конкретну геометрію чи кольори), тож пройшов без правок. `tsc --noEmit`, `eslint` — чисті.
- `next build` — успішний.
- **Реальний браузерний рендер**: Playwright + Chromium (SwiftShader) проти `next start`,
  скріншоти на кількох viewport — підтверджено вживу: повна фігура (голова з волоссям, торс,
  руки з видимими кистями, ноги, взуття) вміщується в кадр без обрізання, і в реальній верстці
  сторінки (474×288px картка), і при зумі через `OrbitControls`.

**Known limitations:** пальці статичні (не окремо анімовані — немає per-finger joint даних),
тож жест "показати руку" виглядає як кисть у нейтральному положенні, а не конкретний
handshape. Це все ще НЕ справжня УЖМ (як і раніше, позначено бейджем DEMO) — покращення суто
візуальне: впізнавана людська фігура замість примітивів, не нова анімаційна точність.

## Діагностика: "на камері не вмикається реакція на руки" (Windows, локальний запуск)

Користувач повідомив, що після успішного `npm install`/`npm run dev` індикатор видимості рук
не реагує. Найімовірніша причина, визначена аналізом коду (не відтворено наживо — це
Windows-машина користувача, не ця sandbox-сесія): `scripts/download_mediapipe_models.sh` — це
bash-скрипт, який неможливо запустити напряму з PowerShell. Без завантажених `.task`-файлів у
`models/mediapipe/`, `LandmarkExtractor` кидає `ModelNotFoundError` (`ml/preprocessing/
landmarks.py`) при першій спробі побудови — backend кешує цю помилку і на кожен кадр відповідає
чесним `{"type":"error","message":"MediaPipe model not found at ..."}` (`backend/websocket/
handler.py::_get_landmark_extractor()`), і `landmarks_status` (яке живить індикатор) взагалі
ніколи не надсилається, бо надсилається вже ПІСЛЯ успішного виклику екстрактора. Індикатор тому
назавжди лишається сірим — не тому, що дані невірні, а тому, що вони ніколи не приходять.
Користувачу дано інструкцію (у чаті) завантажити моделі вручну через PowerShell
(`Invoke-WebRequest`) або запустити скрипт через Git Bash, і перевірити точний текст помилки в
панелі "Переклад" для підтвердження діагнозу перед подальшими кроками.

## Реальна rigged/skinned 3D-модель ("Cesium Man") замість процедурної ляльки (позапланово)

Користувач попросив кращу 3D-модель, запропонувавши Sketchfab. **Sketchfab виявився недоступним
з цього sandbox-середовища** (`curl sketchfab.com` → `000`, з'єднання відхилено мережевою
політикою) — і навіть якби був доступний, безкоштовні моделі на Sketchfab зазвичай вимагають
залогінений сеанс для кнопки "Download" (cookie-based, не просте пряме посилання), тож
автоматичне завантаження звідти в будь-якому разі було б неможливим без участі користувача.
Знайдено кращу альтернативу: **офіційний репозиторій зразків моделей Khronos Group**
(`github.com/KhronosGroup/glTF-Sample-Assets`, той самий консорціум, що стандартизує сам формат
glTF) — містить реальні rigged/skinned/textured моделі з дозвільними ліцензіями, доступні напряму
через `raw.githubusercontent.com` (цей хост доступний з sandbox) без авторизації. Обрано
**"Cesium Man"** (© 2017 Cesium, **CC BY 4.0** — вимагає лише атрибуції, дозволяє комерційне
використання): реальний скін-меш з текстурою, скелет із 19 кісток (торс/шия/руки/ноги),
438 КБ (`.glb`, самодостатній файл).

**Це НЕ проста заміна геометрії** — кістки цієї моделі мають власні, авторські локальні системи
координат (не ті самі умовні осі, що в процедурної ляльки), тож напряму переносити числа з
`poses.ts` було неможливо. Перші спроби емпіричного підбору осей через скріншоти дали
**суперечливі результати** (той самий тест по-різному "читався" на різних масштабах кадру) —
замість продовжувати вгадувати, використано точні числові world-space координати зап'ястка
(`bone.getWorldPosition()`) для кожного тестового кута замість очного порівняння скріншотів:
підтверджено, що `Y`-обертання на цьому рігу НЕ монотонно "піднімає руку" залежно від знаку (як
здавалось на око), а `X`- та `Z`-обертання в СВІТОВИХ координатах (а не локальних осях кістки!)
дають чисту, передбачувану, симетричну поведінку.

- **`applyWorldSwing()`** (`components/Avatar/riggedPuppet.ts`) — коректний підхід до ретаргетингу:
  замість `bone.rotation.set(x,y,z)` (перезаписує bind-обертання і залежить від невідомих
  локальних осей кістки), обчислює потрібне обертання у **світових координатах** і конвертує
  його в локальний простір кістки через **поточний** світовий кватерніон її батька
  (`parent.getWorldQuaternion()`) — коректно незалежно від того, як саме автор рігу орієнтував
  локальні осі цієї конкретної кістки, і коректно композується по всьому ланцюжку (плече→лікоть)
  без потреби вручну балансувати знаки для кожної пари кісток.
- **`ml/tests`-еквівалент для фронтенду**: `riggedPuppet.test.ts` (4 тести) перевіряє саму
  математику `applyWorldSwing()` на синтетичній ієрархії `THREE.Bone` (без завантаження реальної
  моделі чи WebGL) — включно з кейсом "обертання навколо світового X переміщує точку зі світового
  Y до світового Z **незалежно від довільного обертання батьківської кістки**" — це і є
  формальне підтвердження, що підхід дійсно не залежить від локальних осей, не лише "виглядає
  правильно на одному скріншоті".
- **`components/Avatar/riggedPoses.ts`** (NEW) — окрема таблиця жестів для цього рігу (той самий
  тип `Pose`/`JointRotations` з `poses.ts`, перевикористаний як контейнер, а не тому що числа
  означають те саме). Значення підібрані емпірично через headless Chromium з точним читанням
  world-space координат (не навмання): T-pose (руки в сторони) — це bind-поза моделі, тож
  "нейтральна" поза (`RIG_NEUTRAL_POSE`) потребує world-Z свінгу (~1 рад, дзеркально по знаку
  для лівої/правої руки), щоб руки природно звисали, а не стирчали в сторони.
- **`components/Avatar/player.ts`** — `GlossPlayer` тепер приймає **опціональні** `neutralPose`/
  `poseLookup` через конструктор (за замовчуванням — точнісінько ті самі, що й раніше:
  `NEUTRAL_POSE`/`poseForGloss` із `poses.ts`), тож уся timing/transition/wobble-логіка
  повторно використовується для обох "бекендів" аватара без дублювання коду. Усі існуючі 10
  тестів `player.test.ts` пройшли **без жодної зміни** після рефакторингу — підтверджено, що
  дефолтна поведінка для процедурної ляльки не зачеплена.
- **`components/Avatar/Avatar.tsx`** — процедурна лялька будується одразу (як і раніше, нуль
  мережевих залежностей, завжди на екрані з першого кадру), а `loadRiggedPuppet()` (асинхронний
  `GLTFLoader`) запускається паралельно; коли/якщо він завершується успішно — сцена і плеєр
  "гаряче" замінюються на rigged-версію (окреме кадрування камери під реальні виміряні
  world-space розміри моделі: ~1.5 одиниці зростом проти ~2.4 у процедурної). **Чесний fallback**
  (той самий принцип, що й скрізь у проєкті): якщо завантаження впаде (мережа, недоступний файл,
  несподівана структура glTF) — `catch` просто лишає вже показану процедурну ляльку, лише
  `console.warn`, аватар ніколи не лишається порожнім чи зламаним.
- Атрибуція ліцензії (CC BY 4.0 вимагає) — малий підпис під канвасом ("Модель: "Cesium Man" (CC
  BY 4.0, cesium.com)"), з'являється лише коли rigged-модель реально активна.
- `frontend/public/avatar/CesiumMan.glb` — модель лежить у `public/`, віддається Next.js як
  статичний файл (`/avatar/CesiumMan.glb`), без бекенд-залежності.

**Перевірено наживо:**
- `vitest`: 70/70 passed (+4 нових `riggedPuppet.test.ts`, 0 регресій у решті). `tsc --noEmit`,
  `eslint` — чисті.
- `next build` — успішний.
- **Повний реальний E2E через справжній production-білд** (не мок аватара, лише мокнутий
  backend-запит, оскільки в цьому sandbox немає живого FastAPI): Playwright + Chromium проти
  `next start`, з перехопленим `POST /translate/text-to-gloss` (повертає `{"gloss_sequence":
  ["PRIVIT"]}"`), реальний ввід тексту "Привіт" через `TextInput` → реальний клік "Перекласти" →
  скріншот підтверджує: rigged-модель завантажилась (підпис атрибуції видимий), фігура стоїть у
  природній позі "руки вздовж тіла" (не T-pose), і під час "PRIVIT" права рука реально
  піднімається зі зігнутим ліктем — саме той жест, що й було заплановано, побачений на
  справжньому кадрі рендера, не описаний на словах.

**Known limitations:** ретаргетинг покриває лише 5 demo-glosses (ті самі, що й у процедурної
ляльки — `PRIVIT`/`TAK`/`NI`/`DYAKUYU`/`BUD_LASKA`); пальці цього рігу не мають окремих кісток
(як і в geometриної руки процедурної ляльки), тож жоден з двох "бекендів" ще не показує
конкретні handshape. Поза "руки разом" (`DYAKUYU`/`BUD_LASKA`) на цьому рігу виглядає як "руки
підняті до центру", не буквально складені долоні — прийнятний рівень наближення для DEMO-системи,
як і оригінальні процедурні пози. Той самий `applyWorldSwing()`-підхід можна застосувати до
будь-якої іншої rigged-моделі з людським скелетом у майбутньому — головна складність (розбір
конвенції локальних осей конкретного рігу) саме та, яку цей підхід усуває.

## Минулий час, іменник-підмет, часові прислівники — "Машина їхала вчора ввечері." (позапланово)

Користувач дав конкретний приклад бажаного речення: "машина їхала вчора ввечері" — і до цього
запиту рушій підтримував **лише** речення з займенником-підметом у теперішньому часі
(`[PRONOUN, VERB, NOUN?]`). Це вимагало трьох реальних граматичних розширень, не одного:

- **Іменник у ролі підмета** (`[NOUN, VERB]`, напр. `["CAR","RIDE"]` → "Машина їде.") — раніше
  іменник міг бути лише додатком. У теперішньому часі жодних ускладнень: українська 3-я особа
  однини не залежить від роду ("машина їде" так само, як "він їде"), тож просто береться форма
  `verb.conjugation["3sg"]`.
- **Минулий час** — і ось тут є реальна лінгвістична складність, розв'язана чесно, а не
  вгадуванням: українське минуле не відмінюється за особою (як теперішнє), а за **родом/числом**
  підмета (masc/fem/neut/plural). Для іменника-підмета рід — фіксована лексична властивість
  слова (`NounEntry.gender`, заповнено для всіх 24 іменників), тож завжди відомий. Для
  займенника — **він/вона/ми/ви/вони** мають однозначний рід (він→masc, вона→fem, а множина —
  ми/ви/вони — взагалі не розрізняє роду в минулому часі: "ми їхали"/"ви їхали"/"вони їхали"
  однакові). Але **я/ти** справді неоднозначні: "я їхав" чи "я їхала" залежить від статі мовця,
  чого gloss-послідовність принципово не кодує. Замість вгадувати (порушуючи "no fake AI"),
  `PronounEntry.past_gender = None` саме для I/YOU, і `compose_sentence()` чесно кидає
  `UnsupportedPatternError` ("ambiguous") для минулого часу з цими двома займенниками — решта
  п'ять (він/вона/ми/ви/вони) працюють коректно. Реалізовано як окрема gloss-мітка
  `TENSE_PAST_GLOSS = "PAST"` (за тим самим принципом, що й заперечення `NOT`) — жестові мови
  зазвичай не відмінюють сам жест-дієслово за часом, а позначають час окремим знаком/контекстом,
  тож це не довільне спрощення, а лінгвістично доречний вибір.
- **Часові прислівники** (`ADVERBS`: вчора/сьогодні/завтра/вранці/ввечері/вночі/зараз) —
  незмінні слова, що йдуть в кінці речення (0 чи більше поспіль: "вчора ввечері").
- Новий гол — `RIDE` ("їхати", їхати транспортом) — окреме від уже наявного `GO` ("іти", пішки),
  реальна українська відмінність, якої немає в англійському "go".

Повний конвеєр: `[SUBJECT(pronoun|noun), (NOT)?, (PAST)?, VERB, (OBJECT)?, (ADVERB)*]` в обох
напрямках (`gloss_to_text.py`/`text_to_gloss.py`) — `PAST`-маркер розпізнається в
`text_to_gloss.py` через окремий `_PAST_VERB_INDEX` (кожна минула форма дієслова, напр. "їхала",
розгортається у ДВА gloss-токени `[PAST, RIDE]`, не один).

**Перевірено наживо:** `python3 -m pytest ml/tests/test_gloss_to_text.py
ml/tests/test_text_to_gloss.py ml/tests/test_lexicon_expansion.py` — **3528 passed** (було 2655
до розширення; +873 нових, переважно вичерпний перебір: усі 24 іменники-підмети × 16 дієслів
(present), усі 5 однозначних займенників × 16 дієслів (past), усі 24 іменники × 16 дієслів
(past) — round-trip через `compose_sentence`→`parse_gloss_sequence`, той самий підхід
вичерпного перебору, що й у `test_lexicon_expansion.py` раніше). Існуючі 2 monkeypatch-тести
(`test_verb_missing_a_conjugation...`, `test_verb_governing_a_case...`) оновлено на нові
обов'язкові поля (`past={}`, `gender="masc"`) — самі тести й далі перевіряють те саме. `ruff
check` — чисто. Точний приклад користувача перевірено буквально:
`compose_sentence(["CAR","PAST","RIDE","YESTERDAY","EVENING"]) == "Машина їхала вчора ввечері."`
і round-trip назад дає той самий gloss-список.

- `components/Avatar/Avatar.tsx` — нова кнопка "▶ Переглянути все" поруч із чипами окремих
  жестів: перезапускає всю поточну gloss-послідовність з початку на вимогу (не чекаючи нового
  перекладу) — доповнює вже наявні кнопки "повторити один жест" можливістю переглянути **всі**
  жести один за одним підряд, за запитом користувача.

**Known limitations:** охоплення `[NOUN, VERB]`/минулого часу — той самий вузький лексикон (24
іменники, 16 дієслів), не довільний текст. Минулий час для я/ти навмисно не підтримується (а не
забутий) — щоб додати, знадобиться явний спосіб дізнатись стать мовця/співрозмовника (напр.
перемикач в UI), а не вгадування. Майбутній час і доконаний/недоконаний вид дієслова також поки
не реалізовані.

## Прибрано англійські gloss-коди з UI — тепер справжня українська (позапланово)

Користувач: "у перекладі — забрати написання слів англійською". Виявлено реальну проблему: UI
показував внутрішні gloss-ідентифікатори (`WANT`, `CAR`, `RIDE` — англійські слова, використані
як програмні коди з самого початку проєкту) напряму користувачу — і в панелі "Текст/Голос →
Жести" (`components/Transcript`), і в підписі поточного жесту та списку "Немає анімації для"
під 3D-аватаром. Це не було перекладом англійською — це витік внутрішньої реалізації в UI.

- **`ml/nlp/gloss_to_text.py`** — нова `gloss_display_labels()`: gloss-послідовність → список
  `(український_текст, чи_дактилологія)` для кожного токена (займенник→лема, дієслово→
  інфінітив, іменник→називний відмінок, прислівник/стендалон→власний текст, заперечення→"не",
  дактилологія→розшифроване слово). `TENSE_PAST_GLOSS` не має власної української форми (це
  граматичний маркер, не слово — див. docstring `lexicon.py`) і свідомо пропускається, а не
  вигадується placeholder.
- **`ml/nlp/lexicon.py`** — `VerbEntry` отримав обов'язкове поле `infinitive` (словникова форма,
  напр. "хотіти", а не одна з відмінюваних форм) — заповнено для всіх 16 дієслів.
- **`POST /translate/text-to-gloss`** тепер повертає, крім `gloss_sequence`, ще й
  `gloss_labels` (український підпис + прапорець дактилології на кожен елемент) і
  `composed_text` (повне українське речення через уже наявний `compose_sentence()`, або `null`,
  якщо послідовність не складає граматично підтриманого паттерна — але `gloss_labels` і тоді
  показує, що саме зрозуміло, слово за словом).
- **`components/Transcript`** — тепер показує **справжнє українське речення** жирним зверху
  (коли доступне), і чипи з українськими словами (не gloss-кодами) знизу.
- **`frontend/lib/glossLabels.ts`** (NEW) — статична таблиця українських підписів (дзеркалить
  `lexicon.py`'s поверхневі форми), потрібна окремо від API-відповіді для 3D-аватара: його
  render loop оновлює підпис поточного жесту щокадру синхронно, без мережевого запиту.
  `lib/glossDisplay.ts`'s `formatGlossLabel()` тепер реально перекладає (через цю таблицю), а
  не просто заміняє підкреслення на пробіл, як робив раніше.
- Побічний, але важливий фікс: `TENSE_PAST_GLOSS` ("PAST") тепер явно відфільтровується з
  послідовності, яку бачить 3D-аватар (`components/Avatar/Avatar.tsx`) — до цього фіксу минулий
  час, доданий щойно в позапланові секції вище, змусив би аватар безглуздо "зависати" на
  неанімованому "жесті PAST" на весь `HOLD_SECONDS` і чесно, але оманливо, писати його в
  "Немає анімації для: PAST" (це не жест і не пропущена анімація — це граматичний маркер, який
  ніколи не мав відображатися взагалі).

**Перевірено наживо:**
- `pytest`: `ml/` — +5 нових тестів на `gloss_display_labels`, 3533 passed. `ruff check` — чисто.
- Функцію ендпоінта `text_to_gloss()` викликано напряму (Python-рівень, без TestClient —
  numpy/mediapipe не встановлені саме в цьому sandbox, окреме від коду обмеження середовища, не
  пов'язане зі змінами) на реальних прикладах, включно з точним прикладом користувача — підтверджено
  коректний JSON з `gloss_labels`/`composed_text`.
- `vitest`: 73/73 passed (+5 нових). `tsc --noEmit`, `eslint` — чисті.
- **Реальний E2E через справжній production-білд**: Playwright + Chromium проти `next start` з
  мокнутим `/translate/text-to-gloss` (реальний backend недоступний у цьому sandbox), реальний
  ввід "Машина їхала вчора ввечері" через `TextInput` → скріншот підтверджує: повне речення
  "Машина їхала вчора ввечері." жирним, чипи "машина"/"їхати"/"вчора"/"ввечері" українською,
  підпис аватара "машина" українською, "Немає анімації для: машина, їхати, вчора, ввечері" —
  **жодного англійського слова на сторінці** (перевірено програмно: `/\bCAR\b/`, `/\bRIDE\b/`,
  `/\bPAST\b/` не знайдено в тексті сторінки).

**Known limitations:** таблиця в `glossLabels.ts` — статичний дублікат `lexicon.py`'s даних
(потрібен для синхронного рендеру аватара щокадру); за відсутності запису в таблиці — чесний
fallback (підкреслення → пробіл), а не вигадана "схожа" форма.

## Аватар більше не засмічується камерою; фікс голосового вводу (позапланово)

Користувач показав скріншот: під 3D-аватаром — довжелезний ряд чипів `NI`/`TAK`/`BUD LASKA`,
що повторюються десятки разів і жодним чином не пов'язані з реченням, яке щойно ввели текстом.
Причина: `TranslatorView.tsx` мав `useEffect`, що на кожен підтверджений камерою жест
(`final_prediction`) **дописував** його в `recognizedGlossesRef` (без обмеження довжини) і
перезаписував `avatarGlossSequence` цим списком. Оскільки checkpoint розпізнавання натренований
виключно на синтетичних даних (немає жодного реального датасету УЖМ — задокументовано ще з
Phase 8), він на реальному відео підтверджує ledger випадкові жести з 5 демо-класів мало не
безперервно — і кожне таке підтвердження заповнювало аватар сміттям, витісняючи те, що
користувач насправді хотів перекласти.

- `components/Translator/TranslatorView.tsx` — цей `useEffect` і `recognizedGlossesRef`
  повністю видалено. `avatarGlossSequence` тепер встановлюється **лише** всередині
  `handleTranslate()` — тобто аватар показує рівно те речення/слова, які користувач щойно ввів
  текстом або голосом вище, і нічого більше. Панель "Переклад" (лайв-статус камери) як і раніше
  показує сирі WS-повідомлення — це окрема, свідомо лишена функція (живий фідбек із камери), не
  пов'язана з аватаром.
- `hooks/useSpeechRecognition.ts` — окремо знайдено й виправлено реальний баг: виклик
  `recognition.start()` не був обгорнутий у `try/catch`. Chrome синхронно кидає
  `InvalidStateError`, якщо `start()` викликати повторно до завершення попередньої сесії — без
  `try/catch` це вилітало неспійманим винятком, і клік на "Голос" просто нічого не робив, без
  жодного повідомлення про помилку (виглядало як "голос узагалі не працює").

**Перевірено наживо:**
- `vitest`: 74/74 passed (+1 новий тест на кинутий `start()`). `tsc --noEmit`, `eslint` — чисті.
- **Реальний E2E через справжній production-білд**: Playwright + Chromium проти `next start`,
  підмінений `WebSocket` на сторінці, що імітує 8 підряд "підтверджених камерою" жестів
  (точнісінько як демо-модель у реальності) — підтверджено програмно: **0 чипів** з'явилось під
  аватаром, немає "Переглянути все", немає "Немає анімації для" — аватар лишається чистим,
  доки користувач сам не перекладе щось текстом/голосом. Панель "Переклад" при цьому й далі
  коректно показує останнє WS-повідомлення (`[DEMO] BUD_LASKA`) — це підтверджує, що живий
  camera-фідбек не зламано, лише прибрано його небажаний вплив на аватар.
- **Голосовий ввід**: реальний Chromium із дозволом на мікрофон і `webkitSpeechRecognition`
  підтверджено доступний (`Browser has SpeechRecognition API: true`). Спроба реального
  розпізнавання в цьому sandbox зависає/відхиляється мережею (Chrome стрімить аудіо на сервери
  Google для обробки, а мережева політика sandbox це блокує — `net::ERR_CONNECTION_REFUSED`) —
  це обмеження тестового середовища, не підтвердження чи спростування причини проблеми
  користувача, але `try/catch`-фікс усуває один реальний і відтворюваний клас багів незалежно
  від мережі.

**Known limitations:** голосовий ввід лишається залежним від того, чи браузер користувача
підтримує Web Speech API (Chrome/Edge — так, Firefox — ні) і чи його мережа/антивірус/VPN не
блокують запити Chrome до серверів розпізнавання Google — жодне з цього не є чимось, що можна
виправити кодом застосунку.

## Оверлей реальних MediaPipe-точок на відео (позапланово)

Користувач: "на відео не відображається індикатори на самих руках як в медіапайп" — до цього
`LandmarkIndicator` показував лише булеві "рука видна: так/ні" крапки збоку від відео, а не
реальні точки суглобів прямо на кадрі, як у власних демо MediaPipe.

- **`backend/websocket/protocol.py`** — `LandmarksStatusMessage` отримав три нові опціональні
  поля: `left_hand_points`/`right_hand_points`/`pose_points` (`list[tuple[float, float]] | None`).
  Це **сирі** (x, y) координати в системі MediaPipe [0, 1] — до центрування/масштабування
  `ml/preprocessing/normalization.py` (те, що бачить модель, не годиться для малювання на живому
  відео: там координати центровані відносно долоні, а не кадру). `face` свідомо не включено —
  478 точок обличчя нікому не потрібні для цієї функції.
- **`backend/websocket/handler.py`** — новий хелпер `_xy_points()` бере ці координати з
  `raw_landmarks` (об'єкт **до** нормалізації, який уже обчислювався щокадру) і кладе в
  `LandmarksStatusMessage`. `None` (не порожній список), коли модальність не виявлено цього
  кадру — та сама чесна конвенція, що й у булевих полях.
- **`frontend/types/api.ts`** — `LandmarksStatusMessage` дзеркалить нові поля (`LandmarkPoint`
  = `[number, number]`).
- **`frontend/lib/landmarkOverlay.ts`** (NEW) — чиста, тестована без canvas логіка: власна
  реалізація стандартної 21-точкової топології руки MediaPipe (`HAND_CONNECTIONS`) і
  верхньої частини топології пози (`POSE_CONNECTIONS` — плечі/лікті/зап'ястя/стегна, без ніг,
  не релевантно для жестової мови); `computeObjectCoverTransform()` — та сама математика, яку
  сам браузер застосовує для CSS `object-fit: cover`, потрібна тому, що відео показується в
  боксі `aspect-video` (16:9), а нативний потік камери зазвичай 4:3 — без цього перерахунку
  точки "пливли" б відносно реальних пальців на будь-якому екрані, де відео обрізається.
- **`frontend/components/Camera/Camera.tsx`** — новий опціональний проп `landmarksStatus`;
  `<canvas>` абсолютно спозиціонований поверх `<video>`, розмір синхронізується з реальним CSS
  боксом через `ResizeObserver` (не жорстко закодований), малює скелет прямо на кадрі щоразу,
  коли приходить нове `landmarks_status` — права рука зеленим, ліва оранжевим, поза блакитним
  (різні кольори, як у власних демо MediaPipe).
- **`frontend/components/Translator/TranslatorView.tsx`** — прокидає `landmarksStatus` з
  `useWebSocket()` в `<Camera>` (той самий стан, який уже живив старий булевий індикатор —
  жодних нових мережевих запитів).

**Перевірено наживо:**
- `pytest`: `backend/` — 32/32 passed (включно з новим тестом, що перевіряє рівно 21 точку для
  руки і 33 для пози при частковому виявленні). `ml/` — 3635/3635 passed. `ruff check` на всіх
  змінених файлах — 3 попередження `I001` (порядок імпортів), **усі підтверджено наявними ще до
  цих змін** (звірено через `git stash` + повторний прогін на чистій версії) — не чіпав, як і
  раніше задокументований подібний випадок з `test_translate_route.py`.
- `vitest`: 81/81 passed (+7 нових: чиста математика `computeObjectCoverTransform`/
  `drawLandmarksOverlay` без canvas, і wiring-тест `Camera` з реальним `landmarksStatus`).
  `tsc --noEmit`, `eslint` — чисті.
- **Реальний E2E через справжній production-білд**: Playwright + Chromium (з
  `--use-fake-device-for-media-stream`, реальний синтетичний відеопотік 640×480) проти
  `next start`, підмінений `WebSocket` шле реальну форму `landmarks_status` з 21 точкою правої
  руки. Підтверджено програмно, читаючи піксельні дані самого `<canvas>` (`getImageData`):
  overlay-канвас (450×253 CSS-пікселів реального боксу) отримав **1126 непрозорих пікселів**
  рівно там, де очікується скелет руки — не просто "код виконався без помилок", а підтверджене
  реальне малювання на реальному canvas у реальному браузері.

**Known limitations:** оверлей малює лише те, що реально виявив MediaPipe цього кадру (чесно,
як і булеві індикатори) — на демо-checkpoint (синтетичні дані) самі координати точок так само не
є "справжнім" розпізнаванням жесту, лише реальним виявленням положення руки в кадрі; це різні
речі, і оверлей не видає одне за інше.

## Backpressure для кадрів: зростаюча затримка індикаторів на локальному бекенді (позапланово)

Користувач (локальний бекенд): індикатори на відео відстають від реальної картинки приблизно на
**7 секунд**, причому відео саме по собі йде нормально — відстають саме позначки/індикатори.

Корінна причина знайдена і відтворена: `websocket/handler.py`'s основний цикл читає рівно одне
клієнтське повідомлення за раз (`await websocket.receive_text()`) і повністю обробляє його
(реальне вилучення landmarks через **три** MediaPipe Tasks моделі — руки, поза, обличчя,
остання найважча — плюс нормалізація, і за готовності чекпойнта ще LSTM inference), перш ніж
прочитати наступне. `extractor.extract`/`inference_service.predict` вже винесені в
`asyncio.to_thread` (не блокують інші з'єднання), але **це саме з'єднання** обробляє кадри
строго послідовно. Тим часом `hooks/useCamera.ts`'s capture loop слав новий кадр на власному
таймері (~83 мс при 12 FPS) **незалежно від того, чи бекенд встиг відповісти на попередній** —
на повільному (локальному, без GPU) бекенді, де реальна обробка одного кадру займає помітно
довше за 83 мс, кадри накопичувались у черзі сокета швидше, ніж бекенд їх розбирав, і кожна
наступна `landmarks_status` описувала дедалі старіший кадр — затримка не просто "повільна", а
**необмежено зростає** з часом, точно як повідомив користувач.

- **`frontend/hooks/useWebSocket.ts`** — додано `awaitingFrameResponseRef`: `sendFrame()` тепер
  відкидає (не ставить у чергу) новий кадр, якщо термінальна відповідь на попередній
  (`prediction`/`final_prediction`/`error`; `landmarks_status` — проміжна, ще не рахується)
  ще не прийшла. На з'єднання завжди щонайбільше один кадр "у польоті" — на повільному бекенді
  це означає нижчу, але **живу**, частоту оновлення індикаторів, а не зростаючий лаг.

**Перевірено наживо:**
- `vitest`: 82/82 passed (+1 новий тест на відкидання кадру, поки очікується відповідь).
  `tsc --noEmit`, `eslint`, `next build` — чисті.
- **Реальний E2E через справжній production-білд**: Playwright + Chromium проти `next start`,
  підмінений `WebSocket` імітує бекенд, що відповідає через 800 мс на кадр (значно повільніше
  за 83-мс інтервал захоплення) — за 5 реальних секунд без цього фіксу пішло б ≈60 кадрів
  (`5000 / 83`), підтверджено програмно: пішло рівно **6** — обмежено реальною швидкістю
  "бекенду", а не таймером захоплення.

**Known limitations:** це усуває *необмежене зростання* затримки, а не саму затримку —
на повільному локальному CPU з увімкненими всіма трьома детекторами (руки+поза+обличчя)
індикатори все одно оновлюватимуться з певним фіксованим лагом (в прикладі вище — до ~800 мс на
кадр), просто він більше не накопичується нескінченно. Обличчя (найважча з трьох моделей,
478 точок) вмикається `features_face: bool = True` в `app/core/config.py` і використовується
лише для non-manual граматики (брови) — не для оверлея (той свідомо не малює обличчя). Якщо ця
фіча не потрібна, `FEATURES_FACE=false` в оточенні бекенда прибере найважчу з трьох моделей і
пришвидшить кожен кадр — свідомо не вимкнено за замовчуванням тут, бо це реальна втрата фічі,
а не суто перформанс-налаштування, тож рішення лишається за користувачем.
