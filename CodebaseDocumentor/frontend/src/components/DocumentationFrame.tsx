import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
      <div className="prose prose-slate max-w-none
        prose-headings:font-semibold prose-headings:text-slate-800
        prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
        prose-p:text-slate-700 prose-p:leading-7
        prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
        prose-code:bg-slate-100 prose-code:text-pink-600 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-mono
        prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-pre:rounded-xl prose-pre:overflow-x-auto
        prose-blockquote:border-l-4 prose-blockquote:border-blue-300 prose-blockquote:bg-blue-50 prose-blockquote:px-4 prose-blockquote:py-1 prose-blockquote:text-slate-600 prose-blockquote:not-italic
        prose-ul:list-disc prose-ol:list-decimal
        prose-li:text-slate-700
        prose-table:border-collapse prose-th:bg-slate-100 prose-th:px-4 prose-th:py-2 prose-td:px-4 prose-td:py-2 prose-td:border prose-td:border-slate-200
        prose-strong:text-slate-800 prose-strong:font-semibold
        prose-hr:border-slate-200">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {markdown}
        </ReactMarkdown>
      </div>
    </article>
  );
}

 