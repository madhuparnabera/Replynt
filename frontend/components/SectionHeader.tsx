export function SectionHeader({ title, eyebrow }: { title: string; eyebrow?: string }) {
  return (
    <div>
      {eyebrow ? <div className="text-xs uppercase tracking-[0.22em] text-blue-300">{eyebrow}</div> : null}
      <h2 className="mt-1 text-2xl font-semibold text-white">{title}</h2>
    </div>
  );
}
