import { ConnectionStatus } from "@/components/ConnectionStatus";

export default function TranslatorPage(): React.ReactElement {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Перекладач УЖМ</h1>
        <ConnectionStatus />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Камера
          </h2>
          <div className="flex aspect-video items-center justify-center rounded-xl bg-slate-100 text-sm text-slate-400">
            Камера буде підключена в Phase 4 (getUserMedia, FPS/resolution control)
          </div>
        </section>

        <section className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Переклад
          </h2>
          <div className="flex flex-1 items-center justify-center rounded-xl bg-slate-100 p-4 text-center text-sm text-slate-400">
            Розпізнавання жестів у реальному часі з&rsquo;явиться тут після Phase 5
            (WebSocket) та Phase 9-10 (навчена модель).
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Текст / Голос → Жести
        </h2>
        <div className="flex gap-3">
          <input
            type="text"
            disabled
            placeholder="Введіть текст... (буде активовано в Phase 14)"
            className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-400 disabled:cursor-not-allowed"
          />
          <button
            type="button"
            disabled
            className="rounded-lg bg-slate-200 px-5 py-2 text-sm font-medium text-slate-400 disabled:cursor-not-allowed"
          >
            Перекласти
          </button>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          3D Avatar
        </h2>
        <div className="flex h-40 items-center justify-center rounded-xl bg-slate-100 text-sm text-slate-400">
          Three.js avatar буде доданий у Phase 15
        </div>
      </section>
    </div>
  );
}
