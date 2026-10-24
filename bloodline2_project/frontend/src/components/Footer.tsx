import React from 'react';
import { ExternalLink, ShieldCheck, FileText } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#0B1220] border-t border-slate-800/80 px-6 py-6 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left: Statutory Disclaimer */}
        <div className="flex flex-col space-y-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start space-x-2 text-slate-300 font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Bloodline 2.0 Decision-Support System</span>
            <span className="text-slate-600">•</span>
            <span className="text-rose-400/90 font-medium">Demonstration only, not legal advice</span>
          </div>
          <p className="text-slate-500 text-[11px]">
            All account numbers, ledger entries, and transaction topologies are synthetic.
            System provides advisory indicators; any action with legal effect requires explicit human approval.
          </p>
        </div>

        {/* Right: Regulatory Reference Links (from config/rules.yaml) */}
        <div className="flex flex-wrap items-center justify-center gap-3 text-[11px]">
          <a
            href="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10497"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1 text-slate-400 hover:text-cyan-400 transition"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>RBI Fraud Master Directions (2016)</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
          <span className="text-slate-700 hidden sm:inline">•</span>
          <a
            href="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11040"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1 text-slate-400 hover:text-cyan-400 transition"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Customer Liability Circular (2018)</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
          <span className="text-slate-700 hidden sm:inline">•</span>
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1 text-slate-400 hover:text-amber-400 transition"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>I4C National Helpline 1930</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
        </div>
      </div>
    </footer>
  );
};
