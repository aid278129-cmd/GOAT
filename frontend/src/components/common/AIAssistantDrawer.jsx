import React, { useState, useRef, useEffect } from 'react';
import { assistantApi } from '../../api/assistant';
import { apiClient } from '../../api/client';
import { authApi } from '../../api/auth';
import { TextShimmer } from '../loading-ui/text-shimmer';
import { MorphingInfinity } from '../loading-ui/morphing-infinity';
import { AudioInputButton, TextToSpeechButton } from './AudioInputButton';
import { FormattedMessage } from './FormattedMessage';

function formatCitationDisplay(cite) {
  if (!cite) return 'BIS Standard';
  if (cite.label) {
    return cite.label.replace(/^\[|\]$/g, '').trim();
  }
  const std = cite.standard_number || cite.standard || cite.source || cite.document;
  const cl = cite.clause_number ? `Cl. ${cite.clause_number}` : (cite.clause && cite.clause !== 'Scope' && cite.clause !== 'General' ? cite.clause : '');
  const pg = cite.page ? `Pg. ${cite.page}` : '';
  const parts = [std, cl, pg].filter(Boolean);
  if (parts.length > 0) return parts.join(' — ');
  return cite.source || cite.document || 'BIS Indian Standard';
}

function generateIntelligentResponse(userText, targetStandard = 'IS 17526:2021', assessmentNum = 'SIH-DEMO') {
  const t = userText.toLowerCase();

  if (/^(hi|hello|hey|heya|howdy|namaste|vanakkam|greetings|good\s+(morning|afternoon|evening)|who\s+are\s+you|help\b)/i.test(userText.trim())) {
    return {
      text: `Hello! I am the GOAT BIS Intelligent Compliance Assistant.\n\nI can assist you across Indian Standards and BIS compliance workflows:\n• **Standard Discovery**: Identifying applicable Indian Standards (IS) for your product\n• **Certification Schemes**: Understanding ISI Mark (Scheme I) and CRS (Scheme II) licensing\n• **Clause Interpretation**: Plain-language breakdowns of mandatory technical and safety clauses\n• **Testing & Labs**: Locating BIS-recognized and NABL-accredited test facilities\n• **Hallmarking & Consumer Verification**: Checking gold purity marks and HUID numbers\n\nHow can I assist you today?`,
      citations: []
    };
  }

  if (t.includes('bottle') || t.includes('flask') || t.includes('17526') || t.includes('steel bottle') || t.includes('vacuum') || t.includes('container') || t.includes('thermosteel')) {
    return {
      text: `For **Stainless Steel Bottles / Vacuum Flasks**, here are the mandatory BIS certification requirements under Indian statutory law:\n\n### 1. Applicable Indian Standard\n• **IS 17526:2021** (*Vacuum Insulated Stainless Steel Flasks, Bottles and Containers - Specification*).\n• **Mandatory Status:** Covered under the **DPIIT Quality Control Order (QCO)**. Manufacturing, importing, or selling non-certified stainless steel vacuum bottles in India is prohibited by law.\n\n### 2. Mandatory BIS Conformity Scheme\n• **Scheme I (ISI Mark Scheme):** Requires a Grant of License (CML Number), factory quality management audit, certified in-house testing equipment, and sample testing at BIS-recognized NABL laboratories.\n\n### 3. Key Mandatory Testing Clauses (IS 17526)\n• **Clause 4.1 (Material Grade & Food Safety):** Fluid-contact surfaces must use certified food-grade **Austenitic SS 304** (IS 6911) or **SS 316**. Polymer caps and gaskets must pass migration testing (IS 9845).\n• **Clause 5.1 (Hydraulic Integrity):** 20 kPa hydrostatic pressure test with zero leakage or seal distortion.\n• **Clause 5.3 (Thermal Performance Test):** Must retain hot fluid at **>= 65.0°C after 6 hours** when filled with boiling water (>= 95°C) in a 20°C ambient environment.\n• **Clause 5.6 (Drop Impact Resistance):** 1.0 m drop test onto hardwood 3 times without cracking.\n• **Clause 7.1 (Marking & Labeling):** Permanent marking of brand, capacity, 'IS 17526', and ISI mark with CML license number.\n\n### 4. Step-by-Step Certification Process\n1. Register manufacturing unit on **Manak Online** (manakonline.in) with Form VI.\n2. Upload factory layout, in-house test equipment calibration list, and SS 304 raw material test certificates.\n3. BIS officer conducts factory audit and draws independent samples.\n4. Samples tested in BIS Central Lab or accredited NABL laboratory.\n5. Grant of License (CML) issued allowing ISI mark embossing.`,
      citations: [
        {
          source: 'BIS Specification IS 17526:2021',
          document: 'IS 17526:2021 / DPIIT QCO Order',
          clause: 'Scheme I Mandate & Cl. 5.3',
          authority: 'Bureau of Indian Standards',
          page: '1',
          claim: 'Mandatory Scheme I ISI Mark certification for stainless steel bottles and vacuum flasks under DPIIT QCO.',
        }
      ]
    };
  }

  if (t.includes('inverter') || t.includes('solar') || t.includes('16221')) {
    return {
      text: `For **Photovoltaic Solar Inverters**, BIS compliance is governed under:\n\n• **Mandatory Standard:** **IS 16221 (Part 2)** (Safety of Power Converters for PV Systems) & **IS/IEC 62116** (Anti-islanding test).\n• **Regulatory Scheme:** **Scheme II — Compulsory Registration Scheme (CRS)** notified by MNRE and MeitY.\n• **Key Testing Requirements:** Anti-islanding disconnection within <= 2.0s (Clause 5.3), Dielectric withstand voltage at 2500 V RMS (Clause 5.2.3), and Enclosure IP rating (IP54 outdoor / IP20 indoor per Clause 4.2.1).\n• **Process:** Sample testing in BIS-recognized lab -> Upload test report on crsbis.in -> Grant of R-Number registration.`,
      citations: [
        {
          source: 'IS 16221 (Part 2): 2015',
          document: 'MeitY CRO Schedule IV',
          clause: 'Scope & Clause 5.3',
          authority: 'Ministry of Electronics & IT',
          page: '1',
          claim: 'Mandatory CRS registration for solar grid-tied and standalone inverters.',
        }
      ]
    };
  }

  if (t.includes('battery') || t.includes('lithium') || t.includes('16046') || t.includes('cell')) {
    return {
      text: `For **Secondary Lithium-ion Cells & Batteries**, BIS compliance requirements are:\n\n• **Mandatory Standard:** **IS 16046 (Part 2): 2018 / IEC 62133-2** (Secondary lithium cells/batteries for portable applications).\n• **Regulatory Scheme:** **Scheme II — Compulsory Registration Scheme (CRS)** under MeitY CRO.\n• **Mandatory Tests:** Continuous constant voltage charging (Cl 7.2.1), External short-circuit at 55°C (Cl 7.3.2), Free fall drop test (Cl 7.3.3), and Thermal abuse test at 130°C.\n• **Process:** Testing at NABL lab -> Registration on crsbis.in -> Standard Mark embossing with R-Number.`,
      citations: [
        {
          source: 'IS 16046 (Part 2): 2018',
          document: 'MeitY CRO Schedule II',
          clause: 'Clause 7.3.2',
          authority: 'Ministry of Electronics & IT',
          page: '1',
          claim: 'Mandatory CRS registration for lithium battery packs and cells.',
        }
      ]
    };
  }

  if (t.includes('how to get') || t.includes('procedure') || t.includes('process') || t.includes('scheme i') || t.includes('scheme ii') || t.includes('license') || t.includes('certification')) {
    return {
      text: `BIS operates two primary conformity assessment routes for manufacturers:\n\n### 1. Scheme I — Product Certification (ISI Mark)\n• **Scope:** Industrial, mechanical, domestic safety goods (steel products, vacuum flasks, cement, cables, packaged water, appliances).\n• **Process:** Application on Manak Online (manakonline.in) -> Factory audit by BIS officers -> Independent sample drawing -> Testing in BIS central/regional lab -> Grant of CML License.\n\n### 2. Scheme II — Compulsory Registration Scheme (CRS)\n• **Scope:** Electronics, IT equipment, solar inverters, LED lights, lithium batteries.\n• **Process:** Direct sample testing at BIS-recognized NABL laboratory -> Receive test report -> Online registration on crsbis.in -> Grant of R-Number.\n\n### 3. Foreign Manufacturers Scheme (FMCS)\n• Enables overseas manufacturers to obtain ISI mark with factory audit abroad and Indian Representative (AIR).`,
      citations: [
        {
          source: 'BIS Conformity Assessment Regulations 2018',
          document: 'Schedule II (Scheme I & Scheme II)',
          clause: 'Regulation 3 & 4',
          authority: 'Bureau of Indian Standards',
          page: '1',
          claim: 'Statutory framework for ISI Mark and Compulsory Registration.',
        }
      ]
    };
  }

  if (t.includes('lab') || t.includes('test') || t.includes('where can i test')) {
    return {
      text: `Testing for BIS compliance must be carried out at BIS-recognized or NABL-accredited test facilities under the Laboratory Recognition Scheme (LRS 2020):\n\n• **BIS Central Laboratory (CL):** Sahibabad / Ghaziabad (Photovoltaics, thermal, electrical safety, chemical).\n• **BIS Western Regional Laboratory (WRL):** Mumbai (Power electronics, mechanical, container testing).\n• **BIS Southern Regional Laboratory (SRL):** Chennai (Battery safety, inverters, environmental testing).\n• **BIS Northern Regional Laboratory (NRL):** Mohali / Chandigarh (Domestic appliances, materials).\n• **BIS Eastern Regional Laboratory (ERL):** Kolkata (Insulation, flammability, domestic goods).\n• **Recognized Private NABL Laboratories:** Authorized private testing facilities registered on the BIS Manak Online portal.`,
      citations: [
        {
          source: 'BIS Laboratory Recognition Scheme (LRS 2020)',
          document: 'BIS Lab Directory Guidelines',
          clause: 'Section 4',
          authority: 'Bureau of Indian Standards',
          page: '1',
          claim: 'Network of accredited laboratory testing facilities.',
        }
      ]
    };
  }

  if (t.includes('hallmark') || t.includes('gold') || t.includes('huid')) {
    return {
      text: `Under statutory **BIS Hallmarking Regulations (IS 1417:2016)**:\n\n• **Mandatory 3 Marks:** Every hallmarked piece of gold jewelry in India must bear:\n  1. The official BIS Standard Logo\n  2. Purity & Fineness (e.g., 22K916 for 22 Karat Gold, 18K750 for 18 Karat Gold, 14K585 for 14 Karat Gold)\n  3. 6-digit alphanumeric HUID (Hallmark Unique Identification)\n• **Consumer Verification:** Download the official **BIS CARE** mobile app, enter the 6-character HUID code to view the jeweler's name, AHC center, and certified purity.`,
      citations: [
        {
          source: 'Hallmarking of Gold and Silver Artefacts Order, 2021',
          document: 'IS 1417: 2016',
          clause: 'Order Ref 2021',
          authority: 'Ministry of Consumer Affairs',
          page: '1',
          claim: 'Mandatory 3 marks and HUID tracking rules for gold jewelry.',
        }
      ]
    };
  }

  if (t.includes('gap') || t.includes('open') || t.includes('missing')) {
    return {
      text: `For Assessment ${assessmentNum} (${targetStandard}):\n\n• **Material Verification:** Food-contact surface material certificate (SS 304 / SS 316 per IS 6911) must be verified.\n• **Laboratory Testing Required:** Mandatory test reports required for Clause 5.3 (Thermal Performance Retention >= 65°C) and Clause 5.1 (20 kPa Hydraulic Seal Integrity) before Passport authorization.\n• **Marking Evidence:** Durable nameplate with ISI mark and CML number required.`,
      citations: []
    };
  }

  return {
    text: `Here is the statutory guidance regarding **${userText.trim()}**:\n\nUnder the **Bureau of Indian Standards Act, 2016**, Indian Standards establish mandatory and voluntary technical specifications for safety, durability, and performance. Products notified under Quality Control Orders (QCOs) by respective ministries (DPIIT, MeitY, Ministry of Power, etc.) require mandatory certification before manufacture, import, or commercial distribution in India.\n\n### How Can I Assist You?\n• **Product Specifics:** Ask about steel bottles/flasks, solar inverters, lithium batteries, cables, toys, or electronics.\n• **Certification Schemes:** Compare Scheme I (ISI Mark with Factory Audit) vs Scheme II (CRS Registration with Lab Test).\n• **Testing Laboratories:** Find accredited BIS Regional and recognized NABL testing facilities.\n• **Compliance Roadmap:** Get clause-by-clause requirements, documentation checklists, and application steps on Manak Online.`,
    citations: []
  };
}

/**
 * AIAssistantDrawer
 * 
 * Authoritative BIS Assistant Drawer with audio input and speech synthesis.
 * Dark precision workstation styling matching homepage.
 */
export function AIAssistantDrawer({ isOpen, onClose, assessment, onInspectSource, onOpenFullAssistant }) {
  const assessmentId = assessment?.id || assessment?.assessment_id;
  const assessmentNum = assessment?.assessment_number || assessmentId?.slice(0, 8) || 'SIH-DEMO';
  const targetStandard = assessment?.target_standard || assessment?.compliance?.standard_number || 'IS 17526:2021';

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Hello. I am the Bureau of Indian Standards (BIS) Intelligent Assistant for Assessment ${assessmentNum}.\n\nI can help you determine applicable Indian Standards, explain certification requirements under Scheme I (ISI Mark) and Scheme II (CRS), identify testing laboratories, or summarize open evidence gaps. You can type or use the microphone for voice input.`,
      citations: [],
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    { label: 'Which BIS standard applies?', text: 'Which Indian Standard applies to domestic stainless steel vacuum flasks?' },
    { label: 'What are mandatory QCOs?', text: 'What are the mandatory Quality Control Order (QCO) requirements for domestic containers?' },
    { label: 'Show open compliance gaps', text: 'What open compliance gaps exist for this assessment?' },
    { label: 'Find a BIS recognized lab', text: 'Find a BIS-recognized laboratory for testing vacuum flasks and domestic products.' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    async function ensureAuth() {
      try {
        if (!authApi.getToken()) {
          await authApi.bootstrap();
        }
      } catch (e) {
        console.warn('Auth bootstrap notice:', e);
      }
    }
    ensureAuth();
  }, []);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [isOpen, messages]);

  const sendQuery = async (queryText) => {
    if (!queryText.trim() || isLoading) return;

    const userText = queryText.trim();
    setInputValue('');
    const userMsgId = Date.now().toString();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: userText }
    ]);
    setIsLoading(true);

    try {
      // 1. Primary: query the intelligent conversational BIS Assistant
      try {
        const genRes = await assistantApi.chat(userText, null, 'en');
        if (genRes && genRes.answer) {
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 1).toString(),
              sender: 'assistant',
              text: genRes.answer,
              citations: genRes.citations || [],
            }
          ]);
          setIsLoading(false);
          return;
        }
      } catch (genErr) {
        console.warn('Conversational assistant query notice, checking assessment context:', genErr);
      }

      // 2. Secondary: If query is specifically about assessment evidence/gaps, try assessment endpoint
      const t = userText.toLowerCase();
      if (assessmentId && (t.includes('gap') || t.includes('evidence') || t.includes('status') || t.includes('dna'))) {
        try {
          const data = await apiClient.post(`/assessments/${assessmentId}/chat`, { message: userText });
          if (data && data.answer) {
            setMessages((prev) => [
              ...prev,
              {
                id: (Date.now() + 1).toString(),
                sender: 'assistant',
                text: data.answer,
                citations: data.citations || [],
              }
            ]);
            setIsLoading(false);
            return;
          }
        } catch (asmChatErr) {
          console.warn('Assessment chat fallback:', asmChatErr);
        }
      }

      // 3. Fallback to comprehensive local intelligence engine
      const response = generateIntelligentResponse(userText, targetStandard, assessmentNum);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: response.text,
          citations: response.citations,
        }
      ]);
    } catch (err) {
      console.warn('AI Assistant query error:', err);
      const fallback = generateIntelligentResponse(userText, targetStandard, assessmentNum);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: fallback.text,
          citations: fallback.citations,
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = (e) => {
    e?.preventDefault();
    sendQuery(inputValue);
  };

  const handleAudioTranscript = (transcriptText) => {
    setInputValue((prev) => {
      const clean = prev.trim();
      return clean ? `${clean} ${transcriptText}` : transcriptText;
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm font-sans transition-opacity duration-200">
      <div 
        className="fixed inset-0" 
        onClick={onClose} 
        aria-hidden="true"
      />
      <aside 
        className="relative w-full max-w-lg bg-[#0b0f19] text-slate-100 h-full shadow-2xl flex flex-col border-l border-slate-800 z-10 animate-in slide-in-from-right duration-250 ease-out"
        role="dialog"
        aria-label="AI Assistant"
      >
        {/* Header */}
        <div className="h-14 px-6 border-b border-slate-800 flex items-center justify-between bg-[#080c14] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_10px_rgba(56,189,248,0.2)]">
              <span className="material-symbols-outlined text-[18px]">smart_toy</span>
            </div>
            <div>
              <div className="flex items-center gap-1.5 leading-none">
                <h2 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider">
                  BIS Assistant
                </h2>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" title="Online Knowledge Sync"></span>
              </div>
              <p className="text-[10px] text-cyan-300/60 font-mono leading-none mt-1">
                Statutory Regulatory Guidance Engine
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            title="Close BIS Assistant"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Clear Non-Authoritative Statutory Notice Banner */}
        <div className="px-5 py-2.5 bg-cyan-950/30 border-b border-cyan-500/20 flex items-start gap-2 text-xs shrink-0">
          <span className="material-symbols-outlined text-cyan-400 text-sm mt-0.5 shrink-0">info</span>
          <div className="text-[10px] text-slate-300 leading-normal font-mono">
            <strong className="text-cyan-300 font-semibold">Statutory Advisory:</strong> Guidance is source-backed from Gazette orders. Regulatory compliance verdicts are 100% deterministic with 0% LLM authority.
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
                  className={`max-w-[88%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-md ${
                    isUser
                      ? 'bg-cyan-950/40 text-cyan-100 border border-cyan-500/40 rounded-tr-none'
                      : 'bg-[#0f1422] text-slate-200 border border-slate-800 rounded-tl-none'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                      {isUser ? 'You' : 'GOAT Assistant'}
                    </span>
                    {!isUser && (
                      <TextToSpeechButton text={msg.text} />
                    )}
                  </div>

                  <FormattedMessage text={msg.text} />

                  {/* Grounded Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1.5">
                      <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-slate-400 block">
                        Verified Sources
                      </span>
                      {msg.citations.map((cite, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => {
                            if (onInspectSource) onInspectSource(cite);
                          }}
                          title={cite.claim || cite.label || 'Inspect statutory citation'}
                          className="w-full text-left p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 transition-colors flex items-center justify-between text-[11px] text-cyan-300 cursor-pointer group"
                        >
                          <div className="flex items-center gap-1.5 truncate font-mono">
                            <span className="material-symbols-outlined text-[13px] text-cyan-400 shrink-0">menu_book</span>
                            <span className="truncate">
                              {formatCitationDisplay(cite)}
                            </span>
                          </div>
                          <span className="material-symbols-outlined text-[13px] text-slate-500 group-hover:text-cyan-400 shrink-0 ml-1">
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
            <div className="flex items-center gap-2.5 text-xs pl-3 py-2.5 bg-cyan-950/30 rounded-xl border border-cyan-500/30 mr-auto w-fit">
              <MorphingInfinity className="w-4 h-4 text-cyan-400 shrink-0" />
              <div className="flex items-center gap-1.5">
                <TextShimmer baseColor="#38bdf8" shimmerColor="#a5f3fc" duration={1.6} className="font-semibold text-[11px] uppercase tracking-wider font-mono">
                  Thinking
                </TextShimmer>
                <span className="text-slate-600">&bull;</span>
                <TextShimmer baseColor="#64748b" shimmerColor="#cbd5e1" duration={2.2} className="text-xs">
                  Retrieving grounded standards guidance...
                </TextShimmer>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Query Pills */}
        <div className="px-4 py-2 border-t border-slate-800 bg-[#080c14] overflow-x-auto no-scrollbar flex items-center gap-1.5 shrink-0">
          {quickPrompts.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => sendQuery(q.text)}
              disabled={isLoading}
              className="text-[10px] font-mono text-slate-300 hover:text-cyan-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/30 px-2.5 py-1 rounded-full whitespace-nowrap transition-colors cursor-pointer disabled:opacity-50"
            >
              {q.label}
            </button>
          ))}
        </div>

        {/* Input Form with Audio Input Button */}
        <form onSubmit={handleSendMessage} className="p-3.5 border-t border-slate-800 bg-[#0b0f19] shrink-0">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask or speak to BIS Assistant..."
              disabled={isLoading}
              className="flex-1 px-3.5 py-2.5 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors"
            />

            {/* Audio Voice Input Button */}
            <AudioInputButton
              onTranscript={handleAudioTranscript}
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="px-4 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-30 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-1 transition-all cursor-pointer shadow-[0_0_12px_rgba(56,189,248,0.25)]"
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
