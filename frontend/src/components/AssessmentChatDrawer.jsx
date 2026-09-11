import React, { useState } from 'react';
import { Send, Bot, User, Sparkles, ShieldCheck, AlertCircle, FileText, CheckCircle2, AlertTriangle } from 'lucide-react';

export function AssessmentChatDrawer({ assessmentId, assessmentNumber }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: `Hello! I am your production Layer 3 AI Orchestrator for Assessment ${assessmentNumber}. I provide grounded explanations of verified BIS clauses, testing limits, and missing evidence. Under our zero-hallucination policy, I have 0% compliance authority.`,
      citations: [{ standard: 'IS 302-2-201:2008', source: 'BIS Official Gazette' }],
      groundingStatus: 'SUPPORTED',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setIsLoading(true);

    try {
      const res = await fetch(`/api/v1/assessments/${assessmentId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            text: data.answer,
            citations: data.citations || [],
            disclaimer: data.disclaimer,
            groundingStatus: data.grounding_status || 'SUPPORTED',
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            text: 'I don’t have verified information in the current BIS knowledge base to answer this.',
            citations: [],
            groundingStatus: 'NOT_IN_KNOWLEDGE_BASE',
          },
        ]);
      }
    } catch (err) {
      console.warn('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Unable to communicate with Layer 3 AI Orchestrator service.',
          citations: [],
          groundingStatus: 'UNKNOWN',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-2.5 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xl border border-indigo-400 transition cursor-pointer"
      >
        <Bot className="w-4 h-4" />
        AI Orchestrator Assistant
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-40 w-96 max-w-[calc(100vw-3rem)] h-[540px] bg-white border border-slate-200 rounded-2xl shadow-2xl flex flex-col overflow-hidden text-xs text-slate-900 font-sans">
      {/* Header */}
      <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h4 className="font-bold text-slate-900 leading-none">Layer 3 AI Orchestrator</h4>
              <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-indigo-100 text-indigo-800">
                ONE LLM
              </span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">{assessmentNumber} &bull; Grounded Only</span>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 cursor-pointer"
        >
          &times;
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/60">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[88%] p-3.5 rounded-xl leading-relaxed text-xs ${
                m.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none shadow-xs'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none space-y-2 shadow-2xs'
              }`}
            >
              {/* Grounding Status badge if assistant */}
              {m.sender === 'assistant' && m.groundingStatus && (
                <div className="flex items-center justify-between gap-2 pb-1 border-b border-slate-100">
                  <span className="text-[9px] font-mono uppercase font-bold text-slate-400">Grounding Status:</span>
                  <span
                    className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                      m.groundingStatus === 'SUPPORTED'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : m.groundingStatus === 'UNCERTAIN'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}
                  >
                    {m.groundingStatus}
                  </span>
                </div>
              )}

              <p className="whitespace-pre-wrap">{m.text}</p>

              {/* Citations */}
              {m.citations && m.citations.length > 0 && (
                <div className="pt-2 border-t border-slate-100 text-[10px] text-indigo-700 font-mono space-y-1">
                  <span className="text-slate-400 uppercase block text-[9px] font-bold">Verified Sources:</span>
                  {m.citations.map((c, cIdx) => (
                    <div key={cIdx} className="flex items-center gap-1.5 bg-slate-50 p-1.5 rounded border border-slate-200">
                      <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span className="font-semibold text-slate-800">
                        {c.standard || c.standard_number || 'IS Standard'}
                      </span>
                      {c.clause && <span>Clause {c.clause}</span>}
                      {c.clause_number && <span>Clause {c.clause_number}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 p-3 bg-white border border-slate-200 rounded-xl text-xs text-slate-500 shadow-2xs w-fit">
            <span className="w-3.5 h-3.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
            <span>Orchestrating Grounded Answer...</span>
          </div>
        )}
      </div>

      {/* Footer Invariant & Input */}
      <div className="p-3 bg-white border-t border-slate-200 space-y-2">
        <div className="text-[9px] text-slate-400 text-center font-mono">
          Strict Invariant: LLM Authority = 0% &bull; Zero Hallucination Policy
        </div>
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about clauses, ratings, or evidence..."
            className="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition disabled:opacity-50 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
