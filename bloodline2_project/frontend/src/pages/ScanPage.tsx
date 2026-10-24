import React, { useState, useEffect } from 'react';
import { Shield, Send, AlertTriangle, CheckCircle, Clock, GitBranch, ArrowRight, Info, UserCheck, RefreshCw } from 'lucide-react';
import { runScan } from '../api';
import { ScanResponse } from '../types';
import { RiskGauge } from '../components/RiskGauge';

interface ScanPageProps {
  onTriggerWarning: (data: ScanResponse) => void;
  initialAccount?: string;
  initialAmount?: number;
}

export const ScanPage: React.FC<ScanPageProps> = ({
  onTriggerWarning,
  initialAccount = 'ACC02228',
  initialAmount = 95000.0
}) => {
  const [payeeId, setPayeeId] = useState(initialAccount);
  const [amount, setAmount] = useState<number>(initialAmount);
  const [remark, setRemark] = useState('Contractor urgent advance');
  const [isLoading, setIsLoading] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const testAccounts = [
    { id: 'ACC02228', label: 'Neha Bose (Mule L1 Hub - CH03)', amount: 95000, risk: 'High Risk' },
    { id: 'ACC02233', label: 'Nisha Rao (Layer 2 Dispersal)', amount: 82700, risk: 'High Risk' },
    { id: 'ACC02041', label: 'Reddy Stores (Merchant Shopkeeper)', amount: 1500, risk: 'Legitimate' },
    { id: 'ACC02212', label: 'Nisha Nair (Payroll / Recruiter)', amount: 75000, risk: 'Legitimate' }
  ];

  const handleScan = async (overrideAccount?: string, overrideAmount?: number) => {
    const acc = overrideAccount || payeeId;
    const amt = overrideAmount !== undefined ? overrideAmount : amount;
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

  useEffect(() => {
    // Initial scan on load
    handleScan(initialAccount, initialAmount);
  }, []);

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      {/* Page Header */}
      <div>
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl font-black tracking-tight text-white">Customer Pre-Payment Scan</h2>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/80 text-rose-300 border border-rose-800">
            Real-Time Inference
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Simulates the payee check screen embedded within a banking mobile app or payment portal before fund release.
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

          {/* Planted Scenario Quick Selector */}
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Planted Test Scenarios (1-Click):
            </label>
            <div className="grid grid-cols-2 gap-2">
              {testAccounts.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => {
                    setPayeeId(t.id);
                    setAmount(t.amount);
                    handleScan(t.id, t.amount);
                  }}
                  className={`p-2 rounded-xl text-left border transition text-xs ${
                    payeeId === t.id
                      ? 'bg-rose-950/40 border-[#E5334F] text-white shadow-md shadow-rose-950/50'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold truncate">{t.label}</div>
                  <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400 font-mono">
                    <span>₹{t.amount.toLocaleString('en-IN')}</span>
                    <span className={t.risk === 'High Risk' ? 'text-[#E5334F]' : 'text-emerald-400'}>
                      {t.risk}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-4 pt-1">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Beneficiary Account ID / VPA</label>
              <input
                type="text"
                value={payeeId}
                onChange={(e) => setPayeeId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs text-white focus:outline-none focus:border-cyan-500"
                placeholder="e.g. ACC-MULE-C1-L1-1"
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
                placeholder="Invoice reference or personal transfer"
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

        {/* Right Column: Live Decision & Explainability Panel */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {scanResult && (
            <div className="bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              {/* Top Banner: Score & Verdict */}
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
