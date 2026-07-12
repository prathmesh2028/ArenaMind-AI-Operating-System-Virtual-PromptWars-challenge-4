"use client";

import React from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine, CartesianGrid } from "recharts";
import { AreaChart as ChartIcon } from "lucide-react";

interface ChartDataPoint {
  timeLabel: string;
  density: number;
  waitTime: number;
}

interface ReplayChartsProps {
  chartData: ChartDataPoint[];
  currentFrameIndex: number;
}

export default function ReplayCharts({ chartData = [], currentFrameIndex = 0 }: ReplayChartsProps) {
  // Get time label of current scrubber index
  const activeTimeLabel = chartData[currentFrameIndex]?.timeLabel || "";

  return (
    <div className="glass p-5 rounded-2xl border border-zinc-850 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-zinc-900">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
          <ChartIcon className="w-4.5 h-4.5 text-danger" />
          Synchronized Metrics Timeline
        </h3>
        <span className="text-[10px] text-zinc-500 font-light font-mono">Real-time Telemetry Graph</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Crowd Density Line Chart */}
        <div className="space-y-1">
          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block pl-2">
            Sector D Density (%)
          </span>
          <div className="h-40 w-full bg-zinc-950/20 rounded-xl border border-zinc-900/60 p-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="densityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#18181b" />
                <XAxis dataKey="timeLabel" stroke="#3f3f46" fontSize={8} />
                <YAxis stroke="#3f3f46" fontSize={8} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "10px", borderRadius: "8px" }}
                />
                <Area type="monotone" dataKey="density" stroke="#f59e0b" fillOpacity={1} fill="url(#densityGrad)" strokeWidth={2} />
                
                {/* Vertical Reference Line syncing with current playback position */}
                {activeTimeLabel && (
                  <ReferenceLine x={activeTimeLabel} stroke="#ef4444" strokeWidth={1.5} label={{ value: "REPLAY", fill: "#ef4444", fontSize: 7, position: "top" }} />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Gate 2 Queue Wait Time Line Chart */}
        <div className="space-y-1">
          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block pl-2">
            Gate 2 Wait Time (Seconds)
          </span>
          <div className="h-40 w-full bg-zinc-950/20 rounded-xl border border-zinc-900/60 p-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="waitGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#18181b" />
                <XAxis dataKey="timeLabel" stroke="#3f3f46" fontSize={8} />
                <YAxis stroke="#3f3f46" fontSize={8} domain={[0, 1000]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", fontSize: "10px", borderRadius: "8px" }}
                />
                <Area type="monotone" dataKey="waitTime" stroke="#ef4444" fillOpacity={1} fill="url(#waitGrad)" strokeWidth={2} />
                
                {/* Vertical Reference Line */}
                {activeTimeLabel && (
                  <ReferenceLine x={activeTimeLabel} stroke="#ef4444" strokeWidth={1.5} />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
