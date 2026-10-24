import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, Lock, CheckCircle2, RefreshCw, FileText, ExternalLink, ArrowRight } from 'lucide-react';
import { fetchInvoices, checkVendor, submitDecision, requestLienHold } from '../api';
import { InvoiceItem } from '../types';

export const BusinessShieldPage: React.FC = () => {
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceItem | null>(null);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadInvoices = async () => {
    setIsLoading(true);
    try {
      const data = await fetchInvoices();
      setInvoices(data);
      if (data.length > 0) {
        // Auto-select the planted attack invoice for clear demo
        const attacked = data.find((inv) => inv.is_attacked === 1) || data[0];
        handleSelectInvoice(attacked);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectInvoice = async (inv: InvoiceItem) => {
    setSelectedInvoice(inv);
    setActionMessage(null);
    try {
      const res = await checkVendor(inv.vendor_id, inv.account_id, inv.amount);
      setVerificationResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAction = async (action: 'HOLD' | 'RELEASE') => {
    if (!selectedInvoice) return;
    try {
      if (action === 'HOLD') {
        await requestLienHold(selectedInvoice.account_id);
        await submitDecision(selectedInvoice.account_id, 'HELD', selectedInvoice.invoice_id, 'Placed admin hold on tampered vendor bank details');
        setActionMessage(`Lien request successfully placed on account ${selectedInvoice.account_id}. Payment frozen pending callback verification.`);
      } else {
        await submitDecision(selectedInvoice.account_id, 'PROCEEDED', selectedInvoice.invoice_id, 'Compliance officer authorized vendor disbursement');
        setActionMessage(`Payout released for invoice ${selectedInvoice.invoice_id}.`);
      }
      loadInvoices();
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, []);

  const formatInr = (val: number) => `₹${val.toLocaleString('en-IN')}`;

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl font-black tracking-tight text-white">Business Shield — Invoice Defense</h2>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/80 text-amber-300 border border-amber-800">
            BEC & Tamper Detection
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Automated protection against Business Email Compromise (BEC) and unauthorized vendor bank account divergence attacks.
        </p>
      </div>

      {actionMessage && (
        <div className="p-4 rounded-xl bg-cyan-950/40 border border-cyan-800 text-cyan-200 text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Main Grid: Invoices Table (Left) & Forensic Verification Dossier (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Invoice Queue */}
        <div className="lg:col-span-7 bg-[#0D1527] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="font-bold text-sm text-white flex items-center space-x-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Pending Procurement Invoices</span>
            </span>
            <button
              onClick={loadInvoices}
              className="text-xs text-slate-400 hover:text-cyan-300 flex items-center space-x-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase font-bold text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Invoice</th>
                  <th className="py-2.5 px-3">Vendor</th>
                  <th className="py-2.5 px-3">Amount</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Alert</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {invoices.map((inv) => {
                  const isSelected = selectedInvoice?.invoice_id === inv.invoice_id;
                  const isAttacked = inv.is_attacked === 1 || inv.flag_bank_detail_change === 1;

                  return (
                    <tr
                      key={inv.invoice_id}
                      onClick={() => handleSelectInvoice(inv)}
                      className={`cursor-pointer transition ${
                        isSelected
                          ? 'bg-rose-950/30 text-white'
                          : 'hover:bg-slate-900/60 text-slate-300'
                      }`}
                    >
                      <td className="py-3 px-3 font-bold text-cyan-400">{inv.invoice_id}</td>
                      <td className="py-3 px-3 font-sans truncate max-w-[140px]">{inv.vendor_name}</td>
                      <td className="py-3 px-3">{formatInr(inv.amount)}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            inv.status === 'HELD_ALERT'
                              ? 'bg-rose-950 text-[#E5334F] border border-rose-800'
                              : inv.status === 'PAID'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-sans">
                        {isAttacked ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#E5334F] text-white flex items-center space-x-1 w-max">
                            <AlertTriangle className="w-2.5 h-2.5" />
                            <span>Tampered</span>
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Normal</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Verification & Tampering Analysis Dossier */}
        <div className="lg:col-span-5 bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="font-bold text-sm text-white">Vendor Route Verification</span>
            <span className="text-xs font-mono text-cyan-400">{selectedInvoice?.invoice_id}</span>
          </div>

          {selectedInvoice && verificationResult ? (
            <div className="space-y-4">
              {/* Divergence Banner */}
              {verificationResult.is_bank_detail_diverted ? (
                <div className="p-4 rounded-xl bg-rose-950/60 border-2 border-[#E5334F] text-white space-y-2">
                  <div className="flex items-center space-x-2 font-bold text-xs uppercase tracking-wide text-rose-300">
                    <AlertTriangle className="w-4 h-4 text-[#E5334F]" />
                    <span>Unauthorized Bank Account Divergence Detected</span>
                  </div>
                  <p className="text-xs text-rose-100">
                    {verificationResult.evidence?.[0] || 'Destination account differs from verified procurement records.'}
                  </p>
                  <div className="text-[11px] font-mono text-rose-300 pt-1">
                    Destination Mule Risk: {(verificationResult.account_mule_score * 100).toFixed(1)}%
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800 text-emerald-300 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Beneficiary details match historical verified vendor records. Clean route.</span>
                </div>
              )}

              {/* Vendor Route Comparison */}
              <div className="space-y-2.5 font-mono text-xs bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                <div className="flex justify-between">
                  <span className="text-slate-400">Vendor ID:</span>
                  <span className="text-white font-bold">{selectedInvoice.vendor_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Registered Account:</span>
                  <span className="text-emerald-400">{verificationResult.registered_original_account}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Proposed Destination:</span>
                  <span className={verificationResult.is_bank_detail_diverted ? 'text-[#E5334F] font-bold' : 'text-slate-200'}>
                    {verificationResult.proposed_destination_account}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Invoice Amount:</span>
                  <span className="text-white">{formatInr(selectedInvoice.amount)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-2 flex items-center space-x-3">
                <button
                  onClick={() => handleAction('HOLD')}
                  className="flex-1 py-3 rounded-xl text-xs font-bold bg-[#E5334F] hover:bg-rose-600 text-white shadow-lg shadow-rose-950 transition flex items-center justify-center space-x-1.5"
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span>Place Administrative Hold / Lien</span>
                </button>

                <button
                  onClick={() => handleAction('RELEASE')}
                  className="px-4 py-3 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                >
                  Authorize Release
                </button>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic py-8 text-center">Select an invoice to inspect risk profile.</div>
          )}
        </div>
      </div>
    </div>
  );
};
