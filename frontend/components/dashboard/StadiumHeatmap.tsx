import React from "react";
import { DoorOpen, AlertTriangle } from "lucide-react";
import type { SectorData, GateData } from "../../lib/types";
import { getDensityColor, getDensityProgressColor } from "../../lib/utils";
import {
  DENSITY_CRITICAL_THRESHOLD,
  DENSITY_WARNING_THRESHOLD,
  DENSITY_WARNING_PCT,
} from "../../lib/constants";

interface StadiumHeatmapProps {
  sectors: SectorData[];
  gates: GateData[];
}

export default function StadiumHeatmap({ sectors = [], gates = [] }: StadiumHeatmapProps) {
  const getGateStyle = (gate: GateData) => {
    if (gate.malfunctioning) return "border-danger bg-danger/5 text-danger animate-pulse";
    if (gate.queueDepth > 150) return "border-warning bg-warning/5 text-warning";
    return "border-zinc-800 bg-zinc-950/20 text-zinc-300";
  };

  return (
    <div className="glass rounded-2xl p-6 flex flex-col h-full overflow-hidden">
      <h3 className="text-sm font-semibold tracking-wider uppercase text-zinc-400 mb-6">
        Stadium Density Heatmap & Checkpoints
      </h3>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 flex-1 overflow-y-auto pr-1">
        {/* Left/Middle Column - Stadium Bowl sectors grid */}
        <div className="xl:col-span-2 flex flex-col justify-between">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {sectors.map((sec) => {
              const densityPct = (sec.density * 100);
              return (
                <div
                  key={sec.sector}
                  className={`p-4 rounded-xl border bg-gradient-to-br flex flex-col justify-between h-36 transition-all duration-300 ${getDensityColor(sec.density)}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white tracking-wide">
                      {sec.sector}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                      sec.density >= DENSITY_CRITICAL_THRESHOLD
                        ? "bg-danger/25 text-danger"
                        : sec.density >= DENSITY_WARNING_THRESHOLD
                        ? "bg-warning/25 text-warning"
                        : "bg-success/25 text-success"
                    }`}>
                      {sec.status}
                    </span>
                  </div>

                  <div>
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="text-xl font-extrabold tracking-tight text-white">
                        {densityPct.toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-zinc-400 font-light">
                        {sec.count.toLocaleString()} / {sec.capacity.toLocaleString()}
                      </span>
                    </div>

                    {/* Progress indicator */}
                    <div className="w-full bg-zinc-850 h-1.5 rounded-full overflow-hidden mb-2">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ease-out ${getDensityProgressColor(sec.density)}`}
                        style={{ width: `${Math.min(100, densityPct)}%` }}
                      />
                    </div>

                    <div className="text-[10px] text-zinc-500 font-medium flex justify-between items-center border-t border-zinc-800/20 pt-1">
                      <span>Wait Est.</span>
                      <span className="text-zinc-300 font-semibold">
                        {Math.floor(sec.count / 150)} min
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-5 p-4 rounded-xl bg-zinc-950/40 border border-zinc-800 flex items-center gap-3 text-xs">
            <DoorOpen className="w-5 h-5 text-primary shrink-0" />
            <p className="text-zinc-400 font-light leading-relaxed">
              <strong>Interactive Crowd Rerouting:</strong> The Decision Engine automatically shifts stadium signage displays and redeploys wayfinding volunteers when any sector breaches the {DENSITY_WARNING_PCT}% warning mark.
            </p>
          </div>
        </div>

        {/* Right Column - Entry Gates queues */}
        <div className="flex flex-col">
          <h4 className="text-xs font-semibold tracking-wider text-zinc-500 uppercase mb-3">
            Ingress Gate Checkpoints
          </h4>
          <div className="space-y-3 flex-1">
            {gates.map((g) => (
              <div
                key={g.gate}
                className={`p-3.5 rounded-xl border flex justify-between items-center transition-all duration-300 ${getGateStyle(g)}`}
              >
                <div>
                  <div className="text-xs font-bold flex items-center gap-1.5">
                    {g.gate}
                    {g.malfunctioning && (
                      <span className="inline-flex items-center gap-0.5 bg-danger/25 border border-danger/30 text-[8px] px-1 rounded-sm uppercase tracking-wider font-extrabold">
                        <AlertTriangle className="w-2.5 h-2.5" /> Malfunction
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-zinc-500 mt-1 flex gap-3 font-medium">
                    <span>Rate: <strong className="text-zinc-300">{g.serviceRate} fans/m</strong></span>
                    <span>Wait: <strong className="text-zinc-300">{Math.ceil(g.waitTime / 60)} min</strong></span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-lg font-extrabold tracking-tight">
                    {g.queueDepth}
                  </div>
                  <div className="text-[9px] text-zinc-500 font-semibold uppercase tracking-wider">
                    In Queue
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
