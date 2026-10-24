import React from 'react';
import { Shield, RefreshCw, AlertTriangle, Lock, Award, Eye } from 'lucide-react';
import { LiveStats } from '../types';

interface TopBarProps {
  stats: LiveStats | null;
  onReset: () => void;
  isResetting: boolean;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  stats,
  onReset,
  isResetting,
  theme,
  onToggleTheme
}) => {
  const formatInr = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <header className="sticky top-0 z-50 bg-[#0B1220]/95 backdrop-blur-md border-b border-slate-800 text-slate-100 px-4 lg:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 shadow-2xl">
      {/* Brand & Simulated Badge */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#E5334F] to-amber-500 flex items-center justify-center font-black text-xl text-white shadow-lg shadow-rose-950/40">
          B
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-base lg:text-lg tracking-tight text-white flex items-center space-x-1.5">
              <span>Bloodline</span>
              <span className="text-[#E5334F]">2.0</span>
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-emerald-950/80 text-emerald-400 border border-emerald-700/50 flex items-center space-x-1 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span>Simulated data</span>
            </span>
            <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800/80 text-cyan-400 border border-slate-700">
              Hold: {stats?.current_threshold_hold?.toFixed(2) || '0.70'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 flex items-center space-x-2">
            <span>Bank-Grade Mule Defense</span>
            <span>•</span>
            <span className="text-amber-400/90 font-medium">RBI Regulatory Enforcement</span>
          </p>
        </div>
      </div>

      {/* Live Impact Counters (Sticky Topbar) */}
      <div className="flex items-center space-x-2 sm:space-x-4 overflow-x-auto py-1 scrollbar-none">
        {/* Prevented */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40">
          <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
          <div className="text-left">
            <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-400/80">Prevented</div>
            <div className="font-mono text-xs sm:text-sm font-extrabold text-emerald-300">
              {formatInr(stats?.prevented_inr)}
            </div>
          </div>
        </div>

        {/* At Risk */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-amber-950/40 border border-amber-800/40">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <div className="text-left">
            <div className="text-[10px] uppercase font-bold tracking-wider text-amber-400/80">At Risk</div>
            <div className="font-mono text-xs sm:text-sm font-extrabold text-amber-300">
              {formatInr(stats?.at_risk_inr)}
            </div>
          </div>
        </div>

        {/* Lost */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-rose-950/40 border border-rose-800/40">
          <Lock className="w-4 h-4 text-[#E5334F] shrink-0" />
          <div className="text-left">
            <div className="text-[10px] uppercase font-bold tracking-wider text-rose-400/80">Lost (Exited)</div>
            <div className="font-mono text-xs sm:text-sm font-extrabold text-rose-300">
              {formatInr(stats?.lost_inr)}
            </div>
          </div>
        </div>

        {/* Exposure Avoided (RBI Rule) */}
        <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-cyan-950/40 border border-cyan-800/40">
          <Award className="w-4 h-4 text-cyan-400 shrink-0" />
          <div className="text-left">
            <div className="text-[10px] uppercase font-bold tracking-wider text-cyan-400/80">RBI Exposure Avoided</div>
            <div className="font-mono text-xs sm:text-sm font-extrabold text-cyan-300">
              {formatInr(stats?.exposure_avoided_inr)}
            </div>
          </div>
        </div>
      </div>

      {/* Actions: Demo Reset, Theme, Docs */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onReset}
          disabled={isResetting}
          title="Reset demo data to deterministic baseline"
          className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin text-[#E5334F]' : ''}`} />
          <span className="hidden sm:inline">Reset Demo</span>
        </button>

        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition flex items-center space-x-1"
        >
          <span>API Docs</span>
        </a>

        <button
          onClick={onToggleTheme}
          aria-label="Toggle theme"
          className="p-1.5 rounded-lg text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
};
