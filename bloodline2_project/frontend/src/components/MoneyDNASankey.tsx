import React, { useMemo, useState } from 'react';
import { ShieldCheck, Lock, ExternalLink, Zap, Info, ArrowRight, Eye, CheckCircle2, ChevronDown } from 'lucide-react';
import { LineageResponse } from '../types';

interface MoneyDNASankeyProps {
  data: LineageResponse | null;
  onSelectNode?: (accountId: string) => void;
  onRequestHold?: (accountId: string) => void;
  selectedAccountId?: string | null;
  selectedChainId?: string;
  onSelectChain?: (chainId: string) => void;
}

export const MoneyDNASankey: React.FC<MoneyDNASankeyProps> = ({
  data,
  onSelectNode,
  onRequestHold,
  selectedAccountId,
  selectedChainId,
  onSelectChain
}) => {
  const [hoveredLink, setHoveredLink] = useState<any | null>(null);

  const formatInr = (val?: number) => {
    if (val === undefined || val === null) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)} L`;
    return `₹${Math.round(val).toLocaleString('en-IN')}`;
  };

  // Group nodes by layer (0: Origin, 1: Aggregator, 2: Dispersal, 3: Cash-out)
  const layerColumns = useMemo(() => {
    const cols: Record<number, LineageResponse['nodes']> = { 0: [], 1: [], 2: [], 3: [] };
    if (!data?.nodes) return cols;
    data.nodes.forEach((n) => {
      const l = Math.min(3, Math.max(0, n.layer));
      if (!cols[l]) cols[l] = [];
      cols[l].push(n);
    });
    return cols;
  }, [data]);

  const layerMeta = [
    { title: 'Layer 0: Stolen Origin', subtitle: 'Victim Debit & Breach', color: 'emerald', badge: 'SOURCE' },
    { title: 'Layer 1: Aggregator Hubs', subtitle: 'Rapid Inflow Consolidation', color: 'rose', badge: 'MULE L1' },
    { title: 'Layer 2: Dispersal Hops', subtitle: 'High-Velocity Smurfing', color: 'amber', badge: 'MULE L2' },
    { title: 'Layer 3: Cash-Out Exits', subtitle: 'ATM / Crypto / External', color: 'purple', badge: 'EXIT SINK' }
  ];

  // Geometric coordinates for pixel-perfect card positioning & SVG arrow connectors
  const cardWidth = 220;
  const cardHeight = 88;
  const colWidth = 275;
  const leftMargin = 20;
  const topOffset = 70;
  const verticalSpacing = 98;

  // Map each node to (x, y) coordinates
  const nodePositions = useMemo(() => {
    const pos: Record<string, { x: number; y: number; node: any }> = {};
    if (!data?.nodes) return pos;

    [0, 1, 2, 3].forEach((layerIdx) => {
      const nodesInLayer = layerColumns[layerIdx] || [];
      const colX = leftMargin + layerIdx * colWidth;
      const cardX = colX + 12;

      nodesInLayer.forEach((node, nodeIdx) => {
        const nodeY = topOffset + nodeIdx * verticalSpacing;
        pos[node.id] = { x: cardX, y: nodeY, node };
        pos[node.account_id] = { x: cardX, y: nodeY, node };
      });
    });
    return pos;
  }, [layerColumns, data]);

  // Canvas size
  const maxNodesInCol = Math.max(
    (layerColumns[0]?.length || 1),
    (layerColumns[1]?.length || 1),
    (layerColumns[2]?.length || 1),
    (layerColumns[3]?.length || 1),
    2
  );
  const canvasHeight = Math.max(460, topOffset + maxNodesInCol * verticalSpacing + 30);
  const canvasWidth = leftMargin * 2 + 4 * colWidth;

  // Resolve links with source and target coordinate positions
  const resolvedLinks = useMemo(() => {
    if (!data?.links) return [];
    return data.links.slice(0, 40).map((l, idx) => {
      const sourcePos = nodePositions[l.source] || nodePositions[l.source_account];
      const targetPos = nodePositions[l.target] || nodePositions[l.target_account];
      return {
        ...l,
        id: `link-${idx}`,
        sourcePos,
        targetPos
      };
    }).filter(l => l.sourcePos && l.targetPos);
  }, [data?.links, nodePositions]);

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-80 bg-[#0D1527] border border-slate-800 rounded-2xl text-slate-500 text-xs space-y-3">
        <Info className="w-8 h-8 text-cyan-400 animate-pulse" />
        <span className="font-semibold text-slate-400">Loading Money DNA fund-flow lineage...</span>
      </div>
    );
  }

  const activeChain = selectedChainId || data.active_chain || 'CH03';

  return (
    <div className="w-full bg-[#0B1220] border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
      {/* Top Header & Syndicate Controls */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h3 className="text-base font-black tracking-tight text-white flex items-center space-x-2">
              <span>Money DNA Fund-Flow Graph</span>
              <span className="text-[#E5334F]">•</span>
              <span className="text-xs font-mono font-bold text-cyan-400">Directional Flow Vector</span>
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/80 text-rose-300 border border-rose-800/60 animate-pulse">
              LIVE FLOW REPLAY
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
              Simulated Data
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Visualizing multi-hop taint dispersion with directional arrows, hop transit times, and administrative lien boundaries.
          </p>
        </div>

        {/* Syndicate Chain Selector & Legend */}
        <div className="flex flex-wrap items-center gap-3">
          {data.available_chains && data.available_chains.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-400 font-mono font-semibold">Syndicate:</span>
              <div className="relative">
                <select
                  value={activeChain}
                  onChange={(e) => onSelectChain?.(e.target.value)}
                  className="bg-slate-900 border border-slate-700 hover:border-cyan-500 rounded-xl px-3 py-1.5 text-xs font-mono font-bold text-cyan-300 focus:outline-none focus:ring-1 focus:ring-cyan-400 cursor-pointer pr-8"
                >
                  {data.available_chains.map((c) => (
                    <option key={c.chain_id} value={c.chain_id}>
                      {c.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-cyan-400 absolute right-2.5 top-2.5 pointer-events-none" />
              </div>
            </div>
          )}

          {/* Legend Items */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <div className="flex items-center space-x-1.5 text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded-md border border-emerald-900/60">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>Origin Source</span>
            </div>
            <div className="flex items-center space-x-1.5 text-rose-400 bg-rose-950/40 px-2 py-1 rounded-md border border-rose-900/60">
              <span className="w-2 h-2 rounded-full bg-[#E5334F]"></span>
              <span>Tainted Mule Path &rarr;</span>
            </div>
            <div className="flex items-center space-x-1.5 text-cyan-400 bg-cyan-950/40 px-2 py-1 rounded-md border border-cyan-900/60">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span>Lien Intercepted</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tracked Transaction Banner (when tracking a specific transaction) */}
      {data.target_txn_details && (
        <div className="p-3.5 rounded-xl bg-cyan-950/70 border border-cyan-500/80 text-xs flex flex-wrap items-center justify-between gap-3 text-cyan-200 shadow-lg shadow-cyan-950/40 animate-in fade-in">
          <div className="flex items-center space-x-2.5">
            <span className="px-2 py-0.5 rounded font-mono font-bold bg-cyan-900 text-white border border-cyan-400 text-[10px] animate-pulse">
              TRACKED TRANSACTION
            </span>
            <span className="font-mono font-bold text-white text-sm">{data.target_txn_details.id}</span>
            <span>•</span>
            <span className="text-white font-bold">{formatInr(data.target_txn_details.amount)}</span>
            <span className="text-slate-400 font-mono">({data.target_txn_details.channel})</span>
          </div>
          <div className="flex items-center space-x-2 font-mono text-[11px] text-slate-300">
            <span>Sender: <strong className="text-white">{data.target_txn_details.sender}</strong></span>
            <span>&rarr;</span>
            <span>Payee: <strong className="text-amber-400">{data.target_txn_details.receiver}</strong></span>
          </div>
        </div>
      )}

      {/* Interactive Flow Canvas (HTML Node Cards + Overlaid SVG Directional Arrows) */}
      <div className="relative overflow-x-auto rounded-xl bg-gradient-to-b from-[#0D1527] to-[#070C16] border border-slate-800/80 scrollbar-thin scrollbar-thumb-slate-800">
        <div
          className="relative select-none"
          style={{ width: `${canvasWidth}px`, height: `${canvasHeight}px`, minWidth: `${canvasWidth}px` }}
        >
          {/* Layer Column Guide Tracks & Column Headers */}
          {[0, 1, 2, 3].map((layerIdx) => {
            const colX = leftMargin + layerIdx * colWidth;
            const meta = layerMeta[layerIdx];
            const nodeCount = layerColumns[layerIdx]?.length || 0;

            return (
              <div
                key={`col-track-${layerIdx}`}
                style={{
                  position: 'absolute',
                  left: `${colX}px`,
                  top: '12px',
                  width: `${colWidth - 14}px`,
                  height: `${canvasHeight - 24}px`
                }}
                className="bg-[#0B1220]/60 border border-slate-800/70 rounded-2xl p-3 flex flex-col justify-between pointer-events-none"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-white tracking-wide">{meta.title}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded font-bold bg-slate-800 text-slate-300">
                      {nodeCount} {nodeCount === 1 ? 'node' : 'nodes'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-0.5 font-sans">{meta.subtitle}</span>
                </div>
                <div className="text-[9px] font-mono text-slate-600 text-right">
                  {meta.badge}
                </div>
              </div>
            );
          })}

          {/* SVG Directional Arrow Paths (Overlay with Bézier Curves & Particle Animation) */}
          <svg
            className="absolute inset-0 pointer-events-none w-full h-full"
            width={canvasWidth}
            height={canvasHeight}
          >
            <defs>
              {/* Arrowhead Markers */}
              <marker
                id="arrow-crimson"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#E5334F" />
              </marker>

              <marker
                id="arrow-emerald"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10B981" />
              </marker>

              <marker
                id="arrow-cyan"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#06B6D4" />
              </marker>

              <marker
                id="arrow-amber"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#F59E0B" />
              </marker>

              <filter id="glow-crimson" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Directional Flow Link Paths */}
            {resolvedLinks.map((link) => {
              const x1 = link.sourcePos.x + cardWidth;
              const y1 = link.sourcePos.y + cardHeight / 2;
              const x2 = link.targetPos.x;
              const y2 = link.targetPos.y + cardHeight / 2;

              const dx = Math.abs(x2 - x1);
              const cx1 = x1 + dx * 0.45;
              const cx2 = x2 - dx * 0.45;
              const pathData = `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`;

              const isHeldPath = link.is_held || link.sourcePos.node.is_held || link.targetPos.node.is_held;
              const isTargetTxn = link.is_target_txn || (data.target_txn_id && link.txn_id === data.target_txn_id);
              const isHovered = hoveredLink?.id === link.id || isTargetTxn;

              return (
                <g
                  key={link.id}
                  className="pointer-events-auto cursor-pointer"
                  onMouseEnter={() => setHoveredLink(link)}
                  onMouseLeave={() => setHoveredLink(null)}
                >
                  {/* Background Track Line */}
                  <path
                    d={pathData}
                    fill="none"
                    stroke={
                      isTargetTxn
                        ? '#9A3412'
                        : isHeldPath
                        ? '#065F46'
                        : isHovered
                        ? '#BE123C'
                        : '#4C0519'
                    }
                    strokeWidth={isTargetTxn ? 6 : isHovered ? 5.5 : 3.5}
                    strokeOpacity={isHovered ? 0.95 : 0.5}
                  />

                  {/* Foreground Animated Dashed Flow Line with Arrowhead */}
                  <path
                    d={pathData}
                    fill="none"
                    stroke={
                      isTargetTxn
                        ? '#F59E0B'
                        : isHeldPath
                        ? '#10B981'
                        : isHovered
                        ? '#FB7185'
                        : '#E5334F'
                    }
                    strokeWidth={isTargetTxn ? 4 : isHovered ? 3.5 : 2}
                    strokeDasharray={isHeldPath ? 'none' : '6 4'}
                    markerEnd={
                      isTargetTxn
                        ? 'url(#arrow-amber)'
                        : isHeldPath
                        ? 'url(#arrow-emerald)'
                        : 'url(#arrow-crimson)'
                    }
                    filter={isHovered || isTargetTxn ? 'url(#glow-crimson)' : undefined}
                  >
                    {!isHeldPath && (
                      <animate
                        attributeName="stroke-dashoffset"
                        values="20;0"
                        dur={isTargetTxn ? '0.9s' : '1.2s'}
                        repeatCount="indefinite"
                      />
                    )}
                  </path>

                  {/* Midpoint Amount Badge */}
                  {dx > 40 && (
                    <g transform={`translate(${(x1 + x2) / 2}, ${(y1 + y2) / 2})`}>
                      <rect
                        x={isTargetTxn ? '-48' : '-38'}
                        y="-11"
                        width={isTargetTxn ? '96' : '76'}
                        height="22"
                        rx="7"
                        fill="#0B1220"
                        stroke={
                          isTargetTxn
                            ? '#F59E0B'
                            : isHeldPath
                            ? '#059669'
                            : isHovered
                            ? '#FB7185'
                            : '#334155'
                        }
                        strokeWidth={isTargetTxn ? '1.8' : '1.2'}
                      />
                      <text
                        x="0"
                        y="4"
                        textAnchor="middle"
                        fill={isTargetTxn ? '#FDE68A' : isHeldPath ? '#34D399' : '#FDA4AF'}
                        fontSize="9.5"
                        fontWeight="bold"
                        fontFamily="ui-monospace, monospace"
                      >
                        {isTargetTxn ? `★ ${formatInr(link.amount)}` : formatInr(link.amount)}
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </svg>

          {/* HTML Interactive Node Cards (Zero foreignObject bugs, full DOM responsiveness) */}
          {Object.entries(nodePositions)
            // Filter unique by account_id so we don't render duplicate DOM nodes
            .filter(([key, pos]) => key === pos.node.id)
            .map(([nodeKey, pos]) => {
              const { node, x, y } = pos;
              const isSelected = selectedAccountId === node.account_id;
              const isOrigin = node.layer === 0;
              const isExit = node.layer === 3;
              const isHeld = node.is_held;

              return (
                <div
                  key={nodeKey}
                  style={{
                    position: 'absolute',
                    left: `${x}px`,
                    top: `${y}px`,
                    width: `${cardWidth}px`,
                    height: `${cardHeight}px`
                  }}
                  onClick={() => onSelectNode?.(node.account_id)}
                  className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer select-none shadow-lg flex flex-col justify-between ${
                    isHeld
                      ? 'bg-rose-950/80 border-[#E5334F] ring-2 ring-rose-500/50 shadow-rose-950/80'
                      : isSelected
                      ? 'bg-slate-900 border-cyan-400 ring-2 ring-cyan-500/50 shadow-cyan-950/80'
                      : isOrigin
                      ? 'bg-emerald-950/60 border-emerald-700/70 hover:border-emerald-400'
                      : isExit
                      ? 'bg-purple-950/60 border-purple-800/70 hover:border-purple-400'
                      : 'bg-slate-900/90 border-slate-700/80 hover:border-rose-500/80'
                  }`}
                >
                  {/* Top Row: Account ID + Bank Tag */}
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-black text-white truncate max-w-[120px]" title={node.account_id}>
                      {node.account_id}
                    </span>
                    <span
                      className={`text-[8.5px] px-1.5 py-0.5 rounded font-mono font-bold ${
                        isHeld
                          ? 'bg-rose-900 text-white'
                          : isOrigin
                          ? 'bg-emerald-900/90 text-emerald-200'
                          : isExit
                          ? 'bg-purple-900/90 text-purple-200'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {node.bank_id || 'INTERNAL'}
                    </span>
                  </div>

                  {/* Account Name & Role */}
                  <div className="flex items-center justify-between text-[10px] mt-0.5">
                    <span className="text-slate-200 font-semibold truncate max-w-[130px]" title={node.label}>
                      {node.label}
                    </span>
                    <span className="text-[8.5px] font-mono text-slate-400">
                      {node.role?.replace('MULE_', '') || (isOrigin ? 'SOURCE' : 'MULE')}
                    </span>
                  </div>

                  {/* Volume + Action */}
                  <div className="flex items-center justify-between text-[10px] font-mono pt-1 border-t border-slate-800/70 mt-1">
                    <span className="text-slate-400">
                      {isOrigin ? 'Debited:' : 'Flow:'} <strong className="text-white font-bold">{formatInr(node.outflow || node.inflow)}</strong>
                    </span>

                    {isHeld ? (
                      <span className="text-[#E5334F] font-bold text-[9px] uppercase tracking-wide flex items-center space-x-1 bg-rose-950 px-1.5 py-0.5 rounded border border-rose-800">
                        <Lock className="w-2.5 h-2.5" />
                        <span>Held</span>
                      </span>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRequestHold?.(node.account_id);
                        }}
                        className="text-[9px] px-2 py-0.5 rounded bg-slate-800 hover:bg-[#E5334F] text-slate-300 hover:text-white transition font-sans font-semibold border border-slate-700 hover:border-rose-600"
                      >
                        Hold
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Metric Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono pt-1">
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 block">Total Stolen Tracked:</span>
          <span className="text-sm font-bold text-white">{formatInr(data.total_tracked_inr)}</span>
        </div>
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 block">Intercepted / Held:</span>
          <span className="text-sm font-bold text-emerald-400">{formatInr(data.total_held_inr)}</span>
        </div>
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 block">Escaped to Cash-Out:</span>
          <span className="text-sm font-bold text-rose-400">{formatInr(data.total_exited_inr)}</span>
        </div>
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 block">Active Flow Links:</span>
          <span className="text-sm font-bold text-cyan-400">{resolvedLinks.length} Directional Hops</span>
        </div>
      </div>
    </div>
  );
};
