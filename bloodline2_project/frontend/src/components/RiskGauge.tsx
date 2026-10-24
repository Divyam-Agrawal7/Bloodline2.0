import React from 'react';

interface RiskGaugeProps {
  score: number; // 0.0 to 1.0
  verdict: 'ALLOW' | 'DELAY' | 'HOLD';
  size?: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score, verdict, size = 180 }) => {
  const percent = Math.round(score * 100);
  const strokeWidth = 14;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = radius * Math.PI; // Half circle (180 deg)
  const strokeDashoffset = circumference - (circumference * percent) / 100;

  const getColor = () => {
    if (percent >= 70) return '#E5334F'; // Crimson
    if (percent >= 40) return '#F59E0B'; // Amber
    return '#10B981'; // Emerald
  };

  const color = getColor();

  return (
    <div className="flex flex-col items-center justify-center relative select-none">
      <svg width={size} height={size * 0.62} className="overflow-visible">
        {/* Background Arc */}
        <path
          d={`M ${strokeWidth} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${size / 2}`}
          fill="none"
          stroke="#1E293B"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Foreground Colored Arc */}
        <path
          d={`M ${strokeWidth} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Center Value */}
      <div className="absolute top-[32%] flex flex-col items-center">
        <span className="font-mono font-extrabold text-3xl text-white tracking-tight">
          {percent}%
        </span>
        <span
          className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full mt-0.5 border"
          style={{
            color,
            borderColor: `${color}40`,
            backgroundColor: `${color}15`
          }}
        >
          {verdict}
        </span>
      </div>

      <div className="flex justify-between w-full px-2 text-[10px] text-slate-500 font-mono mt-1">
        <span>0 (Allow)</span>
        <span>40 (Delay)</span>
        <span>70 (Hold)</span>
        <span>100</span>
      </div>
    </div>
  );
};
