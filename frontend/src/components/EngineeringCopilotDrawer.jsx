import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Send,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  FileText,
  CheckCircle2,
  XCircle,
  ExternalLink,
  ChevronRight,
  Layers,
  Box,
  Hash,
  RefreshCw,
  X,
} from 'lucide-react';
import { aiApi } from '../api';

export function EngineeringCopilotDrawer({ jobId, activeStandardId, onOpenReview, onOpenEvidence }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [providerConfigured, setProviderConfigured] = useState(true);
  const [unconfiguredMessage, setUnconfiguredMessage] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [proposals, setProposals] = useState([]);
  const messagesEndRef = useRef(null);

  // Check health on load
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await aiApi.checkHealth();
        if (res.configured === false) {
          setProviderConfigured(false);
          setUnconfiguredMessage(res.message || 'AI unavailable — configure an approved LLM provider.');
        } else {
          setProviderConfigured(true);
        }
      } catch (err) {
        setProviderConfigured(false);
        setUnconfiguredMessage('AI unavailable — configure an approved LLM provider in environment.');
      }
    }
    checkHealth();
  }, []);

  // Fetch pending proposals for job
  useEffect(() => {
    if (!jobId || !isOpen) return;
    async function fetchProposals() {
      try {
        const res = await aiApi.getProposals(jobId);
        setProposals(res.filter((p) => p.status === 'PROPOSED'));
      } catch (err) {
        console.error('Failed to fetch AI proposals:', err);
      }
    }
    fetchProposals();
  }, [jobId, isOpen]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend) => {
    const userQuery = textToSend || input.trim();
    if (!userQuery || isLoading || !jobId) return;

    setInput('');
    const userMsg = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: userQuery,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await aiApi.sendMessage(jobId, userQuery, conversationId);
      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      const asstMsg = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        sources: res.sources || [],
        suggestedActions: res.suggested_actions || [],
        requiresHumanAction: res.requires_human_action || false,
        authorityLevel: res.authority_level || 'AI_ASSISTED',
        modelConfidence: res.model_confidence,
        agent: res.agent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, asstMsg]);

      // Refresh proposals
      const updatedProps = await aiApi.getProposals(jobId);
      setProposals(updatedProps.filter((p) => p.status === 'PROPOSED'));
    } catch (err) {
      const errCode = err.response?.data?.detail?.error_code;
      const errMsg = err.response?.data?.detail?.message || err.message;

      if (err.response?.status === 503 || errCode === 'AI_PROVIDER_NOT_CONFIGURED') {
        setProviderConfigured(false);
        setUnconfiguredMessage('AI unavailable — configure an approved LLM provider.');
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'error',
          content:
            errCode === 'AI_PROVIDER_NOT_CONFIGURED'
              ? 'AI unavailable — configure an approved LLM provider in environment (`LLM_PROVIDER`, `LLM_API_KEY`). Under zero-hallucination statutory rules, canned responses are prohibited.'
              : `Assistant Error: ${errMsg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmProposal = async (proposalId) => {
    try {
      await aiApi.confirmProposal(proposalId);
      setProposals((prev) => prev.filter((p) => p.id !== proposalId));
      setMessages((prev) => [
        ...prev,
        {
          id: `conf_${Date.now()}`,
          role: 'system_confirmation',
          content: `Proposal ${proposalId} has been CONFIRMED by human reviewer. Action executed.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err) {
      alert(`Failed to confirm proposal: ${err.message}`);
    }
  };

  const handleRejectProposal = async (proposalId) => {
    try {
      await aiApi.rejectProposal(proposalId, 'Dismissed from copilot UI');
      setProposals((prev) => prev.filter((p) => p.id !== proposalId));
    } catch (err) {
      alert(`Failed to reject proposal: ${err.message}`);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white shadow-2xl border border-slate-700 transition cursor-pointer group"
      >
        <div className="relative">
          <Bot className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-xs font-bold font-mono tracking-wider">ENGINEERING COPILOT</span>
          <span className="text-[10px] text-slate-400 font-mono">LangGraph Orchestrated</span>
        </div>
        <span className="ml-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          AI ASSISTED
        </span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-40 w-[440px] max-w-[calc(100vw-2rem)] h-[620px] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden text-xs text-slate-100 font-sans backdrop-blur-xl">
      {/* Header */}
      <div className="p-3.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-400 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-slate-100 font-mono tracking-wide text-xs">ENGINEERING COPILOT</h4>
              <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                AI ASSISTED
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Deterministic Invariant &bull; Zero Statutory Authority
            </span>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="w-7 h-7 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 flex items-center justify-center transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Unconfigured Provider Banner */}
      {!providerConfigured && (
        <div className="p-3 bg-amber-500/10 border-b border-amber-500/30 text-amber-300 text-[11px] flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">AI Provider Not Configured</span>
            <p className="text-[10px] text-amber-200/80 mt-0.5 leading-relaxed">
              AI unavailable — configure an approved LLM provider in environment (`LLM_PROVIDER`, `LLM_API_KEY`).
              Under our statutory integrity policy, canned/fake responses are prohibited.
            </p>
          </div>
        </div>
      )}

      {/* Pending Proposals Bar */}
      {proposals.length > 0 && (
        <div className="px-3 py-2 bg-indigo-950/60 border-b border-indigo-800/40 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] text-indigo-300 font-mono">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{proposals.length} Action Proposal(s) Awaiting Human Gate</span>
          </div>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 p-3.5 overflow-y-auto space-y-3.5 bg-slate-900/50">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-300">
              <Bot className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <p className="font-bold text-slate-200 text-xs">Authoritative AI Engineering Copilot</p>
              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed max-w-xs">
                Ask about assessment results, CAD measurements, codified clauses, evidence provenance, or draft dossier
                sections.
              </p>
            </div>
            <div className="w-full pt-2 space-y-1.5">
              <button
                onClick={() => handleSend('Why did Clause 4.2.2 fail?')}
                className="w-full text-left px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-[11px] text-slate-300 hover:text-white transition flex items-center justify-between"
              >
                <span>"Why did Clause 4.2.2 fail?"</span>
                <ChevronRight className="w-3 h-3 text-slate-500" />
              </button>
              <button
                onClick={() => handleSend('What evidence supports enclosure height?')}
                className="w-full text-left px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-[11px] text-slate-300 hover:text-white transition flex items-center justify-between"
              >
                <span>"What evidence supports enclosure height?"</span>
                <ChevronRight className="w-3 h-3 text-slate-500" />
              </button>
              <button
                onClick={() => handleSend('What requirements still need human review?')}
                className="w-full text-left px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-[11px] text-slate-300 hover:text-white transition flex items-center justify-between"
              >
                <span>"What requirements still need human review?"</span>
                <ChevronRight className="w-3 h-3 text-slate-500" />
              </button>
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
            {/* Role Header */}
            <div className="flex items-center gap-1.5 mb-1 text-[10px] text-slate-400 font-mono">
              {m.role === 'user' ? (
                <>
                  <span>You</span>
                  <User className="w-3 h-3" />
                </>
              ) : m.role === 'error' ? (
                <>
                  <ShieldAlert className="w-3 h-3 text-rose-400" />
                  <span className="text-rose-400 font-bold">System Alert</span>
                </>
              ) : (
                <>
                  <Bot className="w-3 h-3 text-indigo-400" />
                  <span className="text-indigo-400 font-bold">{m.agent || 'AI Copilot'}</span>
                  <span className="text-slate-500">&bull; {m.authorityLevel || 'AI_ASSISTED'}</span>
                </>
              )}
              <span className="text-slate-600">{m.timestamp}</span>
            </div>

            {/* Bubble */}
            <div
              className={`p-3 rounded-xl max-w-[90%] text-[11.5px] leading-relaxed whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none'
                  : m.role === 'error'
                  ? 'bg-rose-950/40 border border-rose-800/50 text-rose-200 rounded-bl-none'
                  : 'bg-slate-800/90 border border-slate-700/80 text-slate-200 rounded-bl-none shadow-md'
              }`}
            >
              {m.content}

              {/* Human Action Required Alert */}
              {m.requiresHumanAction && (
                <div className="mt-2.5 p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10.5px] flex items-center gap-1.5 font-mono font-bold">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                  <span>HUMAN ACTION REQUIRED &bull; Confirmation Gate</span>
                </div>
              )}

              {/* Citations List */}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2.5 pt-2.5 border-t border-slate-700/60 space-y-1">
                  <span className="text-[10px] font-mono text-slate-400 block font-bold">AUTHORITATIVE CITATIONS:</span>
                  {m.sources.map((src, i) => (
                    <div
                      key={i}
                      className="p-1.5 rounded bg-slate-900/60 border border-slate-700/50 text-[10px] flex items-center justify-between font-mono"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="px-1 py-0.2 rounded text-[8px] bg-slate-800 text-slate-300 border border-slate-700">
                          {src.source_type}
                        </span>
                        <span className="text-slate-300 truncate">{src.claim}</span>
                      </div>
                      <span className="text-emerald-400 font-bold shrink-0 ml-2">{src.support_status}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Suggested Actions / Proposals */}
              {m.suggestedActions && m.suggestedActions.length > 0 && (
                <div className="mt-2.5 pt-2.5 border-t border-slate-700/60 space-y-2">
                  <span className="text-[10px] font-mono text-indigo-300 block font-bold">
                    AI ACTION PROPOSALS (HUMAN GATE):
                  </span>
                  {m.suggestedActions.map((act, i) => (
                    <div
                      key={i}
                      className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-700/40 space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[9px] font-mono font-bold text-indigo-300 uppercase tracking-wider">
                          AI SUGGESTION &bull; {act.action}
                        </span>
                        <span className="text-[9px] font-mono text-amber-400 font-bold">REQUIRES CONFIRMATION</span>
                      </div>
                      <p className="text-[10.5px] text-slate-300 leading-snug">{act.description || act.label}</p>
                      {act.proposal_id && (
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => handleConfirmProposal(act.proposal_id)}
                            className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-[10px] font-bold transition flex items-center gap-1 cursor-pointer"
                          >
                            <CheckCircle2 className="w-3 h-3" />
                            Confirm Action
                          </button>
                          <button
                            onClick={() => handleRejectProposal(act.proposal_id)}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 font-mono text-[10px] transition cursor-pointer"
                          >
                            Dismiss
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px] p-2">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
            <span>Orchestrating specialist agent reasoning...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="p-3 bg-slate-950 border-t border-slate-800 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={providerConfigured ? "Ask engineering copilot..." : "Configure LLM provider in environment..."}
          disabled={!providerConfigured || isLoading}
          className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!providerConfigured || isLoading || !input.trim()}
          className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-mono text-xs font-bold transition flex items-center gap-1 cursor-pointer disabled:cursor-not-allowed"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
