import Link from "next/link";
import { ConnectionStatus } from "@/components/ConnectionStatus";

export default function HomePage(): React.ReactElement {
  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-bold text-slate-900">UKSL Translator</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Двосторонній перекладач української жестової мови (УЖМ) у реальному часі:
          жести → текст → озвучка, і текст/голос → жести → 3D avatar.
        </p>
        <div className="mt-6 flex items-center gap-4">
          <Link
            href="/translator"
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
          >
            Відкрити перекладач
          </Link>
          <ConnectionStatus />
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-8">
        <h2 className="text-lg font-semibold text-slate-900">Статус проєкту</h2>
        <p className="mt-2 text-sm text-slate-600">
          Це рання стадія розробки (Phase 3). Камера, WebSocket real-time
          розпізнавання жестів та 3D avatar ще не підключені — дивись{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5">PROJECT_STATUS.md</code> у
          репозиторії для деталей по фазах.
        </p>
      </section>
    </div>
  );
}
