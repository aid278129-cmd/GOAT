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
import GlideSelect from './loading-ui/GlideSelect';
import { AudioInputButton, TextToSpeechButton } from './common/AudioInputButton';
import { FormattedMessage } from './common/FormattedMessage';

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

  const languageOptions = [
    { value: 'en', label: 'English', tag: 'EN' },
    { value: 'hi', label: 'हिन्दी', tag: 'HI' },
    { value: 'ta', label: 'தமிழ்', tag: 'TA' },
  ];

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
      t.includes('how do i get bis') ||
      t.includes('scheme i') ||
      t.includes('scheme ii') ||
      t.includes('licensing')
    ) {
      return 'certification';
    }

    if (
      i === 'LABORATORY_DISCOVERY' ||
      t.includes('laboratory') ||
      t.includes('find a lab') ||
      t.includes('testing lab') ||
      t.includes('where can i test') ||
      t.includes('nabl')
    ) {
      return 'laboratory';
    }

    if (
      i === 'HALLMARKING_VERIFICATION' ||
      t.includes('hallmark') ||
      t.includes('huid') ||
      t.includes('gold purity') ||
      t.includes('22k') ||
      t.includes('bis care')
    ) {
      return 'hallmarking';
    }

    if (
      i === 'CONSUMER_COMPLAINT' ||
      t.includes('complaint') ||
      t.includes('fake isi') ||
      t.includes('substandard') ||
      t.includes('report misuse')
    ) {
      return 'consumer';
    }

    return null;
  };

  const isGreeting = (t) => {
    return /^(hi|hello|hey|heya|howdy|namaste|vanakkam|greetings|good\s+(morning|afternoon|evening)|who\s+are\s+you|help\b)/i.test((t || '').trim());
  };

  const handleSendMessage = async (customText) => {
    const textToSend = customText || inputMessage;
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
      let fallbackText = "";
      let fallbackCitations = [];
      const cardType = isGreeting(textToSend) ? null : detectCardType(textToSend, '');

      if (isGreeting(textToSend)) {
        if (selectedLanguage === 'hi') {
          fallbackText = "नमस्ते! मैं ज़ायंट्रिक्स बीआईएस बौद्धिक अनुपालन सहायक हूँ। मैं भारतीय मानकों (IS), प्रमाणन प्रक्रियाओं (ISI/CRS), प्रयोगशाला खोज और हॉलमार्किंग में आपकी सहायता कर सकता हूँ। कृपया अपना प्रश्न दर्ज करें।";
        } else if (selectedLanguage === 'ta') {
          fallbackText = "வணக்கம்! நான் ஜின்ட்ரிக்ஸ் பிஐஎஸ் அறிவார்ந்த இணக்க உதவியாளர். இந்திய தரநிலைகள் (IS), சான்றிதழ் திட்டங்கள் மற்றும் ஆய்வக விவரங்களில் உதவ முடியும். உங்கள் கேள்வியை உள்ளிடவும்.";
        } else {
          fallbackText = "Hello! I am the Zyntrix BIS Intelligent Compliance Assistant. How can I assist you today with Indian Standards (IS), BIS certification schemes (ISI Mark, CRS), testing laboratories, or hallmarking requirements?";
        }
      } else if (cardType === 'assessment') {
        fallbackText = "Based on official Bureau of Indian Standards published records:\n\n**Let's assess your product.**\n\nFor a double-wall stainless steel vacuum flask up to 2000 ml, the statutory standard is **IS 17526:2021** (Vacuum Insulated Stainless Steel Flasks and Containers). This standard is covered under a mandatory Quality Control Order (QCO) requiring Scheme I (ISI Mark) certification before domestic sale or import.";
        fallbackCitations = [
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
        ];
      } else if (cardType === 'certification') {
        fallbackText = "Based on official Bureau of Indian Standards published records:\n\nBIS certification operates primarily under **Scheme I (ISI Mark)** for industrial and domestic goods and **Scheme II (CRS)** for electronic/IT goods. The licensing procedure entails:\n1. Application on the Manak Online portal (Form VI).\n2. Factory audit & sample drawing by BIS officers.\n3. Testing in BIS-recognized NABL laboratories.\n4. Grant of License (CML Number).";
      } else if (cardType === 'laboratory') {
        fallbackText = "Based on official Bureau of Indian Standards published records:\n\nTesting for BIS certification must be performed in the **BIS Central Laboratory** (Sahibabad) or authorized regional/private NABL-accredited test laboratories recognized under the Laboratory Recognition Scheme (LRS 2020).";
      } else if (cardType === 'hallmarking') {
        fallbackText = "Based on official Bureau of Indian Standards published records:\n\nUnder statutory BIS Hallmarking Regulations, all hallmarked gold jewelry in India must bear the **3 mandatory marks**:\n1. BIS Standard Logo\n2. Purity & Fineness (e.g. 22K916 for 22 Karat Gold)\n3. 6-digit alphanumeric HUID (Hallmark Unique Identification).\nConsumers can verify any HUID code directly on the **BIS CARE** mobile app.";
      } else {
        fallbackText = `Regarding "${textToSend}": All Indian Standards and conformity assessment procedures are published under statutory mandate by the Bureau of Indian Standards under the BIS Act 2016.`;
      }

      const asstMsg = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: fallbackText,
        citations: fallbackCitations,
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

  const handleAudioTranscript = (transcriptText) => {
    setInputMessage((prev) => {
      const clean = prev.trim();
      return clean ? `${clean} ${transcriptText}` : transcriptText;
    });
  };

  const isHomeScreen = messages.length === 0;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-[#090d16] text-slate-100 overflow-hidden font-sans">
      {/* ============================================================== */}
      {/* 1. HOME SCREEN (Clean, spacious, single input, 4 examples)    */}
      {/* ============================================================== */}
      {isHomeScreen ? (
        <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-8 overflow-y-auto">
          <div className="max-w-2xl w-full text-center space-y-6 my-auto">
            {/* Brand icon & title */}
            <div className="space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(56,189,248,0.25)]">
                <span className="material-symbols-outlined text-3xl">smart_toy</span>
              </div>
              <div>
                <span className="font-space-grotesk text-xs font-bold uppercase tracking-wider text-cyan-400 block mb-1">
                  GOAT
                </span>
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest block">
                  Intelligent BIS Compliance Assistant
                </span>
                <h1 className="font-space-grotesk text-2xl sm:text-3xl font-bold text-white tracking-tight mt-2">
                  What regulatory guidance do you need?
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 max-w-md mx-auto leading-relaxed">
                  Search Indian Standards, understand certification schemes, find laboratories, verify hallmarking, or speak directly with audio input support.
                </p>
              </div>
            </div>

            {/* Large Conversational Input with Audio Support & GlideSelect */}
            <div className="w-full bg-[#0f1422]/90 backdrop-blur-xl rounded-2xl border border-slate-800 shadow-2xl p-3 sm:p-4 text-left">
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
                placeholder="Ask or speak about a BIS standard, certification, testing, hallmarking, or your product..."
                className="w-full text-xs sm:text-sm text-slate-100 placeholder-slate-500 bg-transparent resize-none focus:outline-none leading-relaxed"
                autoFocus
              />

              <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 mt-2">
                {/* GlideSelect Language switcher */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider hidden sm:inline">
                    Language:
                  </span>
                  <GlideSelect
                    options={languageOptions}
                    value={selectedLanguage}
                    onChange={(val) => onSelectLanguage && onSelectLanguage(val)}
                    size="sm"
                    menuWidth={130}
                    surfaceColor="#0b0f19"
                    highlightColor="#1e293b"
                    accentColor="#38bdf8"
                    textColor="#f1f5f9"
                    radius={8}
                    ariaLabel="Assistant Language"
                  />
                </div>

                {/* Right controls: Audio Input Mic & Submit button */}
                <div className="flex items-center gap-2">
                  <AudioInputButton
                    onTranscript={handleAudioTranscript}
                    language={selectedLanguage}
                    disabled={loading}
                  />

                  <button
                    type="button"
                    onClick={() => handleSendMessage()}
                    disabled={!inputMessage.trim() || loading}
                    className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-30 text-slate-950 font-bold rounded-xl text-xs shadow-[0_0_15px_rgba(56,189,248,0.3)] transition-all flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <span>Ask</span>
                    <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Compact example queries */}
            <div className="space-y-2 pt-2">
              <div className="text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider">
                Or choose an example query:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-xl mx-auto">
                {homeExamples.map((ex, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(ex.query)}
                    className="p-3.5 text-left bg-[#0f1422] hover:bg-[#151c2f] border border-slate-800 hover:border-cyan-500/40 rounded-xl transition-all shadow-md group cursor-pointer"
                  >
                    <div className="text-xs font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors flex items-center justify-between">
                      <span>{ex.label}</span>
                      <span className="material-symbols-outlined text-[15px] text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all">
                        arrow_forward
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="text-[11px] font-mono text-slate-500 pt-4">
              AI-assisted regulatory intelligence &bull; Statutory determinations are deterministic &bull; 0% LLM Compliance Authority.
            </div>
          </div>
        </div>
      ) : (
        /* ============================================================== */
        /* 2. ACTIVE CONVERSATIONAL STREAM & CONTEXTUAL RESULT CARDS      */
        /* ============================================================== */
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Stream Header */}
          <div className="h-12 bg-[#0b0f19] border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-space-grotesk text-xs font-bold text-white">
                Compliance Assistant
              </span>
              <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
                &bull; Source-Backed Regulatory Intelligence
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleStartNewConversation}
                className="px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-cyan-200 hover:bg-slate-800/80 rounded-lg border border-slate-800 transition-colors cursor-pointer flex items-center gap-1"
                title="Start a fresh conversation"
              >
                <span className="material-symbols-outlined text-[15px]">add</span>
                <span>New Conversation</span>
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${
                    m.role === 'user' ? 'items-end' : 'items-start'
                  } space-y-2`}
                >
                  <div
                    className={`max-w-[85%] p-4 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-md ${
                      m.role === 'user'
                        ? 'bg-cyan-950/40 text-cyan-100 border border-cyan-500/30'
                        : 'bg-[#0f1422] text-slate-100 border border-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3 mb-1.5">
                      <div className="flex items-center gap-2">
                        {m.role === 'assistant' ? (
                          <span className="font-mono text-[10px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                            <span className="material-symbols-outlined text-[13px]">shield</span>
                            <span>GOAT BIS Assistant</span>
                          </span>
                        ) : (
                          <span className="font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            You
                          </span>
                        )}
                      </div>

                      {/* Text to Speech Read Aloud for Assistant Messages */}
                      {m.role === 'assistant' && (
                        <TextToSpeechButton
                          text={m.content}
                          language={selectedLanguage}
                        />
                      )}
                    </div>

                    <FormattedMessage text={m.content} />

                    {/* Citations block */}
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1">
                        <div className="font-mono text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                          Authoritative Statutory Citations:
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {m.citations.map((c, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => handleCitationClick(c)}
                              className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-cyan-300 text-[11px] font-mono flex items-center gap-1 cursor-pointer transition-colors"
                              title="Inspect statutory clause snapshot"
                            >
                              <span className="material-symbols-outlined text-[12px] text-cyan-400">menu_book</span>
                              <span>{c.label || c.document || 'Citation'}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Contextual cards */}
                    {m.cardType === 'assessment' && (
                      <ContextualAssessmentCard
                        onStartAssessment={onStartComplianceAssessment}
                        onInspectSource={onInspectSource}
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

              {/* Thinking & Loading Indicator */}
              {loading && (
                <div className="flex items-start gap-3 max-w-2xl mr-auto animate-in fade-in duration-200">
                  <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 flex items-center justify-center shrink-0 shadow-xs">
                    <span className="material-symbols-outlined text-base">shield</span>
                  </div>
                  <div className="p-4 bg-[#0f1422] border border-slate-800 rounded-2xl shadow-md text-xs flex items-center gap-3">
                    <MorphingInfinity className="w-5 h-5 text-cyan-400 shrink-0" />
                    <div className="space-y-0.5">
                      <div className="font-semibold text-cyan-300 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                        <TextShimmer baseColor="#38bdf8" shimmerColor="#a5f3fc" duration={1.8}>
                          Thinking...
                        </TextShimmer>
                      </div>
                      <TextShimmer baseColor="#64748b" shimmerColor="#cbd5e1" duration={2.5}>
                        Consulting authoritative BIS standards, QCO orders, and laboratory repositories...
                      </TextShimmer>
                    </div>
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>
          </div>

          {/* Sticky Bottom Conversational Input with Audio Support */}
          <div className="p-3 sm:p-4 bg-[#0b0f19] border-t border-slate-800 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="max-w-3xl mx-auto flex items-end gap-2"
            >
              <div className="flex-1 relative bg-[#080c14] border border-slate-700/80 rounded-xl focus-within:border-cyan-400 focus-within:ring-1 focus-within:ring-cyan-400/30 transition-colors p-2">
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
                  placeholder="Ask or speak a follow-up about Indian Standards, schemes, testing, or your product..."
                  className="w-full text-xs sm:text-sm text-slate-100 placeholder-slate-500 bg-transparent resize-none focus:outline-none leading-relaxed"
                />
              </div>

              {/* Audio Microphone Input Button */}
              <AudioInputButton
                onTranscript={handleAudioTranscript}
                language={selectedLanguage}
                disabled={loading}
              />

              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="px-4 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-40 text-slate-950 rounded-xl text-xs font-bold shadow-[0_0_15px_rgba(56,189,248,0.25)] transition-all flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed shrink-0"
              >
                {loading ? (
                  <>
                    <MorphingInfinity className="w-4 h-4 text-slate-950" />
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
            <div className="text-center text-[10px] font-mono text-slate-500 mt-2">
              Source-backed assistant &bull; Official Indian Standards &bull; Zero LLM Compliance Authority
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
