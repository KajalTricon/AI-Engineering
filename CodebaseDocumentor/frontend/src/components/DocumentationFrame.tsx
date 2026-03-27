interface DocumentationFrameProps {
  markdown: string | null;
}

export default function DocumentationFrame({ markdown }: DocumentationFrameProps) {
  if (!markdown) {
    return (
      <div className="rounded-[28px] border border-[#629bb5]/35 bg-[#d6ebf3]/55 p-10 text-sm text-slate-700">
        Documentation will appear here after the repository finishes processing.
      </div>
    );
  }

  return (
    <article className="rounded-[28px] border border-[#629bb5]/30 bg-white/95 p-8 shadow-[0_20px_60px_rgba(68,127,152,0.14)]">
      <div className="prose prose-slate max-w-none whitespace-pre-wrap leading-8">
        {markdown}
      </div>
    </article>
  );
}
