import { FormEvent, useEffect, useState } from 'react';
import { ChevronLeft, MessageSquare, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { QAPair } from '../types';

interface QuestionPanelProps {
  history: QAPair[];
  onAsk: (question: string) => Promise<void>;
  onClose: () => void;
  projectName: string;
}

const prompts = [
  'What does this project do?',
  'How is the database connected?',
  'Where should I start reading?',
];

export default function QuestionPanel({
  history,
  onAsk,
  onClose,
  projectName,
}: QuestionPanelProps) {
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [displayed, setDisplayed] = useState<QAPair[]>(history);

  useEffect(() => {
    if (history.length === 0) {
      setDisplayed([]);
      return;
    }

    const latest = history[history.length - 1];
    const previous = history.slice(0, -1);
    let index = 0;

    setDisplayed([...previous, { ...latest, answer: '' }]);

    const timer = window.setInterval(() => {
      index += 1;
      setDisplayed([...previous, { ...latest, answer: latest.answer.slice(0, index) }]);
      if (index >= latest.answer.length) window.clearInterval(timer);
    }, 16);

    return () => window.clearInterval(timer);
  }, [history]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!input.trim() || submitting) return;

    setSubmitting(true);
    try {
      await onAsk(input.trim());
      setInput('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex h-full flex-col bg-[#447f98]">
      <div className="flex items-center justify-between border-b border-[#629bb5]/30 px-6 py-5">
        <div className="flex items-center gap-3">
          <MessageSquare className="text-[#d6ebf3]" size={18} />
          <div>
            <h2 className="text-lg font-semibold text-white">Ask about {projectName}</h2>
            <p className="text-xs text-[#dadee1]">Project-specific Q&amp;A</p>
          </div>
        </div>
        <button
          className="rounded-full border border-[#629bb5]/35 p-2 text-[#d6ebf3] transition hover:bg-[#629bb5]/20"
          onClick={onClose}
          type="button"
        >
          <ChevronLeft size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {displayed.length === 0 && (
          <div className="space-y-3">
            {prompts.map((prompt) => (
              <button
                key={prompt}
                className="block w-full rounded-[18px] border border-[#629bb5]/30 bg-[#629bb5]/12 px-4 py-3 text-left text-sm text-[#d6ebf3] transition hover:bg-[#629bb5]/18"
                onClick={() => setInput(prompt)}
                type="button"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        <div className="space-y-5">
          {displayed.map((item) => (
            <div key={item.id} className="space-y-3">
              <div className="ml-auto max-w-[85%] rounded-[18px] bg-[#d6ebf3] px-4 py-3 text-sm text-[#447f98]">
                {item.question}
              </div>
              <div className="max-w-full rounded-[22px] bg-[#d6ebf3] px-6 py-5 shadow-sm">
                <div className="prose prose-sm max-w-none text-[#447f98]">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {item.answer}
                  </ReactMarkdown>
                </div>
                {item.sources.length > 0 && (
                  <div className="mt-5 pt-4 border-t border-[#447f98]/20">
                    <p className="text-xs font-medium text-[#447f98]/80 mb-2">Sources:</p>
                    <div className="flex flex-wrap gap-2">
                      {item.sources.map((source, index) => (
                        <span
                          key={`${source}-${index}`}
                          className="rounded-full bg-[#d6ebf3] px-3 py-1.5 text-xs font-mono text-[#447f98]"
                        >
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <form className="border-t border-[#629bb5]/30 p-5" onSubmit={handleSubmit}>
        <div className="flex gap-3 rounded-[22px] bg-white px-4 py-3">
          <input
            className="min-w-0 flex-1 bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
            onChange={(event) => setInput(event.target.value)}
            placeholder="How is authentication handled?"
            value={input}
          />
          <button
            className="rounded-full border border-white/75 bg-[#d6ebf3] p-2 text-[#224e63] shadow-[0_10px_20px_rgba(68,127,152,0.14)] transition hover:bg-white"
            disabled={!input.trim() || submitting}
            type="submit"
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
 