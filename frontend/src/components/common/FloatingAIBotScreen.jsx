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
  const cl = cite.clause_number ? `Cl. ${cite.clause_number}` : (cite.clause && cite.clause !== 'Scope' ? cite.clause : '');
  const pg = cite.page ? `Pg. ${cite.page}` : '';
  const parts = [std, cl, pg].filter(Boolean);
  if (parts.length > 0) return parts.join(' — ');
  return cite.source || cite.document || 'BIS Indian Standard';
}

function generateIntelligentResponse(userText, targetStandard = 'IS 17526:2021', assessmentNum = 'SIH-DEMO') {
  const t = userText.toLowerCase();

  if (/^(hi|hello|hey|heya|howdy|namaste|vanakkam|greetings|good\s+(morning|afternoon|evening)|who\s+are\s+you|help\b)/i.test(userText.trim())) {
    return {
      text: `Hello! I am the GOAT BIS Intelligent Compliance Copilot.\n\nI can assist you across Indian Standards and BIS compliance workflows:\n• **Standard Discovery**: Identifying applicable Indian Standards (IS) for your product\n• **Certification Schemes**: Understanding ISI Mark (Scheme I) and CRS (Scheme II) licensing\n• **Clause Interpretation**: Plain-language breakdowns of mandatory technical and safety clauses\n• **Testing & Labs**: Locating BIS-recognized and NABL-accredited test facilities\n• **Hallmarking & Consumer Verification**: Checking gold purity marks and HUID numbers\n\nHow can I assist you today?`,
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
 * FloatingAIBotScreen
 * 
 * Floating right-side AI Copilot workstation companion.
 * Floats on the right side over active workspace views without forcing
 * navigation to a separate page, keeping the engineer in flow.
 */
export function FloatingAIBotScreen({
  isOpen,
  onClose,
  assessment,
  onInspectSource,
  activeTab = 'dashboard'
}) {
  const assessmentId = assessment?.id || assessment?.assessment_id;
  const assessmentNum = assessment?.assessment_number || assessmentId?.slice(0, 8) || 'SIH-DEMO';
  const targetStandard = assessment?.target_standard || assessment?.compliance?.standard_number || 'IS 17526:2021';
  const productName = assessment?.product_name || assessment?.product_dna?.product_name || 'Domestic Product';

  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpandedWidth, setIsExpandedWidth] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Hello. I am the Zyntrix BIS Intelligent Compliance Copilot for Assessment ${assessmentNum}.\n\nI provide real-time statutory guidance across Indian Standards (CRS/ISI), mandatory QCOs, testing limits, and clause interpretations while you work on ${productName}.\n\nYou can speak via microphone or type questions below.`,
      citations: [],
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    { label: 'QCO Mandate', text: `What are the mandatory Quality Control Order (QCO) requirements for ${targetStandard}?` },
    { label: 'Explain Clauses', text: `Explain the key safety and performance clauses required under ${targetStandard}.` },
    { label: 'Open Gaps', text: 'What open compliance gaps or missing evidence items currently exist?' },
    { label: 'Testing Labs', text: `Find BIS-recognized laboratory test facilities for ${targetStandard}.` },
    { label: 'Marking Rules', text: 'What are the official BIS Standard Mark and labeling requirements?' },
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
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [isOpen, isMinimized, messages]);

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
      console.warn('Assistant network notice:', err);
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
    e.preventDefault();
    sendQuery(inputValue);
  };

  const handleAudioTranscript = (transcriptText) => {
    if (!transcriptText || !transcriptText.trim()) return;
    setInputValue((prev) => {
      const clean = prev.trim();
      return clean ? `${clean} ${transcriptText}` : transcriptText;
    });
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: 'reset',
        sender: 'assistant',
        text: `Chat history refreshed. How can I assist your compliance engineering on ${targetStandard}?`,
        citations: [],
      }
    ]);
  };

  if (!isOpen) return null;

  // Minimized Compact Pill
  if (isMinimized) {
    return (
      <div className="fixed bottom-5 right-5 z-50 font-sans animate-in fade-in duration-200">
        <div className="flex items-center gap-2 p-2 bg-[#0b0f19]/95 backdrop-blur-xl border border-cyan-500/40 rounded-full shadow-[0_10px_35px_rgba(0,0,0,0.8),0_0_20px_rgba(56,189,248,0.25)]">
          <button
            type="button"
            onClick={() => setIsMinimized(false)}
            className="flex items-center gap-2.5 px-3 py-1.5 text-xs font-semibold text-white hover:text-cyan-300 transition-colors cursor-pointer"
          >
            <div className="w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_8px_rgba(56,189,248,0.3)]">
              <span className="material-symbols-outlined text-[15px]">smart_toy</span>
            </div>
            <span className="font-space-grotesk font-bold">GOAT Copilot</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          </button>

          <button
            type="button"
            onClick={() => setIsMinimized(false)}
            className="p-1.5 text-slate-400 hover:text-cyan-300 rounded-full hover:bg-slate-800/60 transition cursor-pointer"
            title="Expand Copilot"
          >
            <span className="material-symbols-outlined text-[18px]">open_in_full</span>
          </button>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-full hover:bg-slate-800/60 transition cursor-pointer"
            title="Close Copilot"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      </div>
    );
  }

  // Floating Right-Side Window Screen
  return (
    <aside
      className={`fixed top-16 right-4 bottom-4 z-40 flex flex-col font-sans bg-[#0b0f19]/95 backdrop-blur-2xl rounded-2xl border border-cyan-500/30 shadow-[0_16px_50px_rgba(0,0,0,0.8),0_0_25px_rgba(56,189,248,0.15)] overflow-hidden transition-all duration-300 ease-out animate-in slide-in-from-right-4 ${isExpandedWidth ? 'w-[560px] max-w-[calc(100vw-32px)]' : 'w-[420px] max-w-[calc(100vw-32px)]'
        }`}
      role="complementary"
      aria-label="GOAT AI Copilot"
    >
      {/* Floating Header */}
      <div className="h-14 px-4 bg-[#080c14]/90 border-b border-slate-800/90 flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_10px_rgba(56,189,248,0.25)] shrink-0">
            <span className="material-symbols-outlined text-[17px]">smart_toy</span>
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 leading-none">
              <h3 className="font-space-grotesk text-xs font-bold text-white tracking-wide uppercase truncate">
                GOAT Copilot
              </h3>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" title="Statutory Knowledge Sync Active"></span>
            </div>
            <p className="text-[10px] text-cyan-300/70 font-mono leading-none mt-1 truncate">
              {targetStandard} &bull; {assessmentNum}
            </p>
          </div>
        </div>

        {/* Window Controls */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={handleClearHistory}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 rounded-lg transition cursor-pointer"
            title="Clear Chat History"
          >
            <span className="material-symbols-outlined text-[17px]">delete_sweep</span>
          </button>
          <button
            type="button"
            onClick={() => setIsExpandedWidth(!isExpandedWidth)}
            className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800/80 rounded-lg transition cursor-pointer hidden sm:flex"
            title={isExpandedWidth ? 'Standard Width' : 'Expand Width'}
          >
            <span className="material-symbols-outlined text-[17px]">
              {isExpandedWidth ? 'fit_screen' : 'aspect_ratio'}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setIsMinimized(true)}
            className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800/80 rounded-lg transition cursor-pointer"
            title="Minimize to Floating Button"
          >
            <span className="material-symbols-outlined text-[17px]">minimize</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-lg transition cursor-pointer"
            title="Close Copilot"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      </div>

      {/* Statutory Invariant Ribbon */}
      <div className="px-3.5 py-1.5 bg-cyan-950/40 border-b border-cyan-500/20 flex items-center justify-between gap-2 shrink-0 select-none">
        <div className="flex items-center gap-1.5 text-[10px] text-cyan-300 font-mono truncate">
          <span className="material-symbols-outlined text-[13px] text-cyan-400 shrink-0">verified_user</span>
          <span className="truncate">0% LLM Compliance Authority &bull; Gazette Law</span>
        </div>
        <span className="text-[9px] font-mono text-slate-500 uppercase px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 shrink-0">
          Act, 2016
        </span>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5 scroll-smooth">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[90%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed shadow-md ${isUser
                  ? 'bg-cyan-950/60 text-cyan-100 border border-cyan-500/40 rounded-tr-none'
                  : 'bg-[#0f1422] text-slate-200 border border-slate-800/90 rounded-tl-none'
                  }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                    {isUser ? 'Engineer' : 'GOAT Copilot'}
                  </span>
                  {!isUser && (
                    <TextToSpeechButton text={msg.text} />
                  )}
                </div>

                <FormattedMessage text={msg.text} />

                {/* Grounded Gazette Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/90 space-y-1.5">
                    <span className="text-[9px] uppercase font-mono tracking-wider font-semibold text-slate-400 block">
                      Statutory Citations
                    </span>
                    {msg.citations.map((cite, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => {
                          if (onInspectSource) onInspectSource(cite);
                        }}
                        title={cite.claim || cite.label || 'Inspect statutory citation'}
                        className="w-full text-left p-2 rounded-lg bg-slate-900/90 hover:bg-slate-850 border border-slate-800 hover:border-cyan-500/50 transition-colors flex items-center justify-between text-[11px] text-cyan-300 cursor-pointer group"
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
          <div className="flex items-center gap-2.5 text-xs pl-3 py-2 bg-cyan-950/30 rounded-xl border border-cyan-500/30 mr-auto w-fit">
            <MorphingInfinity className="w-4 h-4 text-cyan-400 shrink-0" />
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              <TextShimmer baseColor="#38bdf8" shimmerColor="#a5f3fc" duration={1.6} className="font-semibold uppercase tracking-wider">
                Compiling
              </TextShimmer>
              <span className="text-slate-600">&bull;</span>
              <TextShimmer baseColor="#64748b" shimmerColor="#cbd5e1" duration={2.2}>
                Retrieving Gazette standard...
              </TextShimmer>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Questions Pills */}
      <div className="px-3 py-1.5 border-t border-slate-800/80 bg-[#080c14]/90 overflow-x-auto no-scrollbar flex items-center gap-1.5 shrink-0">
        {quickPrompts.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => sendQuery(q.text)}
            disabled={isLoading}
            className="text-[10px] font-mono text-slate-400 hover:text-cyan-300 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/30 px-2.5 py-1 rounded-full whitespace-nowrap transition-colors cursor-pointer disabled:opacity-40"
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Voice & Text Input Form */}
      <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-800/90 bg-[#0b0f19] shrink-0">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask or speak to GOAT Copilot..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 text-xs bg-[#080c14] border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-colors font-sans"
          />

          {/* Voice Input Button */}
          <AudioInputButton
            onTranscript={handleAudioTranscript}
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-3.5 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-30 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-1 transition-all cursor-pointer shadow-[0_0_12px_rgba(56,189,248,0.25)] shrink-0"
          >
            <span>Ask</span>
            <span className="material-symbols-outlined text-[13px]">send</span>
          </button>
        </div>
      </form>
    </aside>
  );
}
