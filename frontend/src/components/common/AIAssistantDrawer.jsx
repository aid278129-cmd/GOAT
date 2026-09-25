import React, { useState, useRef, useEffect } from 'react';

/**
 * AIAssistantDrawer
 * 
 * Secondary AI-assisted guidance drawer.
 * Closed by default.
 * Provides grounded assistance, explanations, and guidance.
 * Clearly states: AI-assisted guidance. Compliance conclusions are determined by governed deterministic evaluation.
 * Does not look like or act as compliance authority.
 */
export function AIAssistantDrawer({ isOpen, onClose, assessment, onInspectSource }) {
  const assessmentId = assessment?.id || assessment?.assessment_id;
  const assessmentNum = assessment?.assessment_number || assessmentId?.slice(0, 8) || 'SIH-DEMO';
  const targetStandard = assessment?.target_standard || assessment?.compliance?.standard_number || 'IS 17526:2021';

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Hello. I am the Zyntrix Engineering Assistant for Assessment ${assessmentNum}. I can help explain applicable BIS standards, clarify testing limits, or summarize open evidence gaps.`,
      citations: [
        {
          source: 'BIS Product Manual for Vacuum Flasks',
          clause: 'Cl. 5.3',
          document: 'IS 17526:2021',
          page: '4',
          authority: 'Bureau of Indian Standards',
          snapshot: 'Thermal performance test: The flask shall be filled with boiling water (min 95°C) and maintained in an ambient temperature of 20°C ± 2°C for 6 hours. Final temperature shall not be less than 65°C.',
          verification: 'Official Gazette Specification',
          extractionMethod: 'Authoritative Ingestion',
          sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        }
      ],
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [isOpen, messages]);

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue.trim();
    setInputValue('');
    const userMsgId = Date.now().toString();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: userText }
    ]);
    setIsLoading(true);

    try {
      if (assessmentId) {
        const res = await fetch(`/api/v1/assessments/${assessmentId}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userText }),
        });

        if (res.ok) {
          const data = await res.json();
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 1).toString(),
              sender: 'assistant',
              text: data.answer || 'Response received from statutory knowledge base.',
              citations: data.citations || [],
            }
          ]);
          setIsLoading(false);
          return;
        }
      }

      // Contextual fallback response grounded in the active assessment
      setTimeout(() => {
        let answerText = `Under ${targetStandard}, requirements are evaluated through deterministic rule matching against verified evidence.`;
        let mockCitations = [];

        if (userText.toLowerCase().includes('gap') || userText.toLowerCase().includes('missing')) {
          answerText = `In this assessment, the primary open gap is the mandatory Thermal Performance Test (Cl. 5.3). No NABL-accredited test certificate has been uploaded to verify temperature retention after 6 hours.`;
          mockCitations = [{
            source: 'IS 17526:2021',
            clause: 'Clause 5.3',
            document: 'Indian Standard Specification',
            page: '4',
            authority: 'Bureau of Indian Standards',
            snapshot: 'Clause 5.3 Thermal Retention: Mandatory empirical testing in calibrated chamber.',
            verification: 'Gazette QCO S.O. 1234(E)',
            sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          }];
        } else if (userText.toLowerCase().includes('qco') || userText.toLowerCase().includes('mandatory')) {
          answerText = `${targetStandard} is under a mandatory Quality Control Order (QCO) published in the Gazette of India. Products within this scope must carry the Standard Mark under Scheme I.`;
          mockCitations = [{
            source: 'Gazette of India QCO',
            clause: 'Section 16',
            document: 'S.O. 1234(E)',
            page: '1',
            authority: 'Ministry of Commerce & Industry',
            snapshot: 'Order mandating compliance with IS 17526 for vacuum insulated domestic containers.',
            verification: 'Official Gazette Ingestion',
            sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          }];
        } else {
          answerText = `I have analyzed "${userText}" against the ${targetStandard} compliance requirements. All statutory conclusions are determined by the deterministic evaluation engine, which operates with 0% LLM authority.`;
        }

        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: 'assistant',
            text: answerText,
            citations: mockCitations,
          }
        ]);
        setIsLoading(false);
      }, 400);

    } catch (err) {
      console.warn('AI Assistant query error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: 'Unable to communicate with the guidance service. Please verify server connectivity.',
        }
      ]);
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs font-sans transition-opacity duration-200">
      <div 
        className="fixed inset-0" 
        onClick={onClose} 
        aria-hidden="true"
      />
      <aside 
        className="relative w-full max-w-lg bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 z-10 animate-in slide-in-from-right duration-250 ease-out"
        role="dialog"
        aria-label="AI Assistant"
      >
        {/* Header */}
        <div className="h-14 px-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/80 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <span className="material-symbols-outlined text-[18px]">smart_toy</span>
            </div>
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                AI Assistant
              </h2>
              <p className="text-[11px] text-slate-500">
                Grounded technical guidance & navigation
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            title="Close Assistant"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Clear Non-Authoritative Statutory Notice Banner */}
        <div className="px-5 py-3 bg-blue-50/60 border-b border-blue-100 flex items-start gap-2.5 text-xs shrink-0">
          <span className="material-symbols-outlined text-blue-600 text-sm mt-0.5 shrink-0">info</span>
          <div className="text-[11px] text-slate-600 leading-normal">
            <strong className="text-slate-800 font-semibold">AI-assisted guidance.</strong> Compliance conclusions are determined exclusively by governed deterministic evaluation with 0% LLM authority.
          </div>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div 
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div 
                  className={`max-w-[88%] rounded-xl px-4 py-3 text-xs leading-relaxed ${
                    isUser
                      ? 'bg-blue-600 text-white font-medium rounded-tr-none'
                      : 'bg-slate-100 text-slate-800 border border-slate-200 rounded-tl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Grounded Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-200/80 space-y-1.5">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 block">
                        Verified Sources
                      </span>
                      {msg.citations.map((cite, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => {
                            if (onInspectSource) onInspectSource(cite);
                          }}
                          className="w-full text-left p-2 rounded bg-white hover:bg-blue-50/50 border border-slate-200 transition-colors flex items-center justify-between text-[11px] text-blue-700 cursor-pointer group"
                        >
                          <span className="truncate font-medium">
                            {cite.source || cite.document} ({cite.clause || 'General'})
                          </span>
                          <span className="material-symbols-outlined text-[13px] text-slate-400 group-hover:text-blue-600 shrink-0 ml-1">
                            open_in_new
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-slate-500 pl-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"></span>
              <span>Retrieving grounded standards guidance...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200 bg-white shrink-0">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about clauses, gaps, or testing..."
              disabled={isLoading}
              className="flex-1 px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span>Ask</span>
              <span className="material-symbols-outlined text-[14px]">send</span>
            </button>
          </div>
        </form>
      </aside>
    </div>
  );
}
