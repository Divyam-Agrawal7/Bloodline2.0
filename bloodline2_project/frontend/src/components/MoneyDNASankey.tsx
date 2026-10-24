import React, { useMemo, useState } from 'react';
import { ArrowRight, ShieldCheck, Lock, ExternalLink, Zap, Info, Eye } from 'lucide-react';
import { LineageResponse } from '../types';

interface MoneyDNASankeyProps {
  data: LineageResponse | null;
  onSelectNode?: (accountId: string) => void;
  onRequestHold?: (accountId: string) => void;
  selectedAccountId?: string | null;
}

export const MoneyDNASankey: React.FC<MoneyDNASankeyProps> = ({
  data,
  onSelectNode,
  onRequestHold,
  selectedAccountId
}) => {
  const [hoveredLink, setHoveredLink] = useState<any | null>(null);
  const [filterLayer, setFilterLayer] = useState<number | null>(null);

  const formatInr = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)} L`;
    return `₹${Math.round(val).toLocaleString('en-IN')}`;
  };

  // Group nodes by layer (0, 1, 2, 3)
  const layerColumns = useMemo(() => {
    const cols: Record<number, LineageResponse['nodes']> = { 0: [], 1: [], 2: [], 3: [] };
    (data?.nodes || []).forEach((n) => {
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
    { title: 'Layer 3: Cash-Out Exits', subtitle: 'ATM / Crypto / Hawala', color: 'purple', badge: 'EXIT SINK' }
  ];

  // Calculate geometric node coordinates for SVG arrow paths
  const cardWidth = 210;
  const cardHeight = 84;
  const colWidth = 270;
  const topOffset = 70;
  const verticalSpacing = 96;

  // Map each node to its (x, y) coordinates
  const nodePositions = useMemo(() => {
    const pos: Record<string, { x: number; y: number; node: any }> = {};
    [0, 1, 2, 3].forEach((layerIdx) => {
      const nodesInLayer = layerColumns[layerIdx] || [];
      const colX = 30 + layerIdx * colWidth;
      nodesInLayer.forEach((node, nodeIdx) => {
        const nodeY = topOffset + nodeIdx * verticalSpacing;
        pos[node.id] = { x: colX, y: nodeY, node };
      });
    });
    return pos;
  }, [layerColumns]);

  // Compute SVG canvas dimensions
  const maxNodesInCol = Math.max(
    (layerColumns[0]?.length || 1),
    (layerColumns[1]?.length || 1),
    (layerColumns[2]?.length || 1),
    (layerColumns[3]?.length || 1)
  );
  const canvasHeight = Math.max(480, topOffset + maxNodesInCol * verticalSpacing + 40);
  const canvasWidth = 30 + 4 * colWidth + 40;

  // Resolve links between nodes
  const resolvedLinks = useMemo(() => {
    if (!data?.links) return [];
    return data.links.map((l, idx) => {
      const sourcePos = nodePositions[l.source] || Object.values(nodePositions).find(p => p.node.account_id === l.source_account);
      const targetPos = nodePositions[l.target] || Object.values(nodePositions).find(p => p.node.account_id === l.target_account);
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
      <div className="flex flex-col items-center justify-center h-80 bg-[#0D1527] border border-slate-800 rounded-2xl text-slate-500 text-xs space-y-2">
        <Info className="w-6 h-6 text-slate-600 animate-pulse" />
        <span>No Money DNA lineage flows loaded. Select an origin transaction to trace fund flows.</span>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#0B1220] border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
      {/* Header & Flow Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
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
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Visualizing multi-hop taint dispersion with directional arrows, hop transit times, and administrative lien boundaries.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded-md border border-emerald-900/60">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
            <span>Origin Source</span>
          </div>
          <div className="flex items-center space-x-1.5 text-rose-400 bg-rose-950/40 px-2 py-1 rounded-md border border-rose-900/60">
            <span className="w-2.5 h-2.5 rounded-full bg-[#E5334F]"></span>
            <span>Tainted Mule Path &rarr;</span>
          </div>
          <div className="flex items-center space-x-1.5 text-amber-400 bg-amber-950/40 px-2 py-1 rounded-md border border-amber-900/60">
            <span className="w-2 h-2 border border-amber-400 border-dashed rounded-full"></span>
            <span>Predicted Next Hop &rarr;</span>
          </div>
          <div className="flex items-center space-x-1.5 text-cyan-400 bg-cyan-950/40 px-2 py-1 rounded-md border border-cyan-900/60">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
            <span>Lien Intercepted</span>
          </div>
        </div>
      </div>

      {/* Interactive Flow Canvas */}
      <div className="relative overflow-x-auto rounded-xl bg-gradient-to-b from-[#0D1527] to-[#070C16] border border-slate-800/80 scrollbar-thin scrollbar-thumb-slate-800">
        <svg
          width={canvasWidth}
          height={canvasHeight}
          className="w-full min-w-[1100px]"
          style={{ minHeight: `${canvasHeight}px` }}
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

            {/* Glowing Gradients */}
            <linearGradient id="gradient-flow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#E5334F" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
            </linearGradient>

            <filter id="glow-crimson" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Layer Background Columns & Header Titles */}
          {[0, 1, 2, 3].map((layerIdx) => {
            const colX = 20 + layerIdx * colWidth;
            const meta = layerMeta[layerIdx];
            return (
              <g key={`col-header-${layerIdx}`}>
                {/* Column Guide Track */}
                <rect
                  x={colX}
                  y={12}
                  width={cardWidth + 20}
                  height={canvasHeight - 24}
                  rx="14"
                  fill="#0B1220"
                  fillOpacity="0.6"
                  stroke="#1E293B"
                  strokeWidth="1"
                />

                {/* Column Header Title */}
                <text
                  x={colX + 14}
                  y={38}
                  fill="#F8FAFC"
                  fontSize="12"
                  fontWeight="bold"
                  fontFamily="system-ui, -apple-system, sans-serif"
                >
                  {meta.title}
                </text>
                <text
                  x={colX + 14}
                  y={54}
                  fill="#94A3B8"
                  fontSize="10"
                  fontFamily="system-ui, -apple-system, sans-serif"
                >
                  {meta.subtitle}
                </text>
              </g>
            );
          })}

          {/* Directional Connecting Arrows (Flow Links) */}
          {resolvedLinks.map((link) => {
            const x1 = link.sourcePos.x + cardWidth;
            const y1 = link.sourcePos.y + cardHeight / 2;
            const x2 = link.targetPos.x;
            const y2 = link.targetPos.y + cardHeight / 2;

            // Smooth cubic Bézier curvature
            const dx = Math.abs(x2 - x1);
            const cx1 = x1 + dx * 0.45;
            const cx2 = x2 - dx * 0.45;
            const pathData = `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`;

            const isHeldPath = link.is_held || link.sourcePos.node.is_held || link.targetPos.node.is_held;
            const isHovered = hoveredLink?.id === link.id;

            return (
              <g
                key={link.id}
                onMouseEnter={() => setHoveredLink(link)}
                onMouseLeave={() => setHoveredLink(null)}
                className="cursor-pointer transition-opacity"
              >
                {/* Background Shadow Link */}
                <path
                  d={pathData}
                  fill="none"
                  stroke={isHeldPath ? '#065F46' : '#881337'}
                  strokeWidth={isHovered ? 6 : 3}
                  strokeOpacity={isHovered ? 0.9 : 0.4}
                />

                {/* Foreground Flow Line with Arrow */}
                <path
                  d={pathData}
                  fill="none"
                  stroke={isHeldPath ? '#10B981' : isHovered ? '#FB7185' : '#E5334F'}
                  strokeWidth={isHovered ? 3.5 : 2}
                  strokeDasharray={isHeldPath ? 'none' : '6 4'}
                  markerEnd={isHeldPath ? 'url(#arrow-emerald)' : 'url(#arrow-crimson)'}
                  filter={isHovered ? 'url(#glow-crimson)' : undefined}
                >
                  {/* Active Fluid Motion Particle Animation */}
                  {!isHeldPath && (
                    <animate
                      attributeName="stroke-dashoffset"
                      values="20;0"
                      dur="1.2s"
                      repeatCount="indefinite"
                    />
                  )}
                </path>

                {/* Money Flow Amount Badge in Center of Path */}
                {dx > 40 && (
                  <g transform={`translate(${(x1 + x2) / 2}, ${(y1 + y2) / 2})`}>
                    <rect
                      x="-36"
                      y="-11"
                      width="72"
                      height="20"
                      rx="6"
                      fill="#0B1220"
                      stroke={isHovered ? '#FB7185' : '#334155'}
                      strokeWidth="1"
                    />
                    <text
                      x="0"
                      y="3"
                      textAnchor="middle"
                      fill={isHeldPath ? '#34D399' : '#FDA4AF'}
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="ui-monospace, monospace"
                    >
                      {formatInr(link.amount)}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Node Cards Rendered via SVG ForeignObjects */}
          {Object.entries(nodePositions).map(([nodeKey, pos]) => {
            const { node, x, y } = pos;
            const isSelected = selectedAccountId === node.account_id;
            const isOrigin = node.layer === 0;
            const isExit = node.layer === 3;
            const isHeld = node.is_held;

            return (
              <foreignObject
                key={nodeKey}
                x={x}
                y={y}
                width={cardWidth}
                height={cardHeight}
                className="overflow-visible"
              >
                <div
                  onClick={() => onSelectNode?.(node.account_id)}
                  className={`h-full p-2.5 rounded-xl border text-left transition-all cursor-pointer relative select-none shadow-lg ${
                    isHeld
                      ? 'bg-rose-950/70 border-[#E5334F] ring-2 ring-rose-500/40 shadow-rose-950/80'
                      : isSelected
                      ? 'bg-slate-900 border-cyan-400 ring-2 ring-cyan-500/40'
                      : isOrigin
                      ? 'bg-emerald-950/50 border-emerald-700/60 hover:border-emerald-400'
                      : isExit
                      ? 'bg-purple-950/50 border-purple-800/60 hover:border-purple-400'
                      : 'bg-slate-900/90 border-slate-700/70 hover:border-rose-500/80'
                  }`}
                >
                  {/* Top Row: Account ID + Bank Tag */}
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-black text-white truncate max-w-[110px]" title={node.account_id}>
                      {node.account_id}
                    </span>
                    <span
                      className={`text-[8px] px-1.5 py-0.2 rounded font-mono font-bold ${
                        isHeld
                          ? 'bg-rose-900 text-white'
                          : isOrigin
                          ? 'bg-emerald-900/90 text-emerald-200'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {node.bank_id || 'BANK'}
                    </span>
                  </div>

                  {/* Account Name / Label */}
                  <div className="text-[10px] text-slate-300 font-medium truncate mt-0.5" title={node.label}>
                    {node.label}
                  </div>

                  {/* Volume + Action */}
                  <div className="flex items-center justify-between text-[10px] font-mono mt-1 pt-1 border-t border-slate-800/70">
                    <span className="text-slate-400">
                      {isOrigin ? 'Debited:' : 'Flow:'} <strong className="text-white font-bold">{formatInr(node.outflow || node.inflow)}</strong>
                    </span>

                    {isHeld ? (
                      <span className="text-[#E5334F] font-bold text-[9px] uppercase tracking-wide flex items-center space-x-1">
                        <Lock className="w-2.5 h-2.5" />
                        <span>Held</span>
                      </span>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRequestHold?.(node.account_id);
                        }}
                        className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-[#E5334F] text-slate-300 hover:text-white transition font-sans font-semibold"
                      >
                        Hold
                      </button>
                    )}
                  </div>
                </div>
              </foreignObject>
            );
          })}
        </svg>
      </div>

      {/* Dynamic Summary Strip */}
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
