import React, { useState, useEffect } from 'react';
import {
  Clock, ShieldAlert, FileText, CheckCircle2, UserCheck, AlertOctagon,
  Calendar, FastForward, RotateCcw, Scale, Send
} from 'lucide-react';
import { fetchCases, advanceCase, submitDecision } from '../api';
import { CaseItem } from '../types';

interface CaseQueuePageProps {
  onRefreshStats: () => void;
}

export const CaseQueuePage: React.FC<CaseQueuePageProps> = ({ onRefreshStats }) => {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [approvalModal, setApprovalModal] = useState<{
    isOpen: boolean;
    type: 'SHOW_CAUSE' | 'CLASSIFICATION';
    caseId: string;
  } | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  const loadCases = async () => {
    setIsLoading(true);
    try {
      const data = await fetchCases();
      setCases(data);
      if (data.length > 0 && !selectedCase) {
        setSelectedCase(data[0]);
      } else if (selectedCase) {
        const updated = data.find((c) => c.case_id === selectedCase.case_id);
        if (updated) setSelectedCase(updated);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleSimulateDays = async (days: number) => {
    if (!selectedCase) return;
    try {
      await advanceCase(selectedCase.case_id, undefined, true, days);
      await loadCases();
    } catch (e) {
      console.error(e);
    }
  };

  const handleApproveNotice = async () => {
    if (!approvalModal) return;
    try {
      const targetStage = approvalModal.type === 'SHOW_CAUSE' ? 'SHOW_CAUSE_ISSUED' : 'CLASSIFIED';
      await advanceCase(approvalModal.caseId, targetStage, true, 0);
      setApprovalModal(null);
      await loadCases();
      setFeedbackSuccess(`Human compliance approval confirmed. Case moved to stage '${targetStage}'.`);
      setTimeout(() => setFeedbackSuccess(null), 5000);
    } catch (e: any) {
      alert(`Approval failed: ${e.message}`);
    }
  };

  const handleMarkFeedback = async (outcome: 'FALSE_POSITIVE' | 'CONFIRMED_MULE') => {
    if (!selectedCase) return;
    try {
      const res = await submitDecision(
        selectedCase.account_id,
        outcome,
        selectedCase.case_id,
        `Analyst registered ${outcome} outcome from Case Queue`
      );
      setFeedbackSuccess(
        outcome === 'FALSE_POSITIVE'
          ? `Marked as False Positive. Hold threshold adjusted ${res.prior_threshold_hold?.toFixed(2)} → ${res.current_threshold_hold?.toFixed(2)}.`
          : `Fraud confirmed. Protection threshold tightened ${res.prior_threshold_hold?.toFixed(2)} → ${res.current_threshold_hold?.toFixed(2)}.`
      );
      onRefreshStats();
      await loadCases();
      setTimeout(() => setFeedbackSuccess(null), 6000);
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-2">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-black tracking-tight text-white">Regulatory Case Clock Queue</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/80 text-amber-300 border border-amber-800">
              RBI Statutory Time Clock
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Tracks formal mule account cases under Section 35A Banking Regulation Act. Enforces 21-day show-cause and 14-day FMR deadlines.
          </p>
        </div>

        {/* Simulate Days Acceleration Control */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 p-1.5 rounded-xl text-xs">
          <span className="text-slate-400 font-mono px-2 flex items-center space-x-1">
            <FastForward className="w-3.5 h-3.5 text-cyan-400" />
            <span>Simulate Time:</span>
          </span>
          <button
            onClick={() => handleSimulateDays(1)}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-mono transition"
          >
            +1 Day
          </button>
          <button
            onClick={() => handleSimulateDays(5)}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-mono transition"
          >
            +5 Days
          </button>
          <button
            onClick={() => handleSimulateDays(14)}
            className="px-2.5 py-1 rounded-lg bg-[#E5334F] hover:bg-rose-600 text-white font-mono font-bold transition"
          >
            +14 Days
          </button>
        </div>
      </div>

      {feedbackSuccess && (
        <div className="p-4 rounded-xl bg-cyan-950/50 border border-cyan-800 text-cyan-200 text-xs flex items-center justify-between">
          <span>{feedbackSuccess}</span>
          <button onClick={() => setFeedbackSuccess(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Main Grid: Cases List (Left) & Case Dossier + Show-Cause Draft (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Case List */}
        <div className="lg:col-span-5 bg-[#0D1527] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="font-bold text-sm text-white flex items-center space-x-2">
              <Scale className="w-4 h-4 text-cyan-400" />
              <span>Active Investigation Dossiers</span>
            </span>
            <span className="text-xs text-slate-400 font-mono">{cases.length} active</span>
          </div>

          <div className="space-y-3">
            {cases.map((c) => {
              const isSelected = selectedCase?.case_id === c.case_id;
              const showCauseRemaining = Math.max(0, 21 - c.elapsed_days);
              const fmrRemaining = Math.max(0, 14 - Math.max(0, c.elapsed_days - 21));

              return (
                <div
                  key={c.case_id}
                  onClick={() => setSelectedCase(c)}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition space-y-2.5 ${
                    isSelected
                      ? 'bg-rose-950/30 border-[#E5334F] shadow-lg shadow-rose-950/40'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-white">{c.case_id}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300">
                      {c.stage}
                    </span>
                  </div>

                  <div className="text-xs text-slate-300 font-mono">
                    Target: <span className="text-cyan-300 font-bold">{c.account_id}</span>
                  </div>

                  {/* Clocks */}
                  <div className="flex items-center justify-between text-[11px] font-mono pt-1 border-t border-slate-800/80">
                    <div className="flex items-center space-x-1.5 text-amber-400">
                      <Clock className="w-3.5 h-3.5" />
                      <span>21d Show-Cause: {showCauseRemaining}d left</span>
                    </div>
                    {c.stage === 'CLASSIFIED' && (
                      <div className="text-rose-400 font-bold">
                        14d FMR: {fmrRemaining}d
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Case Dossier & Statutory Show-Cause Draft */}
        <div className="lg:col-span-7 bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="font-bold text-sm text-white">Forensic Dossier & Statutory Notice</span>
            <span className="text-xs font-mono text-cyan-400">{selectedCase?.case_id}</span>
          </div>

          {selectedCase ? (
            <div className="space-y-5">
              {/* Statutory Clock Countdown Card */}
              <div className="grid grid-cols-2 gap-3 bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-xs font-mono">
                <div>
                  <span className="text-slate-400 text-[10px] block uppercase">Show-Cause Representation:</span>
                  <span className="text-lg font-bold text-amber-400">
                    {Math.max(0, 21 - selectedCase.elapsed_days)} Days Remaining
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Section 35A BR Act Clock</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block uppercase">Mandatory FMR Filing Clock:</span>
                  <span className="text-lg font-bold text-rose-400">
                    {selectedCase.stage === 'CLASSIFIED' ? `${Math.max(0, 14 - Math.max(0, selectedCase.elapsed_days - 21))} Days` : 'Standby'}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">Central Fraud Registry Clock</span>
                </div>
              </div>

              {/* LLM Forensic Case Summary */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Forensic Investigation Summary:
                </span>
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                  {selectedCase.llm_case_summary || 'Forensic analysis dossier in preparation.'}
                </div>
              </div>

              {/* LLM Show-Cause Notice Draft */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Statutory Notice Draft (Section 35A):
                  </span>
                  <span className="text-[10px] text-amber-400 font-mono">Requires Human Approval</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-line leading-relaxed max-h-56 overflow-y-auto">
                  {selectedCase.show_cause_draft || 'Notice draft generated via LLM compliance engine.'}
                </div>
              </div>

              {/* Human Approval Gates & Feedback Buttons */}
              <div className="pt-2 flex flex-wrap items-center gap-3 border-t border-slate-800">
                <button
                  onClick={() => setApprovalModal({ isOpen: true, type: 'SHOW_CAUSE', caseId: selectedCase.case_id })}
                  className="px-4 py-2.5 rounded-xl text-xs font-bold bg-[#E5334F] hover:bg-rose-600 text-white shadow-lg transition flex items-center space-x-1.5"
                >
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>Approve Show-Cause Notice</span>
                </button>

                <button
                  onClick={() => setApprovalModal({ isOpen: true, type: 'CLASSIFICATION', caseId: selectedCase.case_id })}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                >
                  Confirm Fraud Classification
                </button>

                <div className="ml-auto flex items-center space-x-2">
                  <button
                    onClick={() => handleMarkFeedback('FALSE_POSITIVE')}
                    className="px-3 py-2 rounded-xl text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-amber-300 border border-slate-700 transition"
                    title="Mark False Positive and relax threshold"
                  >
                    Mark False Positive
                  </button>
                  <button
                    onClick={() => handleMarkFeedback('CONFIRMED_MULE')}
                    className="px-3 py-2 rounded-xl text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-rose-300 border border-slate-700 transition"
                    title="Confirm mule account and tighten threshold"
                  >
                    Confirm Mule
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic py-8 text-center">Select a case to inspect dossier.</div>
          )}
        </div>
      </div>

      {/* Human Approval Confirmation Modal */}
      {approvalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-[#0D1527] border-2 border-[#E5334F] rounded-2xl p-6 text-slate-100 shadow-2xl space-y-4">
            <div className="flex items-center space-x-3 text-[#E5334F]">
              <AlertOctagon className="w-6 h-6" />
              <h3 className="font-bold text-base text-white">Statutory Human Sign-Off Gate</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              In accordance with banking safety governance, the automated system never classifies anyone as a fraudster or issues legal notices autonomously.
              You are confirming your compliance authorization for case <span className="font-mono text-cyan-300">{approvalModal.caseId}</span>.
            </p>
            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setApprovalModal(null)}
                className="px-4 py-2 rounded-xl text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleApproveNotice}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-[#E5334F] text-white hover:bg-rose-600 shadow-lg transition"
              >
                Confirm Compliance Authorization
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
