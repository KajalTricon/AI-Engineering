interface MermaidPanelProps {
  title: string;
  description?: string | null;
  mermaid?: string | null;
}

function buildMermaidDocument(mermaid: string) {
  return `<!doctype html>
  <html>
    <head>
      <meta charset="UTF-8" />
      <style>
        body {
          margin: 0;
          padding: 24px;
          background: #d6ebf3;
          font-family: "Segoe UI", sans-serif;
        }
        .shell {
          border: 1px solid rgba(68,127,152,0.22);
          border-radius: 24px;
          background: white;
          padding: 20px;
          box-shadow: 0 18px 40px rgba(68,127,152,0.14);
        }
      </style>
    </head>
    <body>
      <div class="shell">
        <pre class="mermaid">${mermaid}</pre>
      </div>
      <script type="module">
        import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
        mermaid.initialize({ startOnLoad: true, theme: "base" });
      </script>
    </body>
  </html>`;
}

export default function MermaidPanel({
  title,
  description,
  mermaid,
}: MermaidPanelProps) {
  const diagram = mermaid || 'flowchart TD\nA["Diagram unavailable"]';

  return (
    <section className="rounded-[28px] border border-[#629bb5]/30 bg-white/95 p-8 shadow-[0_20px_60px_rgba(68,127,152,0.14)]">
      <h2 className="text-2xl font-semibold text-[#447f98]">{title}</h2>
      {description && <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">{description}</p>}
      <iframe
        className="mt-6 h-[680px] w-full rounded-[24px] border border-[#629bb5]/20 bg-[#d6ebf3]"
        srcDoc={buildMermaidDocument(diagram)}
        title={title}
      />
    </section>
  );
}
