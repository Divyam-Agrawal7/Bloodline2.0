import React from 'react';
import { Shield, ArrowRight, Zap, Scale, GitBranch, Cpu, Lock, CheckCircle2 } from 'lucide-react';
import { LiveStats } from '../types';

interface LandingPageProps {
  stats: LiveStats | null;
  onNavigate: (tab: any) => void;
  onLaunchDemoStory: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  stats,
  onNavigate,
  onLaunchDemoStory
}) => {
  const formatInr = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <div className="space-y-12 py-4">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-[#0F172A] to-[#0B1220] border border-slate-800 p-8 md:p-12 shadow-2xl">
        <div className="absolute -top-32 -right-32 w-96 h-96 bg-[#E5334F]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-3xl space-y-6 relative z-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/60 border border-rose-800/60 text-rose-300">
            <span className="w-2 h-2 rounded-full bg-[#E5334F] animate-pulse" />
            <span>Next-Generation Mule Network & Fraud Interception</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white leading-tight">
            Intercept stolen money <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 via-amber-300 to-cyan-400">
              before it reaches the cash-out node.
            </span>
          </h1>

          <p className="text-slate-300 text-sm md:text-base leading-relaxed">
            Banks and payment apps embed Bloodline 2.0 through real-time APIs. It scores payees and transactions under 20ms,
            traces multi-bank Money DNA flows, predicts downstream destination hops, enforces statutory RBI Case Clocks, and measures rupees saved.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={onLaunchDemoStory}
              className="px-6 py-3.5 rounded-xl text-sm font-bold bg-[#E5334F] hover:bg-rose-600 text-white shadow-xl shadow-rose-950/60 transition flex items-center space-x-2"
            >
              <span>Launch 5-Minute Demo</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('scan')}
              className="px-6 py-3.5 rounded-xl text-sm font-semibold bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center space-x-2"
            >
              <Zap className="w-4 h-4 text-cyan-400" />
              <span>Simulate Payee Scan</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3 Key Impact Counters pulled live from /stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-[#0D1527] border border-slate-800 shadow-xl relative overflow-hidden group hover:border-emerald-500/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Rupees Prevented</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-950 flex items-center justify-center text-emerald-400 border border-emerald-800/50">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-white mt-3">
            {formatInr(stats?.prevented_inr)}
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Stolen funds successfully held or cancelled during customer warning windows.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-[#0D1527] border border-slate-800 shadow-xl relative overflow-hidden group hover:border-cyan-500/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">RBI Exposure Avoided</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-950 flex items-center justify-center text-cyan-400 border border-cyan-800/50">
              <Scale className="w-4 h-4" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-white mt-3">
            {formatInr(stats?.exposure_avoided_inr)}
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Bank compensation liability avoided under RBI Customer Protection circulars.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-[#0D1527] border border-slate-800 shadow-xl relative overflow-hidden group hover:border-amber-500/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Active Watch Volume</span>
            <div className="w-8 h-8 rounded-lg bg-amber-950 flex items-center justify-center text-amber-400 border border-amber-800/50">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-white mt-3">
            {formatInr(stats?.at_risk_inr)}
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Monitored in 24h dynamic watch windows across participating banks.
          </p>
        </div>
      </div>

      {/* Product Pillar Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <div className="p-6 rounded-2xl bg-[#0D1527] border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-[#E5334F]">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-base">Real ML Model & TreeSHAP</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Cost-sensitive XGBoost trained on point-in-time features with early PR-AUC stopping. Never hardcodes scores;
            every verdict produces exact SHAP reason contributions and perturbation counterfactuals.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-[#0D1527] border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <GitBranch className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-base">Money DNA Flow Replay</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Haircut flow tracer tracking multi-layer dispersal DAGs. Interactive time slider lets investigators replay
            syndicate formation minute-by-minute and lock downstream next-hop exits.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-[#0D1527] border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Scale className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-base">RBI Statutory Case Clock</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            State machine enforcing 21-day show-cause representation and 14-day mandatory FMR filing clocks.
            LLM auto-drafts forensic dossiers and statutory notices with human approval gates.
          </p>
        </div>
      </div>
    </div>
  );
};
