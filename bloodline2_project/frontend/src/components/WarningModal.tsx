import React, { useState, useEffect, useRef } from 'react';
import { AlertOctagon, PhoneCall, XCircle, CheckCircle2, ArrowRight, ShieldAlert, Clock } from 'lucide-react';
import { ScanResponse } from '../types';

interface WarningModalProps {
  isOpen: boolean;
  scanData: ScanResponse | null;
  onCancelPayment: () => void;
  onProceedAnyway: () => void;
}

export const WarningModal: React.FC<WarningModalProps> = ({
  isOpen,
  scanData,
  onCancelPayment,
  onProceedAnyway
}) => {
  const [timeLeft, setTimeLeft] = useState(60);
  const [confirmedRisk, setConfirmedRisk] = useState(false);
  const [showHelpline, setShowHelpline] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      setTimeLeft(60);
      setConfirmedRisk(false);
      setShowHelpline(false);
      return;
    }

    // Trap focus in modal
    modalRef.current?.focus();

    // Prevent background scrolling
    document.body.style.overflow = 'hidden';

    // 60-second timer countdown
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      clearInterval(timer);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Handle accidental Escape key suppression
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  if (!isOpen || !scanData) return null;

  const isTimerDone = timeLeft === 0;
  const progressPercent = ((60 - timeLeft) / 60) * 100;
  const strokeDashoffset = 283 - (283 * progressPercent) / 100;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="warning-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200"
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        className="relative w-full max-w-2xl bg-[#0D1527] border-2 border-[#E5334F]/80 rounded-2xl shadow-2xl shadow-rose-950/80 p-6 md:p-8 text-slate-100 outline-none overflow-hidden"
      >
        {/* Glow accent */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-[#E5334F]/20 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-start space-x-4 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center shrink-0 shadow-lg shadow-rose-950/50">
            <AlertOctagon className="w-7 h-7 text-[#E5334F] animate-pulse" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase bg-rose-950 text-rose-400 border border-rose-800">
                {scanData.verdict === 'HOLD' ? 'Administrative Hold Recommended' : 'Cooling-Off Delay Triggered'}
              </span>
              <span className="text-xs text-slate-400 font-mono">Risk: {(scanData.probability * 100).toFixed(1)}%</span>
            </div>
            <h2 id="warning-modal-title" className="text-xl md:text-2xl font-bold tracking-tight text-white mt-1">
              Scammers rush you. Pause for a moment.
            </h2>
            <p className="text-xs md:text-sm text-slate-300 mt-1">
              Our automated fraud defense detected severe mule-account anomalies on beneficiary{' '}
              <span className="font-mono font-semibold text-rose-300">{scanData.account_id}</span>.
            </p>
          </div>
        </div>

        {/* Circular Countdown Timer + Narrative Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 items-center bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          {/* Animated Circular Timer */}
          <div className="flex flex-col items-center justify-center col-span-1 border-b md:border-b-0 md:border-r border-slate-800 pb-3 md:pb-0 md:pr-3">
            <div className="relative w-24 h-24 flex items-center justify-center">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="currentColor"
                  strokeWidth="6"
                  className="text-slate-800"
                  fill="transparent"
                />
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="currentColor"
                  strokeWidth="6"
                  strokeDasharray="251.2"
                  strokeDashoffset={(251.2 * timeLeft) / 60}
                  strokeLinecap="round"
                  className="text-[#E5334F] transition-all duration-1000 ease-linear"
                  fill="transparent"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center">
                <span className="font-mono font-extrabold text-2xl text-white">{timeLeft}</span>
                <span className="text-[9px] uppercase tracking-wider text-slate-400">Seconds</span>
              </div>
            </div>
            <button
              onClick={() => setTimeLeft(0)}
              className="mt-2 text-[10px] text-cyan-400 hover:text-cyan-300 underline font-medium transition"
              title="Skip countdown for demonstration purposes"
            >
              Skip timer (Demo)
            </button>
          </div>

          {/* Top 3 Plain Language Reasons */}
          <div className="col-span-3 space-y-2.5">
            <div className="text-xs uppercase font-bold tracking-wider text-amber-400 flex items-center space-x-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Why this payment was intercepted:</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-200">
              {scanData.plain_language_reasons && scanData.plain_language_reasons.length > 0 ? (
                scanData.plain_language_reasons.map((reason, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#E5334F] mt-1.5 shrink-0" />
                    <span>{reason}</span>
                  </li>
                ))
              ) : (
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E5334F] mt-1.5 shrink-0" />
                  <span>Beneficiary account displays high-velocity pass-through characteristics without balance retention.</span>
                </li>
              )}
            </ul>
          </div>
        </div>

        {/* Counterfactual Insight */}
        {scanData.counterfactual && (
          <div className="mb-6 p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-xs text-cyan-200 flex items-start space-x-2.5">
            <Clock className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
            <div>
              <span className="font-bold text-cyan-300 uppercase tracking-wide text-[10px] block">
                Counterfactual Explainability (Perturbation Search):
              </span>
              <p className="mt-0.5 text-slate-300">{scanData.counterfactual}</p>
            </div>
          </div>
        )}

        {/* Second Confirmation Checkbox (Required before Proceed) */}
        <div className="mb-6 flex items-start space-x-2.5 bg-slate-900/40 p-3 rounded-lg border border-slate-800">
          <input
            id="risk-checkbox"
            type="checkbox"
            checked={confirmedRisk}
            onChange={(e) => setConfirmedRisk(e.target.checked)}
            disabled={!isTimerDone}
            className="mt-0.5 w-4 h-4 rounded bg-slate-800 border-slate-700 text-[#E5334F] focus:ring-[#E5334F] focus:ring-offset-slate-900 disabled:opacity-40"
          />
          <label
            htmlFor="risk-checkbox"
            className={`text-xs select-none ${isTimerDone ? 'text-slate-300 cursor-pointer' : 'text-slate-500'}`}
          >
            I acknowledge that this destination account exhibits verified mule network markers.
            I understand that funds transferred to this account may be irrecoverable.
          </label>
        </div>

        {/* Helpline Popup Panel */}
        {showHelpline && (
          <div className="mb-6 p-4 rounded-xl bg-slate-800 border border-amber-500/50 text-xs space-y-2 animate-in fade-in">
            <div className="font-bold text-amber-400 flex items-center space-x-2">
              <PhoneCall className="w-4 h-4" />
              <span>National Cyber Fraud Helpline & Bank Security Desk</span>
            </div>
            <p className="text-slate-300">
              If you were instructed to send money by an unknown caller claiming to be from the police, CBI, tax authorities, or customs, hang up immediately.
            </p>
            <div className="flex flex-wrap gap-2 pt-1 font-mono text-xs">
              <span className="px-2.5 py-1 bg-slate-900 rounded border border-slate-700 text-white font-bold">
                Toll-Free Cyber Helpline: 1930
              </span>
              <span className="px-2.5 py-1 bg-slate-900 rounded border border-slate-700 text-emerald-400">
                Bank Fraud Desk: 1800-425-0018
              </span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-800">
          {/* Primary Action: Cancel Payment */}
          <button
            onClick={onCancelPayment}
            className="w-full sm:w-auto px-6 py-3 rounded-xl text-xs md:text-sm font-bold bg-[#E5334F] hover:bg-rose-600 text-white shadow-lg shadow-rose-950 transition flex items-center justify-center space-x-2"
          >
            <XCircle className="w-4 h-4" />
            <span>Cancel Payment (Protect Funds)</span>
          </button>

          <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
            {/* Secondary Action: Call My Bank */}
            <button
              onClick={() => setShowHelpline(!showHelpline)}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition flex items-center space-x-1.5"
            >
              <PhoneCall className="w-3.5 h-3.5 text-amber-400" />
              <span>Call Bank Helpline</span>
            </button>

            {/* Restricted Secondary Action: Proceed Anyway */}
            <button
              onClick={onProceedAnyway}
              disabled={!isTimerDone || !confirmedRisk}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800/60 hover:bg-slate-700 text-slate-400 disabled:opacity-40 disabled:cursor-not-allowed border border-slate-700/60 transition flex items-center space-x-1.5"
            >
              <span>Proceed Anyway</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
