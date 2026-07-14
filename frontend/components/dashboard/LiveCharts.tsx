"use client";

import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import { formatTimestamp } from "../../lib/utils";
import { SECTOR_CHART_COLORS } from "../../lib/constants";

interface LiveChartsProps {
  crowdHistory: Array<{ timestamp: string; [sector: string]: unknown }>;
  energyHistory: Array<{ timestamp: string; active_power: number; solar_offset: number }>;
}

export default function LiveCharts({ crowdHistory = [], energyHistory = [] }: LiveChartsProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6 h-80 animate-pulse bg-zinc-900/40" />
        <div className="glass rounded-2xl p-6 h-80 animate-pulse bg-zinc-900/40" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
      {/* Crowd Density over time Chart */}
      <div className="glass rounded-2xl p-6 flex flex-col h-80 relative">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-zinc-400 mb-4">
          Crowd Density Index (%)
        </h3>
        <div className="flex-1 w-full text-xs">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={crowdHistory} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" opacity={0.3} />
              <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} stroke="#71717a" />
              <YAxis stroke="#71717a" domain={[0, 100]} tickFormatter={(val) => `${val}%`} />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
                labelFormatter={(label) => `Time: ${new Date(label).toLocaleTimeString()}`}
              />
              <Legend iconType="circle" />
              <Line type="monotone" dataKey="Sector A" stroke={SECTOR_CHART_COLORS["Sector A"]} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="Sector B" stroke={SECTOR_CHART_COLORS["Sector B"]} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="Sector C" stroke={SECTOR_CHART_COLORS["Sector C"]} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="Sector D" stroke={SECTOR_CHART_COLORS["Sector D"]} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="Sector E" stroke={SECTOR_CHART_COLORS["Sector E"]} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="Sector F" stroke={SECTOR_CHART_COLORS["Sector F"]} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid Load and Carbon Offsets Chart */}
      <div className="glass rounded-2xl p-6 flex flex-col h-80 relative">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-zinc-400 mb-4">
          Energy Grid Load & Clean Offset (kW)
        </h3>
        <div className="flex-1 w-full text-xs">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={energyHistory} margin={{ top: 5, right: 10, left: -15, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" opacity={0.3} />
              <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} stroke="#71717a" />
              <YAxis stroke="#71717a" />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
                labelFormatter={(label) => `Time: ${new Date(label).toLocaleTimeString()}`}
              />
              <Legend iconType="circle" />
              <Area
                type="monotone"
                dataKey="active_power"
                name="Grid Consumption"
                stroke="#f59e0b"
                fill="url(#colorPower)"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="solar_offset"
                name="Solar Generation"
                stroke="#10b981"
                fill="url(#colorSolar)"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <defs>
                <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
