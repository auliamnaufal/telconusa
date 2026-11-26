export function PlaceholderPage({ title, issue }: { title: string; issue: string }) {
  return (
    <div>
      <h1 className="font-display text-2xl font-extrabold text-slate-900">{title}</h1>
      <p className="mt-2 rounded-lg border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        Layar ini belum dikerjakan ({issue}).
      </p>
    </div>
  );
}
