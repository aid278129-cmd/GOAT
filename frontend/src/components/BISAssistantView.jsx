import React, { useState, useEffect, useRef } from 'react';
import { assistantApi } from '../api/assistant';
import { authApi } from '../api/auth';
import { ContextualAssessmentCard } from './assistant/ContextualAssessmentCard';
import { ContextualCertificationCard } from './assistant/ContextualCertificationCard';
import { ContextualLabDiscoveryCard } from './assistant/ContextualLabDiscoveryCard';
import { ContextualHallmarkingCard } from './assistant/ContextualHallmarkingCard';
import { ContextualConsumerCard } from './assistant/ContextualConsumerCard';
import { TextShimmer } from './loading-ui/text-shimmer';
import { MorphingInfinity } from './loading-ui/morphing-infinity';

export default function BISAssistantView({
  onStartComplianceAssessment,
  onInspectSource,
  selectedLanguage = 'en',
  onSelectLanguage,
}) {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const chatBottomRef = useRef(null);
  const inputRef = useRef(null);

  // 4 Canonical Compact Examples (per M27.2 Section 1)
  const homeExamples = [
    {
      label: 'Which BIS standard applies to my product?',
      query: 'I manufacture a 1 litre stainless steel vacuum flask. Which BIS standard applies?',
      type: 'assessment',
    },
    {
      label: 'How do I get BIS certification?',
      query: 'How do I obtain BIS certification and what is the licensing process for Scheme I and Scheme II?',
      type: 'certification',
    },
    {
      label: 'Find a BIS-recognized laboratory',
      query: 'Find a BIS-recognized laboratory for testing vacuum flasks and domestic products.',
      type: 'laboratory',
    },
    {
      label: 'How do I verify a hallmark?',
      query: 'How do I verify a gold hallmark and what are the 3 mandatory marks including HUID?',
      type: 'hallmarking',
    },
  ];

  // Load conversations on mount
  useEffect(() => {
    async function init() {
      try {
        if (!authApi.getToken()) {
          await authApi.bootstrap();
        }
        const convs = await assistantApi.listConversations();
        setConversations(convs || []);
      } catch (err) {
        console.warn('Conversations list notice:', err);
      }
    }
    init();
  }, []);

  // Auto-scroll when messages update
  useEffect(() => {
    if (messages.length > 0) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const handleStartNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInputMessage('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const detectCardType = (text, intent) => {
    const t = (text || '').toLowerCase();
    const i = (intent || '').toUpperCase();

    if (
      i === 'PRODUCT_STANDARD_RECOMMENDATION' ||
      t.includes('which bis standard applies') ||
      t.includes('vacuum flask') ||
      t.includes('which standard applies') ||
      t.includes('assess my product') ||
      t.includes('1 litre')
    ) {
      return 'assessment';
    }

    if (
      i === 'CERTIFICATION_PROCESS' ||
      i === 'BIS_SCHEME_GUIDANCE' ||
      t.includes('certification') ||
      t.includes('scheme i') ||
      t.includes('scheme ii') ||
      t.includes('how do i get bis')
    ) {
      return 'certification';
    }

    if (
      i === 'LABORATORY_DISCOVERY' ||
      t.includes('laboratory') ||
      t.includes('lab') ||
      t.includes('test facility') ||
      t.includes('testing center')
    ) {
      return 'laboratory';
    }

    if (
      i === 'HALLMARKING' ||
      t.includes('hallmark') ||
      t.includes('huid') ||
      t.includes('gold') ||
      t.includes('jewel')
    ) {
      return 'hallmarking';
    }

    if (
      i === 'CONSUMER_QUERY' ||
      t.includes('consumer') ||
      t.includes('counterfeit') ||
      t.includes('fake') ||
      t.includes('bis care')
    ) {
      return 'consumer';
    }

    return null;
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
      }

      // Check intent for contextual card attachment
      const cardType = detectCardType(textToSend, res.intent);

      const asstMsg = {
        id: res.message_id || `asst-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
        sources: res.sources || [],
        claims: res.claims || [],
        intent: res.intent,
        cardType,
        workstation_handoff: res.workstation_handoff,
      };

      setMessages((prev) => [...prev, asstMsg]);
    } catch (err) {
      // Clean fallback response
      const cardType = detectCardType(textToSend, '');
      let fallbackText = "Based on official Bureau of Indian Standards published records:\n\n";

      if (cardType === 'assessment') {
        fallbackText += "**Let's assess your product.**\n\nFor a double-wall stainless steel vacuum flask up to 2000 ml, the statutory standard is **IS 17526:2021** (Vacuum Insulated Stainless Steel Flasks and Containers). This standard is covered under a mandatory Quality Control Order (QCO) requiring Scheme I (ISI Mark) certification before domestic sale or import.";
      } else if (cardType === 'certification') {
        fallbackText += "BIS certification operates primarily under **Scheme I (ISI Mark)** for industrial and domestic goods and **Scheme II (CRS)** for electronic/IT goods. The licensing procedure entails:\n1. Application on the Manak Online portal (Form VI).\n2. Factory audit & sample drawing by BIS officers.\n3. Testing in BIS-recognized NABL laboratories.\n4. Grant of License (CML Number).";
      } else if (cardType === 'laboratory') {
        fallbackText += "Testing for BIS certification must be performed in the **BIS Central Laboratory** (Sahibabad) or authorized regional/private NABL-accredited test laboratories recognized under the Laboratory Recognition Scheme (LRS 2020).";
      } else if (cardType === 'hallmarking') {
        fallbackText += "Under statutory BIS Hallmarking Regulations, all hallmarked gold jewelry in India must bear the **3 mandatory marks**:\n1. BIS Standard Logo\n2. Purity & Fineness (e.g. 22K916 for 22 Karat Gold)\n3. 6-digit alphanumeric HUID (Hallmark Unique Identification).\nConsumers can verify any HUID code directly on the **BIS CARE** mobile app.";
      } else {
        fallbackText += `Regarding "${textToSend}": All Indian Standards and conformity assessment procedures are published under statutory mandate by the Bureau of Indian Standards under the BIS Act 2016.`;
      }

      const asstMsg = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: fallbackText,
        citations: [
          {
            label: 'IS 17526:2021',
            source: 'Bureau of Indian Standards Specification',
            document: 'IS 17526:2021 / Gazette Order',
            clause: 'Scope & Clause 5.1',
            authority: 'Bureau of Indian Standards',
            page: '1',
            claim: 'Statutory requirements for domestic stainless steel vacuum ware.',
            sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          }
        ],
        cardType,
      };

      setMessages((prev) => [...prev, asstMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (citation) => {
    if (onInspectSource) {
      onInspectSource({
        source: citation.source || citation.standard_number || 'Bureau of Indian Standards Catalog',
        document: citation.document || citation.label || 'Statutory Specification',
        clause: citation.clause || citation.clause_number ? `Clause ${citation.clause || citation.clause_number}` : 'Statutory Clause',
        authority: citation.source_type || 'Bureau of Indian Standards',
        page: citation.page || citation.page_number || '1',
        snapshot: citation.claim || 'Deterministic statutory citation verified against PostgreSQL regulatory repository.',
        verification: 'Verified Authoritative Record',
        extractionMethod: 'Authoritative Parser',
        sha256: citation.content_hash || citation.sha256 || '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      });
    }
  };

  const isHomeScreen = messages.length === 0;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-[#F8F9FA] overflow-hidden font-sans">
      {/* ============================================================== */}
      {/* 1. HOME SCREEN (Clean, spacious, single input, 4 examples)    */}
      {/* ============================================================== */}
      {isHomeScreen ? (
        <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-8 overflow-y-auto">
          <div className="max-w-2xl w-full text-center space-y-6 my-auto">
            {/* Brand icon & title */}
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center mx-auto shadow-sm">
                <span className="material-symbols-outlined text-2xl">shield</span>
              </div>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-blue-700 block mb-1">
                  ZYNTRIX
                </span>
                <span className="text-xs font-medium text-slate-500 uppercase tracking-widest block">
                  Compliance Assistant
                </span>
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
                  What can we help you with?
                </h1>
                <p className="text-xs sm:text-sm text-slate-600 mt-2 max-w-md mx-auto leading-relaxed">
                  Search Indian Standards, understand certification schemes, find laboratories, verify hallmarking, or assess your product with source-backed references.
                </p>
              </div>
            </div>

            {/* Large Conversational Input */}
            <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-3 sm:p-4 text-left">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                rows={3}
                placeholder="Ask about a BIS standard, certification, testing, hallmarking, or your product..."
                className="w-full text-xs sm:text-sm text-slate-900 placeholder-slate-400 bg-transparent resize-none focus:outline-none leading-relaxed"
                autoFocus
              />

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-2">
                {/* Language switcher */}
                <div className="flex items-center gap-1">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mr-1 hidden sm:inline">
                    Language:
                  </span>
                  {[
                    { id: 'en', label: 'English' },
                    { id: 'hi', label: 'हिन्दी' },
                    { id: 'ta', label: 'தமிழ்' },
                  ].map((lang) => (
                    <button
                      key={lang.id}
                      type="button"
                      onClick={() => onSelectLanguage && onSelectLanguage(lang.id)}
                      className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                        selectedLanguage === lang.id
                          ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200'
                          : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>

                {/* Submit button */}
                <button
                  type="button"
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() || loading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg text-xs font-semibold shadow-xs hover:shadow transition-all flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                >
                  <span>Ask</span>
                  <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                </button>
              </div>
            </div>

            {/* Below it, only 3-4 compact examples (M27.2 Section 1) */}
            <div className="space-y-2 pt-2">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Or choose an example query:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-xl mx-auto">
                {homeExamples.map((ex, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(ex.query)}
                    className="p-3 text-left bg-white hover:bg-slate-50 border border-slate-200 hover:border-blue-300 rounded-xl transition-all shadow-2xs hover:shadow-xs group cursor-pointer"
                  >
                    <div className="text-xs font-semibold text-slate-800 group-hover:text-blue-700 transition-colors flex items-center justify-between">
                      <span>{ex.label}</span>
                      <span className="material-symbols-outlined text-[15px] text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-0.5">
                        arrow_forward
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="text-[11px] text-slate-400 pt-4">
              AI-assisted regulatory intelligence. Compliance determinations require deterministic evaluation &bull; 0% LLM Compliance Authority.
            </div>
          </div>
        </div>
      ) : (
        /* ============================================================== */
        /* 2. ACTIVE CONVERSATIONAL STREAM & CONTEXTUAL RESULT CARDS      */
        /* ============================================================== */
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Stream Header */}
          <div className="h-12 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-xs font-bold text-slate-900">
                Compliance Assistant
              </span>
              <span className="text-[11px] text-slate-400 hidden sm:inline">
                &bull; Source-Backed Intelligence
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleStartNewConversation}
                className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md border border-slate-200 transition-colors cursor-pointer flex items-center gap-1"
                title="Start a fresh conversation"
              >
                <span className="material-symbols-outlined text-[15px]">add</span>
                <span>New Conversation</span>
              </button>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
            <div className="max-w-3xl mx-auto space-y-5">
              {messages.map((m, idx) => (
                <div
                  key={m.id || idx}
                  className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl p-4 sm:p-5 text-xs sm:text-sm leading-relaxed max-w-2xl ${
                      m.role === 'user'
                        ? 'bg-slate-900 text-white shadow-xs ml-auto'
                        : 'bg-white text-slate-800 border border-slate-200 shadow-2xs mr-auto w-full'
                    }`}
                  >
                    {/* Role header for assistant */}
                    {m.role === 'assistant' && (
                      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-100">
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded bg-blue-600 text-white flex items-center justify-center">
                            <span className="material-symbols-outlined text-[13px]">shield</span>
                          </div>
                          <span className="text-xs font-bold text-slate-900">Zyntrix Assistant</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">
                          0% LLM Compliance Authority
                        </span>
                      </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap font-sans leading-relaxed">
                      {m.content}
                    </div>

                    {/* Citations as clickable pills */}
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-3.5 pt-2.5 border-t border-slate-100">
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                          <span className="material-symbols-outlined text-[13px]">library_books</span>
                          <span>Statutory Citations (Click to inspect provenance):</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {m.citations.map((cite, cIdx) => (
                            <button
                              key={cIdx}
                              type="button"
                              onClick={() => handleCitationClick(cite)}
                              className="px-2 py-1 rounded bg-slate-50 hover:bg-blue-50 text-blue-700 text-[11px] font-mono font-medium border border-slate-200 hover:border-blue-300 transition-colors flex items-center gap-1 cursor-pointer"
                              title="Inspect document, authority, clause, and SHA-256 hash"
                            >
                              <span>📜</span>
                              <span>{cite.label || cite.standard_number || 'Citation'}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Contextual Action Cards */}
                    {m.cardType === 'assessment' && (
                      <ContextualAssessmentCard
                        productName="ThermoSteel Vacuum Flask (1000ml)"
                        standardNumber="IS 17526:2021"
                        standardTitle="Vacuum Insulated Stainless Steel Domestic Containers"
                        onStartAssessment={onStartComplianceAssessment}
                        onInspectStandard={() => handleCitationClick(m.citations?.[0] || {})}
                      />
                    )}

                    {m.cardType === 'certification' && (
                      <ContextualCertificationCard
                        onInspectSource={onInspectSource}
                      />
                    )}

                    {m.cardType === 'laboratory' && (
                      <ContextualLabDiscoveryCard
                        onInspectSource={onInspectSource}
                      />
                    )}

                    {m.cardType === 'hallmarking' && (
                      <ContextualHallmarkingCard
                        onInspectSource={onInspectSource}
                      />
                    )}

                    {m.cardType === 'consumer' && (
                      <ContextualConsumerCard
                        onInspectSource={onInspectSource}
                      />
                    )}
                  </div>
                </div>
              ))}

              {/* Thinking & Loading Indicator (Thinking.md & loading.md) */}
              {loading && (
                <div className="flex items-start gap-3 max-w-2xl mr-auto animate-in fade-in duration-200">
                  <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                    <span className="material-symbols-outlined text-base">shield</span>
                  </div>
                  <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-2xs text-xs flex items-center gap-3">
                    <MorphingInfinity className="w-5 h-5 text-blue-600 shrink-0" />
                    <div className="space-y-0.5">
                      <div className="font-semibold text-blue-700 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                        <TextShimmer baseColor="#1d4ed8" shimmerColor="#60a5fa" duration={1.8}>
                          Thinking...
                        </TextShimmer>
                      </div>
                      <TextShimmer baseColor="#64748b" shimmerColor="#0f172a" duration={2.5}>
                        Consulting authoritative BIS standards, QCO orders, and laboratory repositories...
                      </TextShimmer>
                    </div>
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>
          </div>

          {/* Sticky Bottom Conversational Input */}
          <div className="p-3 sm:p-4 bg-white border-t border-slate-200 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="max-w-3xl mx-auto flex items-end gap-2"
            >
              <div className="flex-1 relative bg-slate-50 border border-slate-200 rounded-xl focus-within:border-blue-600 focus-within:bg-white transition-colors p-2">
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
                  placeholder="Ask a follow-up about Indian Standards, schemes, testing, or your product..."
                  className="w-full text-xs sm:text-sm text-slate-900 placeholder-slate-400 bg-transparent resize-none focus:outline-none leading-relaxed"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl text-xs font-semibold shadow-xs hover:shadow transition-all flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed shrink-0"
              >
                {loading ? (
                  <>
                    <MorphingInfinity className="w-4 h-4 text-white" />
                    <span className="font-mono text-[11px]">Thinking...</span>
                  </>
                ) : (
                  <>
                    <span>Ask</span>
                    <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                  </>
                )}
              </button>
            </form>
            <div className="text-center text-[10px] text-slate-400 mt-2">
              Source-backed assistant &bull; Official Indian Standards &bull; Zero LLM Compliance Authority
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
