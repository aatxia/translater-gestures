# UKSL Translator

Вебзастосунок для двостороннього перекладу **української жестової мови (УЖМ)** у реальному часі:
жести → текст → озвучка, і текст/голос → жести → 3D avatar.

Детальна архітектура: [`docs/architecture.md`](docs/architecture.md)
Поточний статус проєкту: [`PROJECT_STATUS.md`](PROJECT_STATUS.md)

## Технологічний стек

- **Frontend**: Next.js, TypeScript, Tailwind CSS, WebSocket, WebRTC (camera), Three.js (avatar)
- **Backend**: Python, FastAPI, WebSocket, Pydantic
- **ML/CV**: MediaPipe (hands/pose/face landmarks), PyTorch (BiLSTM/GRU baseline → Transformer),
  Hugging Face Transformers (NLP gloss→text), Video-JEPA (experimental)
- **Avatar**: Three.js + предзадані анімації, мапінг gloss → animation ID
- **Infra**: Docker / docker-compose (з Phase 2+)

## Структура репозиторію

```
frontend/    Next.js застосунок (камера, WS клієнт, UI, 3D avatar)
backend/     FastAPI сервер, WebSocket protocol, оркестрація сервісів
ml/          CV preprocessing, temporal models, NLP, fingerspelling, evaluation
avatar/      3D модель, анімації, gloss→animation mappings
data/        raw/processed відео, annotations, signer-independent splits
models/      checkpoints (не в git)
scripts/     допоміжні скрипти (напр. створення dataset split)
tests/       backend / ml / frontend / integration тести
docs/        технічна документація
docker/      Dockerfile'и для кожного сервісу
configs/     YAML конфігурації (feature toggles, model, camera)
experiments/ результати ML-експериментів
```

## Встановлення

```bash
git clone https://github.com/aatxia/translater-gestures.git
cd translater-gestures
cp .env.example .env
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend буде доступний на `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend буде доступний на `http://localhost:3000`.

### ML — dataset, training, inference

Preprocessing pipeline (MediaPipe landmark extraction, normalization,
augmentation) is ready — see [`ml/README.md`](ml/README.md) for setup and
usage. Dataset pipeline and model training are not implemented yet
(see `PROJECT_STATUS.md`). Тренування моделей передбачається на Google Colab
(GPU), checkpoint переноситься в `models/checkpoints/` і використовується
локально через `SignRecognizer`.

## Roadmap (Phases)

| # | Фаза | Статус |
|---|------|--------|
| 1 | Repository + architecture | ✅ Done |
| 2 | Backend FastAPI | ✅ Done |
| 3 | Frontend Next.js | ✅ Done |
| 4 | Camera | ✅ Done |
| 5 | WebSocket | ✅ Done |
| 6 | MediaPipe preprocessing | ✅ Done |
| 7 | Landmark extraction | ⏳ Next |
| 8 | Dataset pipeline | ⏳ |
| 9 | Baseline ML model | ⏳ |
| 10 | Real-time inference | ⏳ |
| 11 | Sign → gloss | ⏳ |
| 12 | Gloss → Ukrainian NLP | ⏳ |
| 13 | Speech-to-text | ⏳ |
| 14 | Text → gloss | ⏳ |
| 15 | Avatar | ⏳ |
| 16 | Fingerspelling | ⏳ |
| 17 | Face/facial grammar | ⏳ |
| 18 | Transformer / advanced model | ⏳ |
| 19 | Video-JEPA experiment | ⏳ |
| 20 | Evaluation | ⏳ |
| 21 | Optimization | ⏳ |
| 22 | Final integration | ⏳ |

Детальний технічний план кожної фази — у `PROJECT_STATUS.md`, який оновлюється після кожної фази.

## Принципи проєкту

- Жодних fake-заглушок ML там, де реалізація можлива вже зараз.
- Кожен ML-компонент — за абстрактним інтерфейсом, взаємозамінний через конфіг.
- Signer-independent split для чесної оцінки generalization.
- Приватність: сирі відео не зберігаються і не логуються за замовчуванням.
