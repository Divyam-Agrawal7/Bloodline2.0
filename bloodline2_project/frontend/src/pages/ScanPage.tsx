import React, { useState, useEffect } from 'react';
import {
  Shield, Send, AlertTriangle, CheckCircle, Clock, GitBranch,
  ArrowRight, Info, UserCheck, RefreshCw, Lock, ShieldAlert,
  Search, ExternalLink, Zap
} from 'lucide-react';
import { runScan, fetchDetectedMules, requestLienHold } from '../api';
import { ScanResponse, MuleAccountItem } from '../types';
import { RiskGauge } from '../components/RiskGauge';

interface ScanPageProps {
  onTriggerWarning: (data: ScanResponse) => void;
  onNavigateToMoneyDNA?: (accountId: string, chainId?: string) => void;
  initialAccount?: string;
  initialAmount?: number;
}

export const ScanPage: React.FC<ScanPageProps> = ({
  onTriggerWarning,
  onNavigateToMoneyDNA,
  initialAccount = 'ACC02228',
  initialAmount = 95000.0
}) => {
  const [payeeId, setPayeeId] = useState(initialAccount);
  const [amount, setAmount] = useState<number>(initialAmount);
  const [remark, setRemark] = useState('Contractor urgent advance');
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Live Detected Mules from database
  const [detectedMules, setDetectedMules] = useState<MuleAccountItem[]>([]);
  const [isLoadingMules, setIsLoadingMules] = useState(false);
  const [activeTabFilter, setActiveTabFilter] = useState<'mules' | 'legit'>('mules');
  const [isHolding, setIsHolding] = useState(false);

  // Legitimate sample accounts for benchmark comparison
  const legitAccounts = [
    { id: 'ACC00053', label: 'Divya Hegde (Private Wealth Client)', amount: 450, bank: 'INTERNAL', role: 'NORMAL' },
    { id: 'ACC02041', label: 'Reddy Stores (Verified Retail Merchant)', amount: 1250, bank: 'BANK_ALPHA', role: 'MERCHANT' },
    { id: 'ACC01370', label: 'Pooja Patel (Salaried Executive)', amount: 5000, bank: 'BANK_BETA', role: 'NORMAL' }
  ];

  // Load detected mules dynamically from database
  const loadDetectedMules = async () => {
    setIsLoadingMules(true);
    try {
      const res = await fetchDetectedMules();
      setDetectedMules(res.mules || []);
    } catch (e) {
      console.error('Failed to load detected mules', e);
    } finally {
      setIsLoadingMules(false);
    }
  };

  useEffect(() => {
    loadDetectedMules();
  }, []);

  // Sync state if initialAccount prop changes from parent
  useEffect(() => {
    if (initialAccount) {
      setPayeeId(initialAccount);
      if (initialAmount) setAmount(initialAmount);
      handleScan(initialAccount, initialAmount);
    }
  }, [initialAccount, initialAmount]);

  const handleScan = async (overrideAccount?: string, overrideAmount?: number) => {
    const acc = (overrideAccount || payeeId || '').trim();
    const amt = overrideAmount !== undefined ? overrideAmount : amount;
    if (!acc) return;

    setIsLoading(true);
    setError(null);
    try {
      const data = await runScan(acc, amt, 'ACC-VIC-01', remark);
      setScanResult(data);
      if (data.verdict === 'DELAY' || data.verdict === 'HOLD') {
        onTriggerWarning(data);
      }
    } catch (err: any) {
      setError(err.message || 'Scan failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyLienHold = async (accId: string) => {
    setIsHolding(true);
    try {
      await requestLienHold(accId);
      await loadDetectedMules();
      if (scanResult && scanResult.account_id === accId) {
        setScanResult({
          ...scanResult,
          plain_language_reasons: [
            'Administrative lien hold placed by compliance operations.',
            ...scanResult.plain_language_reasons
          ]
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsHolding(false);
    }
  };

  // Check if current payee is held
  const currentMuleInfo = detectedMules.find(m => m.id === payeeId);
  const isCurrentPayeeHeld = currentMuleInfo?.is_held;

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      {/* Page Header */}
      <div>
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl font-black tracking-tight text-white">Customer Pre-Payment Scan</h2>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/80 text-rose-300 border border-rose-800">
            Real-Time Inference
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
            Simulated Data
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Simulates the real-time payee check screen embedded within a banking mobile app or payment switch before funds leave the bank.
        </p>
      </div>

      {/* Two Column Grid: Payment Form (Left) & Real-Time Risk Analysis (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Mock Banking Payment Form */}
        <div className="lg:col-span-5 bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="font-bold text-sm text-white flex items-center space-x-2">
              <Send className="w-4 h-4 text-cyan-400" />
              <span>Make Electronic Transfer</span>
            </span>
            <span className="text-[11px] font-mono text-slate-400">IMPS / UPI Rail</span>
          </div>

          {/* Quick Payee Selector: Live Detected Mules vs Legitimate Accounts */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-[10px] font-bold">
                <button
                  type="button"
                  onClick={() => setActiveTabFilter('mules')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    activeTabFilter === 'mules'
                      ? 'bg-[#E5334F] text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Detected Mules ({detectedMules.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTabFilter('legit')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    activeTabFilter === 'legit'
                      ? 'bg-emerald-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Verified Merchants
                </button>
              </div>

              <button
                type="button"
                onClick={loadDetectedMules}
                disabled={isLoadingMules}
                className="text-slate-400 hover:text-white p-1 rounded-lg transition"
                title="Refresh risky accounts from database"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingMules ? 'animate-spin text-cyan-400' : ''}`} />
              </button>
            </div>

            {/* List of Risky Accounts / Mules */}
            <div className="grid grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
              {activeTabFilter === 'mules' ? (
                detectedMules.slice(0, 10).map((m) => {
                  const isSelected = payeeId === m.id;
                  const isHeld = m.is_held;
                  const suggestedAmount = m.layer === 1 ? 95000 : (m.layer === 2 ? 82700 : 120000);

                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => {
                        setPayeeId(m.id);
                        setAmount(suggestedAmount);
                        handleScan(m.id, suggestedAmount);
                      }}
                      className={`p-2 rounded-xl text-left border transition text-xs relative ${
                        isSelected
                          ? 'bg-rose-950/60 border-[#E5334F] text-white shadow-md shadow-rose-950/50 ring-1 ring-rose-500'
                          : isHeld
                          ? 'bg-rose-950/20 border-rose-900/60 text-slate-300 hover:border-rose-700'
                          : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] font-bold text-white">{m.id}</span>
                        {isHeld ? (
                          <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-rose-900 text-white font-bold flex items-center space-x-0.5">
                            <Lock className="w-2 h-2" />
                            <span>HELD</span>
                          </span>
                        ) : (
                          <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                            {m.chain_id || 'CH-AUTO'}
                          </span>
                        )}
                      </div>
                      <div className="font-semibold text-[11px] truncate mt-0.5" title={m.pseudonymous_label}>
                        {m.pseudonymous_label}
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[9px] font-mono">
                        <span className="text-slate-400">Layer {m.layer}</span>
                        <span className="text-[#E5334F] font-bold">{(m.mule_score * 100).toFixed(0)}% Risk</span>
                      </div>
                    </button>
                  );
                })
              ) : (
                legitAccounts.map((legit) => {
                  const isSelected = payeeId === legit.id;
                  return (
                    <button
                      key={legit.id}
                      type="button"
                      onClick={() => {
                        setPayeeId(legit.id);
                        setAmount(legit.amount);
                        handleScan(legit.id, legit.amount);
                      }}
                      className={`p-2 rounded-xl text-left border transition text-xs ${
                        isSelected
                          ? 'bg-emerald-950/50 border-emerald-500 text-white shadow-md'
                          : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] font-bold text-white">{legit.id}</span>
                        <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                          CLEAN
                        </span>
                      </div>
                      <div className="font-semibold text-[11px] truncate mt-0.5">{legit.label}</div>
                      <div className="text-[9px] text-slate-400 font-mono mt-1">₹{legit.amount.toLocaleString('en-IN')}</div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-4 pt-1">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-300">Beneficiary Account ID / VPA</label>
                {isCurrentPayeeHeld && (
                  <span className="text-[10px] font-mono font-bold text-[#E5334F] flex items-center space-x-1">
                    <Lock className="w-2.5 h-2.5" />
                    <span>Lien Hold Active</span>
                  </span>
                )}
              </div>
              <input
                type="text"
                value={payeeId}
                onChange={(e) => setPayeeId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs text-white focus:outline-none focus:border-cyan-500"
                placeholder="e.g. ACC02228"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Transfer Amount (₹ INR)</label>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-slate-500 font-mono">₹</span>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="w-full pl-8 pr-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs text-white focus:outline-none focus:border-cyan-500"
                  placeholder="50000"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Payment Remark / Note</label>
              <input
                type="text"
                value={remark}
                onChange={(e) => setRemark(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-cyan-500"
                placeholder="Invoice reference or contractor payment"
              />
            </div>

            <button
              onClick={() => handleScan()}
              disabled={isLoading}
              className="w-full py-3 rounded-xl font-bold text-xs bg-[#E5334F] hover:bg-rose-600 text-white shadow-lg shadow-rose-950 transition flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Evaluating Live ML Model...</span>
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  <span>Pay & Scan Pre-Payment Risk</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Live Decision & Forensic Explainability Panel */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {scanResult && (
            <div className="bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 animate-in fade-in">
              {/* Top Banner: Score, Verdict & One-Click Actions */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <RiskGauge score={scanResult.probability} verdict={scanResult.verdict} size={190} />

                <div className="flex-1 space-y-2 text-center sm:text-left">
                  <div className="flex items-center justify-center sm:justify-start space-x-2">
                    <span className="font-bold text-lg text-white font-mono">{scanResult.account_id}</span>
                    <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-800 text-cyan-300 border border-slate-700">
                      {scanResult.bank_id}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 font-medium">
                    {scanResult.account_label}
                  </div>
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1 font-mono text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700">
                      IsoForest Outlier: {(scanResult.iso_anomaly_score * 100).toFixed(0)}%
                    </span>
                    {scanResult.honeypot_proximity_boost > 0 && (
                      <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800">
                        Honeypot Proximity: +{(scanResult.honeypot_proximity_boost * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {/* Immediate Action Buttons: Track Money DNA & Request Hold */}
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-2">
                    <button
                      onClick={() => onNavigateToMoneyDNA?.(scanResult.account_id)}
                      className="px-3 py-1.5 rounded-xl text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-md flex items-center space-x-1.5 transition"
                    >
                      <GitBranch className="w-3.5 h-3.5" />
                      <span>Track Money DNA Flow</span>
                      <ArrowRight className="w-3 h-3 ml-0.5" />
                    </button>

                    <button
                      onClick={() => handleApplyLienHold(scanResult.account_id)}
                      disabled={isHolding || isCurrentPayeeHeld}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
                        isCurrentPayeeHeld
                          ? 'bg-rose-950 text-[#E5334F] border border-rose-800 cursor-default'
                          : 'bg-[#E5334F] hover:bg-rose-600 text-white shadow-md'
                      }`}
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>{isCurrentPayeeHeld ? 'Lien Active' : 'Request Hold'}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Counterfactual Insight Panel */}
              {scanResult.counterfactual && (
                <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-xs text-cyan-200 flex items-start space-x-3">
                  <Clock className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-bold uppercase tracking-wide text-[10px] text-cyan-300 block">
                      Counterfactual Search Condition:
                    </span>
                    <p className="mt-1 text-slate-200">{scanResult.counterfactual}</p>
                  </div>
                </div>
              )}

              {/* Horizontal SHAP Reason Code Contributions */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span>Top Reason Contributions (TreeSHAP)</span>
                  <span className="text-[10px] font-mono lowercase text-slate-500">point-in-time</span>
                </div>
                <div className="space-y-2">
                  {scanResult.top_reasons.map((r, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs text-slate-300">
                        <span className="truncate pr-2">{r.label}</span>
                        <span className="font-mono text-rose-400 font-bold shrink-0">
                          {r.contribution > 0 ? `+${r.contribution.toFixed(3)}` : r.contribution.toFixed(3)}
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-amber-500 to-[#E5334F] rounded-full transition-all duration-700"
                          style={{ width: `${Math.min(100, Math.max(10, r.contribution * 200))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Next Hop Destinations */}
              {scanResult.next_hops && scanResult.next_hops.length > 0 && (
                <div className="space-y-2.5 pt-2 border-t border-slate-800">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                    <GitBranch className="w-3.5 h-3.5 text-amber-400" />
                    <span>Predicted Downstream Next-Hops (Top 3):</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {scanResult.next_hops.map((hop, i) => (
                      <div key={i} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-1">
                        <div className="flex items-center justify-between font-mono font-bold text-white text-[11px]">
                          <span className="truncate">{hop.account_id}</span>
                          <span className="text-amber-400">{(hop.probability * 100).toFixed(0)}%</span>
                        </div>
                        <div className="text-[10px] text-slate-400 truncate">{hop.label}</div>
                        <div className="text-[9px] text-slate-500 truncate">{hop.reason}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
