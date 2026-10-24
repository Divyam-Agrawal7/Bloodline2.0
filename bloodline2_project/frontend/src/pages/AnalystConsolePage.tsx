import React, { useState, useEffect, useMemo } from 'react';
import {
  Share2, Play, Pause, RotateCcw, Lock, ArrowRight, ShieldAlert,
  GitBranch, Send, Cpu, CheckCircle2, AlertOctagon, ExternalLink,
  Search, Filter, RefreshCw, Zap, ShieldCheck, Database, ListFilter
} from 'lucide-react';
import { fetchLineage, requestLienHold, executeHandoff, fetchDetectedMules, fetchLiveTransactions } from '../api';
import { LineageResponse, MuleAccountItem, LiveTransactionItem } from '../types';
import { MoneyDNASankey } from '../components/MoneyDNASankey';

interface AnalystConsolePageProps {
  onRefreshStats: () => void;
  initialAccount?: string;
  initialTxnId?: string;
  initialChainId?: string;
}

export const AnalystConsolePage: React.FC<AnalystConsolePageProps> = ({
  onRefreshStats,
  initialAccount,
  initialTxnId,
  initialChainId
}) => {
  // Navigation sub-tab
  const [activeTab, setActiveTab] = useState<'flow' | 'transactions' | 'mules'>('flow');

  // Selected syndicate chain
  const [selectedChainId, setSelectedChainId] = useState<string>(initialChainId || 'CH03');

  // Lineage data
  const [lineageData, setLineageData] = useState<LineageResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(initialAccount || 'ACC02228');
  const [timelineIndex, setTimelineIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [handoffSuccess, setHandoffSuccess] = useState<any | null>(null);
  const [isHolding, setIsHolding] = useState<boolean>(false);

  // Live Transactions Panel data
  const [transactions, setTransactions] = useState<LiveTransactionItem[]>([]);
  const [txnSearch, setTxnSearch] = useState<string>('');
  const [txnFilter, setTxnFilter] = useState<'all' | 'mule' | 'held'>('all');
  const [isLoadingTxns, setIsLoadingTxns] = useState<boolean>(false);

  // Detected Mules Panel data
  const [mules, setMules] = useState<MuleAccountItem[]>([]);
  const [muleSearch, setMuleSearch] = useState<string>('');
  const [muleFilterRole, setMuleFilterRole] = useState<'all' | 'L1' | 'L2' | 'held'>('all');
  const [isLoadingMules, setIsLoadingMules] = useState<boolean>(false);

  // Load Lineage Data
  const loadLineage = async (chainId?: string) => {
    const chain = chainId || selectedChainId || 'CH03';
    try {
      const data = await fetchLineage(chain);
      setLineageData(data);
      if (data.active_chain) {
        setSelectedChainId(data.active_chain);
      }
      if (data.timeline && data.timeline.length > 0) {
        setTimelineIndex(data.timeline.length - 1);
      }
      if (data.nodes && data.nodes.length > 0) {
        const exists = data.nodes.some((n) => n.account_id === selectedNodeId);
        if (!exists) {
          const preferred = data.nodes.find((n) => n.layer === 1) || data.nodes[0];
          setSelectedNodeId(preferred.account_id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Load Transactions Feed
  const loadTransactions = async () => {
    setIsLoadingTxns(true);
    try {
      const res = await fetchLiveTransactions(150);
      setTransactions(res.transactions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingTxns(false);
    }
  };

  // Load Detected Mules
  const loadMules = async () => {
    setIsLoadingMules(true);
    try {
      const res = await fetchDetectedMules();
      setMules(res.mules || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingMules(false);
    }
  };

  useEffect(() => {
    const startRef = initialTxnId || initialChainId || initialAccount || 'CH03';
    if (initialAccount) setSelectedNodeId(initialAccount);
    if (initialChainId) setSelectedChainId(initialChainId);
    loadLineage(startRef);
    loadTransactions();
    loadMules();
  }, [initialTxnId, initialChainId, initialAccount]);

  // Time replay animation loop
  useEffect(() => {
    if (!isPlaying || !lineageData?.timeline) return;

    const interval = setInterval(() => {
      setTimelineIndex((prev) => {
        if (prev >= lineageData.timeline.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 700);

    return () => clearInterval(interval);
  }, [isPlaying, lineageData]);

  const handleRequestHold = async (accId: string) => {
    setIsHolding(true);
    try {
      await requestLienHold(accId);
      await Promise.all([loadLineage(selectedChainId), loadMules(), loadTransactions()]);
      onRefreshStats();
    } catch (e) {
      console.error(e);
    } finally {
      setIsHolding(false);
    }
  };

  const handleTrackMoney = async (t: LiveTransactionItem) => {
    await loadLineage(t.id);
    setSelectedNodeId(t.receiver);
    setActiveTab('flow');
  };

  const handleInspectTransaction = async (t: LiveTransactionItem) => {
    const targetChain = t.chain_id || 'CH03';
    if (targetChain !== selectedChainId) {
      setSelectedChainId(targetChain);
      await loadLineage(targetChain);
    }
    setSelectedNodeId(t.receiver);
    setActiveTab('flow');
  };

  const handleInspectMule = async (m: MuleAccountItem) => {
    const targetChain = m.chain_id || 'CH03';
    if (targetChain !== selectedChainId) {
      setSelectedChainId(targetChain);
      await loadLineage(targetChain);
    }
    setSelectedNodeId(m.id);
    setActiveTab('flow');
  };

  const handleCrossBankHandoff = async () => {
    if (!selectedNodeId) return;
    try {
      const res = await executeHandoff(
        'CASE-2026-001',
        'TXN-CROSS-001',
        selectedNodeId,
        450000.0,
        ['RAPID_PASS_THROUGH', 'SHARED_HARDWARE_CLUSTER']
      );
      setHandoffSuccess(res);
      setTimeout(() => setHandoffSuccess(null), 8000);
    } catch (e) {
      console.error(e);
    }
  };

  const formatInr = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${Math.round(val).toLocaleString('en-IN')}`;
  };

  const selectedNode = lineageData?.nodes.find((n) => n.account_id === selectedNodeId);
  const currentTxn = lineageData?.timeline[timelineIndex];

  // Filtered Transactions
  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      const matchSearch =
        !txnSearch ||
        t.id.toLowerCase().includes(txnSearch.toLowerCase()) ||
        t.sender.toLowerCase().includes(txnSearch.toLowerCase()) ||
        (t.sender_name && t.sender_name.toLowerCase().includes(txnSearch.toLowerCase())) ||
        t.receiver.toLowerCase().includes(txnSearch.toLowerCase()) ||
        (t.receiver_name && t.receiver_name.toLowerCase().includes(txnSearch.toLowerCase()));

      if (!matchSearch) return false;
      if (txnFilter === 'mule') return t.is_mule_flow === 1;
      if (txnFilter === 'held') return t.status.includes('HELD');
      return true;
    });
  }, [transactions, txnSearch, txnFilter]);

  // Filtered Mules
  const filteredMules = useMemo(() => {
    return mules.filter((m) => {
      const matchSearch =
        !muleSearch ||
        m.id.toLowerCase().includes(muleSearch.toLowerCase()) ||
        (m.pseudonymous_label && m.pseudonymous_label.toLowerCase().includes(muleSearch.toLowerCase())) ||
        (m.chain_id && m.chain_id.toLowerCase().includes(muleSearch.toLowerCase()));

      if (!matchSearch) return false;
      if (muleFilterRole === 'L1') return m.layer === 1 || m.role.includes('L1') || m.role.includes('AGGREGATOR');
      if (muleFilterRole === 'L2') return m.layer === 2 || m.role.includes('L2') || m.role.includes('DISPERSAL');
      if (muleFilterRole === 'held') return m.is_held;
      return true;
    });
  }, [mules, muleSearch, muleFilterRole]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-2">
      {/* Top Header & Sub-Navigation */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-2xl font-black tracking-tight text-white">Analyst Investigation Console</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
              Money DNA & Syndicate Tracker
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Replay transaction flows with directional arrows, inspect live ledger activity, and manage administrative lien holds.
          </p>
        </div>

        {/* Global Action: Cross-Bank Trace Handoff */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCrossBankHandoff}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-950 transition flex items-center space-x-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Transmit Cross-Bank Handoff</span>
          </button>
        </div>
      </div>

      {handoffSuccess && (
        <div className="p-4 rounded-xl bg-cyan-950/80 border border-cyan-500 text-xs text-cyan-200 space-y-1 animate-in fade-in">
          <div className="flex items-center space-x-2 font-bold text-white">
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            <span>Privacy-Preserving Cross-Bank Handoff Transmitted</span>
          </div>
          <p className="font-mono text-[11px] text-cyan-300">
            Token: {handoffSuccess.handoff_token} • Destination Bank: {handoffSuccess.destination_bank} • Raw Ledger Shared: False (Zero-Knowledge Hash)
          </p>
        </div>
      )}

      {/* Sub-Tabs Navigation */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('flow')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 ${
            activeTab === 'flow'
              ? 'bg-[#E5334F] text-white shadow-lg shadow-rose-950'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>Money DNA Flow (Directional Arrows & Replay)</span>
        </button>

        <button
          onClick={() => setActiveTab('transactions')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 ${
            activeTab === 'transactions'
              ? 'bg-[#E5334F] text-white shadow-lg shadow-rose-950'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Live Transactions Feed ({transactions.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('mules')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 ${
            activeTab === 'mules'
              ? 'bg-[#E5334F] text-white shadow-lg shadow-rose-950'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>Detected Mules Directory ({mules.length})</span>
        </button>
      </div>

      {/* TAB 1: Money DNA Flow with Directional Arrows */}
      {activeTab === 'flow' && (
        <div className="space-y-6 animate-in fade-in">
          {/* Flow Diagram with Animated Directional Arrows */}
          <MoneyDNASankey
            data={lineageData}
            onSelectNode={(id) => setSelectedNodeId(id)}
            onRequestHold={handleRequestHold}
            selectedAccountId={selectedNodeId}
            selectedChainId={selectedChainId}
            onSelectChain={(chain) => {
              setSelectedChainId(chain);
              loadLineage(chain);
            }}
          />

          {/* Time Scrubber Replay Bar */}
          <div className="bg-[#0D1527] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="w-9 h-9 rounded-xl bg-[#E5334F] hover:bg-rose-600 text-white flex items-center justify-center shadow-lg transition"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                </button>
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setTimelineIndex(0);
                  }}
                  className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  title="Rewind to beginning"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <div>
                  <span className="font-bold text-xs text-white uppercase tracking-wider block">
                    Time Replay Engine (Step {timelineIndex + 1} of {lineageData?.timeline.length || 0})
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {currentTxn ? `${currentTxn.timestamp.slice(0, 19)} • ${formatInr(currentTxn.amount)}` : 'Idle'}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2 text-xs font-mono">
                <span className="text-slate-400">Taint Horizon:</span>
                <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400 font-bold">
                  {((timelineIndex + 1) / (lineageData?.timeline.length || 1) * 100).toFixed(0)}% Dispersed
                </span>
              </div>
            </div>

            {/* Slider */}
            <div>
              <input
                type="range"
                min={0}
                max={Math.max(0, (lineageData?.timeline.length || 1) - 1)}
                value={timelineIndex}
                onChange={(e) => {
                  setIsPlaying(false);
                  setTimelineIndex(Number(e.target.value));
                }}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#E5334F]"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
                <span>Victim Breach (T-0)</span>
                <span>L1 Aggregator Consolidation</span>
                <span>L2 Dispersal Fan-out</span>
                <span>Cash-Out Exit Intercepted</span>
              </div>
            </div>
          </div>

          {/* Node Profile Inspector & Next-Hop Predictions */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Selected Node Details */}
            <div className="lg:col-span-6 bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="font-bold text-sm text-white flex items-center space-x-2">
                  <ShieldAlert className="w-4 h-4 text-[#E5334F]" />
                  <span>Inspected Account Forensic Profile</span>
                </span>
                <span className="font-mono text-xs text-cyan-400 bg-slate-900 px-2.5 py-0.5 rounded border border-slate-800">
                  {selectedNodeId || 'None'}
                </span>
              </div>

              {selectedNode ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-white text-base">{selectedNode.label}</h4>
                      <span className="text-xs text-slate-400 font-mono">Role: {selectedNode.role}</span>
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded text-xs font-mono font-bold ${
                        selectedNode.is_held
                          ? 'bg-rose-950 text-[#E5334F] border border-rose-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                    >
                      {selectedNode.is_held ? 'HOLD (LIEN ACTIVE)' : 'UNLOCKED / ACTIVE'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Bank Rail:</span>
                      <span className="text-white font-bold">{selectedNode.bank_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Graph Layer:</span>
                      <span className="text-white font-bold">Layer {selectedNode.layer}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Inbound Volume:</span>
                      <span className="text-emerald-400 font-bold">{formatInr(selectedNode.inflow)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Outbound Volume:</span>
                      <span className="text-rose-400 font-bold">{formatInr(selectedNode.outflow)}</span>
                    </div>
                  </div>

                  {/* Place Administrative Hold */}
                  <div className="pt-2">
                    <button
                      onClick={() => handleRequestHold(selectedNode.account_id)}
                      disabled={selectedNode.is_held || isHolding}
                      className="w-full py-3 rounded-xl text-xs font-bold bg-[#E5334F] hover:bg-rose-600 disabled:bg-slate-800 disabled:text-slate-500 text-white shadow-lg shadow-rose-950 transition flex items-center justify-center space-x-2"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>{selectedNode.is_held ? 'Administrative Lien Confirmed (Frozen)' : 'Request Administrative Hold (Lien)'}</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 italic py-6 text-center">Click any node in the Money DNA graph above to inspect.</div>
              )}
            </div>

            {/* Right: Next-Hop Escape Trajectory */}
            <div className="lg:col-span-6 bg-[#0D1527] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="font-bold text-sm text-white flex items-center space-x-2">
                  <GitBranch className="w-4 h-4 text-amber-400" />
                  <span>Predicted Next-Hop Destinations</span>
                </span>
                <span className="text-[11px] text-slate-400 font-mono">Dashed = Predicted • Solid = Held</span>
              </div>

              <div className="space-y-3">
                {[
                  {
                    id: 'ACC02233',
                    label: 'Nisha Rao (Layer 2 Dispersal)',
                    prob: 0.65,
                    bank: 'INTERNAL',
                    desc: 'Frequent high-velocity outflow recipient in Chain CH03.'
                  },
                  {
                    id: 'ACC02230',
                    label: 'Manoj Khan (Correlated Node)',
                    prob: 0.48,
                    bank: 'INTERNAL',
                    desc: 'Correlated hardware fingerprint cluster destination.'
                  },
                  {
                    id: 'ACC02231',
                    label: 'Rohan Gowda (Syndicate Layer)',
                    prob: 0.48,
                    bank: 'INTERNAL',
                    desc: 'Cluster partner destination based on historical IP co-location.'
                  }
                ].map((hop, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/50 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-white">{hop.id}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded font-mono bg-slate-800 text-slate-300">
                          {hop.bank}
                        </span>
                      </div>
                      <span className="text-xs font-mono font-bold text-amber-400">
                        {(hop.prob * 100).toFixed(0)}% Probability
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300 font-medium mt-1">{hop.label}</div>
                    <p className="text-[10px] text-slate-400 mt-0.5">{hop.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Live Transactions Feed Panel */}
      {activeTab === 'transactions' && (
        <div className="space-y-4 animate-in fade-in">
          {/* Controls Bar */}
          <div className="bg-[#0D1527] border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                placeholder="Search by Transaction ID, Sender Name/ID, or Receiver..."
                value={txnSearch}
                onChange={(e) => setTxnSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setTxnFilter('all')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  txnFilter === 'all' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                All Feed ({transactions.length})
              </button>
              <button
                onClick={() => setTxnFilter('mule')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  txnFilter === 'mule' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                Mule Flows Only
              </button>
              <button
                onClick={() => setTxnFilter('held')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  txnFilter === 'held' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                Held (Lien)
              </button>

              <button
                onClick={loadTransactions}
                disabled={isLoadingTxns}
                className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
                title="Refresh Feed"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingTxns ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="bg-[#0D1527] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-[11px] text-slate-400 uppercase font-mono border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Time</th>
                    <th className="py-3 px-4">Txn Reference</th>
                    <th className="py-3 px-4">Sender (Debit)</th>
                    <th className="py-3 px-4">Receiver (Credit)</th>
                    <th className="py-3 px-4 text-right">Amount (₹)</th>
                    <th className="py-3 px-4">Channel</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredTransactions.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500 italic">
                        No transactions found matching search query.
                      </td>
                    </tr>
                  ) : (
                    filteredTransactions.slice(0, 50).map((t) => {
                      const isHeld = t.status.includes('HELD');
                      const isMule = t.is_mule_flow === 1;

                      return (
                        <tr key={t.id} className="hover:bg-slate-800/40 transition">
                          <td className="py-2.5 px-4 text-slate-400 text-[11px]">
                            {t.ts.replace('T', ' ').slice(0, 19)}
                          </td>
                          <td className="py-2.5 px-4 font-bold text-white text-[11px]">
                            {t.id}
                          </td>
                          <td className="py-2.5 px-4">
                            <div className="text-white text-[11px] font-semibold">{t.sender_name || t.sender}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{t.sender} • {t.sender_bank || 'BANK'}</div>
                          </td>
                          <td className="py-2.5 px-4">
                            <div className="text-white text-[11px] font-semibold">{t.receiver_name || t.receiver}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{t.receiver} • {t.receiver_bank || 'BANK'}</div>
                          </td>
                          <td className="py-2.5 px-4 text-right font-bold text-white text-[11px]">
                            {formatInr(t.amount)}
                          </td>
                          <td className="py-2.5 px-4">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-bold">
                              {t.channel}
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-center">
                            <span
                              className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                isHeld
                                  ? 'bg-rose-950 text-[#E5334F] border border-rose-800'
                                  : isMule
                                  ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                  : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                              }`}
                            >
                              {t.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-center">
                            <div className="flex items-center justify-center space-x-1.5">
                              <button
                                onClick={() => handleTrackMoney(t)}
                                className="px-2 py-1 rounded bg-[#E5334F] hover:bg-rose-600 text-white font-bold text-[10px] shadow flex items-center space-x-1 transition"
                                title="Trace Money DNA fund-flow DAG for this transaction"
                              >
                                <GitBranch className="w-3 h-3" />
                                <span>Track Money</span>
                              </button>
                              <button
                                onClick={() => handleInspectTransaction(t)}
                                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-white text-[10px] font-sans font-semibold transition"
                              >
                                Inspect
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-slate-900/60 border-t border-slate-800 text-[11px] text-slate-500 font-mono text-center">
              Displaying {Math.min(50, filteredTransactions.length)} of {filteredTransactions.length} live transaction events.
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Detected Mules Master Directory Panel */}
      {activeTab === 'mules' && (
        <div className="space-y-4 animate-in fade-in">
          {/* Controls Bar */}
          <div className="bg-[#0D1527] border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                placeholder="Search detected mules by Account ID, Name, or Syndicate Chain (e.g. CH03)..."
                value={muleSearch}
                onChange={(e) => setMuleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setMuleFilterRole('all')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  muleFilterRole === 'all' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                All Mules ({mules.length})
              </button>
              <button
                onClick={() => setMuleFilterRole('L1')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  muleFilterRole === 'L1' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                L1 Aggregators
              </button>
              <button
                onClick={() => setMuleFilterRole('L2')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  muleFilterRole === 'L2' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                L2 Dispersal
              </button>
              <button
                onClick={() => setMuleFilterRole('held')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  muleFilterRole === 'held' ? 'bg-[#E5334F] text-white' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                Lien Requested
              </button>

              <button
                onClick={loadMules}
                disabled={isLoadingMules}
                className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
                title="Refresh Mules"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingMules ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Mules Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMules.map((m) => (
              <div
                key={m.id}
                className={`p-4 rounded-2xl border transition-all relative ${
                  m.is_held
                    ? 'bg-rose-950/40 border-[#E5334F] shadow-lg shadow-rose-950/40'
                    : 'bg-[#0D1527] border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-black text-white">{m.id}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-slate-800 text-slate-300">
                      {m.bank_id}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-950 text-[#E5334F] border border-rose-800">
                    {(m.mule_score * 100).toFixed(0)}% MULE RISK
                  </span>
                </div>

                <div className="mt-2">
                  <div className="font-bold text-sm text-white">{m.pseudonymous_label}</div>
                  <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-400 mt-0.5">
                    <span>Role: <strong className="text-amber-400">{m.role}</strong></span>
                    <span>•</span>
                    <span>Chain: <strong className="text-cyan-400">{m.chain_id || 'CH-AUTO'}</strong></span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 my-3">
                  <div>
                    <span className="text-slate-500 block">Layer:</span>
                    <span className="text-white font-bold">Layer {m.layer}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Shared Devices:</span>
                    <span className="text-amber-400 font-bold">{m.shared_devices} linked</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Balance:</span>
                    <span className="text-slate-300 font-bold">{formatInr(m.current_balance)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">KYC Tier:</span>
                    <span className="text-slate-300 font-bold">{m.kyc_tier}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <button
                    onClick={() => handleInspectMule(m)}
                    className="flex-1 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 transition text-center"
                  >
                    View in Money DNA
                  </button>
                  <button
                    onClick={() => handleRequestHold(m.id)}
                    disabled={m.is_held || isHolding}
                    className={`px-3 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 ${
                      m.is_held
                        ? 'bg-rose-950 text-[#E5334F] border border-rose-800 cursor-default'
                        : 'bg-[#E5334F] hover:bg-rose-600 text-white shadow-md'
                    }`}
                  >
                    <Lock className="w-3.5 h-3.5" />
                    <span>{m.is_held ? 'Held' : 'Hold'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
