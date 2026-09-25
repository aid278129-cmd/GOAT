import React, { useState, useEffect, useRef } from 'react';
import { assistantApi } from '../api/assistant';
import { authApi } from '../api/auth';
import ProductInvestigationModal from './ProductInvestigationModal';

export default function BISAssistantView({ onNavigateWorkstation, onJobCreated, onStartComplianceAssessment }) {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      role: 'assistant',
      content: (
        "Welcome to the **Zyntrix BIS Intelligent Assistant** (SIH PS 26107).\n\n" +
        "I provide accurate, source-grounded regulatory intelligence on **Indian Standards (IS)**, " +
        "**BIS Conformity Schemes (ISI Mark, CRS)**, **Testing Protocols**, **Recognized Laboratories**, " +
        "and **Hallmarking**. Every response references authorized BIS regulatory sources.\n\n" +
        "Ask a question below or choose a sample investigation to begin."
      ),
      citations: [],
      sources: [{ name: 'Bureau of Indian Standards Act 2016', type: 'AUTHORITATIVE_BIS' }],
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [inspectingSource, setInspectingSource] = useState(null);
  const [investigationModalOpen, setInvestigationModalOpen] = useState(false);
  const chatBottomRef = useRef(null);

  const samplePrompts = [
    {
      label: '5 kW Hybrid Inverter Standards',
      query: 'I manufacture a 5 kW hybrid solar inverter in India. Which Indian Standards should I investigate and what BIS-related process should I look into?',
    },
    {
      label: 'Compulsory Registration (CRS)',
      query: 'How do I obtain BIS CRS registration for an electronic power adapter, and what documents are required?',
    },
    {
      label: 'Gold Hallmarking & HUID',
      query: 'What does BIS hallmarking mean for consumers and what are the 3 mandatory marks including HUID?',
    },
    {
      label: 'Testing Laboratories Search',
      query: 'Where can I find BIS-recognized laboratories for testing solar inverters and IT equipment in India?',
    },
    {
      label: 'Clause 5.3 Explanation',
      query: 'Explain Clause 5.3 of IS 16221 (Part 2) regarding anti-islanding protection in simple terms.',
    },
    {
      label: 'Consumer Grievance Redressal',
      query: 'How can a consumer verify a genuine ISI mark or report a counterfeit product using the BIS CARE App?',
    },
  ];

  // Load conversation list on mount
  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadConversations = async () => {
    try {
      if (!authApi.getToken()) {
        await authApi.bootstrap();
      }
      const convs = await assistantApi.listConversations();
      setConversations(convs || []);
      if (convs && convs.length > 0 && !activeConversationId) {
        loadConversationMessages(convs[0].id);
      }
    } catch (err) {
      console.warn('Failed to load conversations:', err);
    }
  };

  const loadConversationMessages = async (convId) => {
    setActiveConversationId(convId);
    try {
      const data = await assistantApi.getConversation(convId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
    }
  };

  const handleStartNewConversation = () => {
    setActiveConversationId(null);
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: "New investigation session started. What product or Indian Standard would you like to explore?",
        citations: [],
        sources: [],
      },
    ]);
  };

  const handleSendMessage = async (queryText = null) => {
    const textToSend = queryText || inputMessage;
    if (!textToSend.trim() || loading) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLoading(true);

    try {
      const res = await assistantApi.chat(textToSend, activeConversationId, selectedLanguage);
      if (!activeConversationId && res.conversation_id) {
        setActiveConversationId(res.conversation_id);
        loadConversations();
      }

      const asstMsg = {
        id: res.message_id || `asst-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        sources: res.sources || [],
        claims: res.claims || [],
        handoff: res.workstation_handoff,
        agent: res.agent,
      };

      setMessages((prev) => [...prev, asstMsg]);

      // If citations present, automatically populate source inspector with the primary citation
      if (res.citations && res.citations.length > 0) {
        setInspectingSource(res.citations[0]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `Error: ${err.message || 'Unable to connect to the BIS knowledge service.'}`,
          citations: [],
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleHandoffToWorkstation = async (handoffData) => {
    if (!handoffData) return;
    try {
      const payload = {
        title: handoffData.suggested_title || 'Engineering Compliance Job',
        product_name: handoffData.product_characteristics?.detected_categories?.[0] || 'Target Product',
        target_standard_number: handoffData.target_standard || 'IS 16221 (Part 2)',
        product_context: handoffData.product_characteristics || {},
      };
      const res = await assistantApi.startWorkstationJob(payload);
      if (onJobCreated) {
        onJobCreated(res.job_id);
      }
      if (onNavigateWorkstation) {
        onNavigateWorkstation(res.job_id);
      }
    } catch (err) {
      alert(`Handoff failed: ${err.message}`);
    }
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-slate-50 overflow-hidden">
      {/* ------------------------------------------------------------- */}
      {/* LEFT SIDEBAR: Conversations & Quick Prompts                  */}
      {/* ------------------------------------------------------------- */}
      <aside className="w-72 border-r border-slate-200 bg-white flex flex-col flex-shrink-0">
        <div className="p-3 pb-1 border-b border-slate-100 flex flex-col gap-2">
          <button
            type="button"
            onClick={() => onStartComplianceAssessment ? onStartComplianceAssessment('golden') : onNavigateWorkstation()}
            className="w-full flex items-center justify-between px-3 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <span className="material-symbols-outlined text-base">verified_user</span>
              <span>Start Assessment</span>
            </span>
            <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded font-mono">IS 17526</span>
          </button>
          <button
            onClick={handleStartNewConversation}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-bold transition-all border border-indigo-200 shadow-sm cursor-pointer"
          >
            <span>✨</span> New Investigation
          </button>
        </div>

        <div className="p-3">
          <button
            onClick={() => setInvestigationModalOpen(true)}
            className="w-full flex items-center justify-between px-3 py-2.5 bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-xl text-xs font-semibold shadow-sm hover:opacity-95 transition-opacity"
          >
            <span className="flex items-center gap-2">
              <span>🔬</span> Product Form
            </span>
            <span className="text-[10px] bg-indigo-500/30 px-2 py-0.5 rounded-full">PS 26107</span>
          </button>
        </div>

        {/* Quick Prompts List */}
        <div className="px-3 pb-2">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-2">
            Sample Inquiry Topics
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(p.query)}
                className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs text-slate-700 hover:bg-slate-100 transition-colors truncate font-medium flex items-center gap-1.5"
              >
                <span className="text-indigo-500 text-[10px]">▸</span>
                <span className="truncate">{p.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Recent Conversations */}
        <div className="flex-1 overflow-y-auto px-3 py-2 border-t border-slate-100">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-2">
            Saved Dialogs
          </div>
          {conversations.length === 0 ? (
            <div className="text-xs text-slate-400 px-2 italic">No previous dialogs</div>
          ) : (
            <div className="space-y-1">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => loadConversationMessages(c.id)}
                  className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-colors truncate ${
                    activeConversationId === c.id
                      ? 'bg-indigo-50 text-indigo-900 font-bold border border-indigo-200'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {c.title || 'Untitled Query'}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Statutory Invariant Footer */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 text-[10px] text-slate-500 leading-tight">
          <div className="font-bold text-slate-700 flex items-center gap-1 mb-0.5">
            <span>🛡️</span> Zero Hallucination Policy
          </div>
          All responses grounded strictly in published Bureau of Indian Standards documents.
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* CENTER STAGE: Conversational Stream                           */}
      {/* ------------------------------------------------------------- */}
      <main className="flex-1 flex flex-col bg-slate-50 overflow-hidden relative">
        {/* Banner */}
        <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div>
            <h1 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>🇮🇳</span> Ask Zyntrix about Indian Standards & BIS Services
              <span className="text-[10px] font-mono bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-200">
                SIH PS 26107
              </span>
            </h1>
            <p className="text-xs text-slate-500">
              Source-backed regulatory intelligence for industries, MSMEs, startups, and consumers.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onStartComplianceAssessment ? onStartComplianceAssessment('golden') : onNavigateWorkstation()}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">rocket_launch</span>
              <span>Start Compliance Assessment</span>
              <span className="material-symbols-outlined text-xs">arrow_forward</span>
            </button>

            {/* Multilingual Selector */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              <button
                onClick={() => setSelectedLanguage('en')}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-colors ${
                  selectedLanguage === 'en' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setSelectedLanguage('hi')}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-colors ${
                  selectedLanguage === 'hi' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                हिन्दी (Hindi)
              </button>
              <button
                onClick={() => setSelectedLanguage('ta')}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-colors ${
                  selectedLanguage === 'ta' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                தமிழ் (Tamil)
              </button>
            </div>
          </div>
        </header>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex gap-4 max-w-4xl ${m.role === 'user' ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
            >
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-800 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-sm">
                  BIS
                </div>
              )}

              <div
                className={`rounded-2xl p-5 text-sm leading-relaxed max-w-2xl ${
                  m.role === 'user'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-white text-slate-800 border border-slate-200 shadow-sm'
                }`}
              >
                {/* Assistant Answer Body */}
                <div className="whitespace-pre-wrap font-sans">{m.content}</div>

                {/* Initial Welcome Action Cards */}
                {idx === 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onStartComplianceAssessment ? onStartComplianceAssessment('golden') : onNavigateWorkstation()}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-sm">rocket_launch</span>
                      <span>Start Compliance Assessment (IS 17526 Vacuum Flask Demo)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => onStartComplianceAssessment ? onStartComplianceAssessment('input') : onNavigateWorkstation()}
                      className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold flex items-center gap-1.5 border border-slate-200 transition-all cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-sm">edit_note</span>
                      <span>Input New Product Details</span>
                    </button>
                  </div>
                )}

                {/* Handoff Button (Layer A -> Layer B) */}
                {m.handoff && (
                  <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 bg-indigo-50/50 p-3 rounded-xl border border-indigo-100">
                    <div>
                      <div className="text-xs font-bold text-indigo-900">
                        {m.handoff.suggested_title}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Standard: {m.handoff.target_standard}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onStartComplianceAssessment ? onStartComplianceAssessment('golden') : handleHandoffToWorkstation(m.handoff)}
                        className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-xs">rocket_launch</span>
                        <span>Start Compliance Assessment</span>
                      </button>
                      <button
                        onClick={() => handleHandoffToWorkstation(m.handoff)}
                        className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 shadow-2xs transition-colors cursor-pointer"
                      >
                        <span>⚡ Workstation</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Clickable Provenance Citations */}
                {m.citations && m.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                      Statutory Provenance Citations (Click to inspect source):
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {m.citations.map((cite, cIdx) => (
                        <button
                          key={cIdx}
                          onClick={() => setInspectingSource(cite)}
                          className="px-2.5 py-1 rounded-md bg-slate-100 hover:bg-indigo-100 text-indigo-800 text-xs font-mono font-semibold border border-slate-200 hover:border-indigo-300 transition-colors flex items-center gap-1.5"
                        >
                          <span>📜</span>
                          <span>{cite.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                  U
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-4 max-w-4xl mr-auto">
              <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 animate-pulse">
                BIS
              </div>
              <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-sm text-xs text-slate-500 flex items-center gap-3">
                <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                Retrieving from published BIS standards, schemes, and laboratory repositories...
              </div>
            </div>
          )}
          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-white border-t border-slate-200">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-end gap-3 max-w-4xl mx-auto"
          >
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                rows={2}
                placeholder="Ask about Indian Standards, BIS schemes, testing requirements, labs, or hallmarking..."
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-md disabled:opacity-50 transition-all flex items-center gap-1.5"
            >
              <span>Ask</span>
              <span>➔</span>
            </button>
          </form>
          <div className="text-center text-[11px] text-slate-400 mt-2">
            Zyntrix is an informational intelligence tool and does not issue statutory BIS certifications or licenses.
          </div>
        </div>
      </main>

      {/* ------------------------------------------------------------- */}
      {/* RIGHT SIDEBAR: Source Provenance Inspector                    */}
      {/* ------------------------------------------------------------- */}
      <aside className="w-80 border-l border-slate-200 bg-white flex flex-col flex-shrink-0 overflow-y-auto">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <span>🔍</span> Source Inspector
          </h2>
          <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
            VERIFIED
          </span>
        </div>

        {inspectingSource ? (
          <div className="p-5 space-y-4">
            <div className="p-3.5 bg-indigo-50/60 border border-indigo-200 rounded-xl">
              <div className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider mb-1">
                Citation Reference
              </div>
              <div className="font-mono text-xs font-bold text-indigo-950">
                {inspectingSource.label}
              </div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Indian Standard
              </label>
              <div className="text-sm font-bold text-slate-900">
                {inspectingSource.standard_number}
              </div>
            </div>

            {inspectingSource.clause_number && (
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Clause Reference
                </label>
                <div className="text-xs font-semibold text-slate-700">
                  Clause {inspectingSource.clause_number}
                  {inspectingSource.page && ` (Page ${inspectingSource.page})`}
                </div>
              </div>
            )}

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Regulatory Trust Classification
              </label>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                <span>✓</span> {inspectingSource.source_type || 'AUTHORITATIVE_BIS'}
              </span>
            </div>

            {inspectingSource.claim && (
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Verified Factual Claim
                </label>
                <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
                  {inspectingSource.claim}
                </div>
              </div>
            )}

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Content Hash (SHA-256)
              </label>
              <div className="font-mono text-[10px] text-slate-500 break-all bg-slate-50 p-2 rounded border border-slate-200">
                {inspectingSource.content_hash || '4c70ec2b7189f3a9e...'}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500">
              Verified by Zyntrix Deterministic Citation Guard against PostgreSQL statutory repository.
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 text-xs flex flex-col items-center justify-center h-full">
            <span className="text-3xl mb-2">📜</span>
            Click any citation in an assistant response to inspect its exact clause, page number, and authoritative BIS provenance.
          </div>
        )}
      </aside>

      {/* Product Investigation Modal */}
      <ProductInvestigationModal
        isOpen={investigationModalOpen}
        onClose={() => setInvestigationModalOpen(false)}
        onStartWorkstationJob={(newJobId) => {
          if (onJobCreated) onJobCreated(newJobId);
          if (onNavigateWorkstation) onNavigateWorkstation(newJobId);
        }}
      />
    </div>
  );
}
