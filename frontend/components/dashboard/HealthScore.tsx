import React from "react";
import { Shield, Users, Bus, Zap } from "lucide-react";

interface HealthScoreProps {
  globalScore: number;
  crowdHealth: number;
  transitHealth: number;
  securityHealth: number;
  sustainabilityHealth: number;
}

export default function HealthScore({
  globalScore = 100,
  crowdHealth = 100,
  transitHealth = 100,
  securityHealth = 100,
  sustainabilityHealth = 100,
}: HealthScoreProps) {
  // Compute circular progress properties
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (globalScore / 100) * circumference;

  const getHealthColor = (score: number) => {
    if (score >= 90) return "text-success border-success/20 bg-success/5";
    if (score >= 75) return "text-warning border-warning/20 bg-warning/5";
    return "text-danger border-danger/20 bg-danger/5";
  };

  const getHealthColorSvg = (score: number) => {
    if (score >= 90) return "stroke-success";
    if (score >= 75) return "stroke-warning";
    return "stroke-danger";
  };

  return (
    <div className="glass rounded-2xl p-6 flex flex-col justify-between h-full relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

      <div>
        <h3 className="text-sm font-semibold tracking-wider uppercase text-zinc-400 mb-6">
          Stadium Health Index
        </h3>

        <div className="flex flex-col md:flex-row items-center justify-around gap-6 mb-6">
          {/* Circular Global Score Gauge */}
          <div className="relative flex items-center justify-center w-36 h-36">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="72"
                cy="72"
                r={radius}
                className="stroke-zinc-800"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="72"
                cy="72"
                r={radius}
                className={`transition-all duration-1000 ease-out ${getHealthColorSvg(globalScore)}`}
                strokeWidth="10"
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute text-center">
              <span className="text-4xl font-extrabold tracking-tight text-white">
                {globalScore}
              </span>
              <span className="block text-[10px] text-zinc-500 font-medium uppercase tracking-wider">
                Index
              </span>
            </div>
          </div>

          {/* Health Index Rating Description */}
          <div className="flex flex-col justify-center text-center md:text-left">
            <div className="text-xs text-zinc-500 font-light mb-1">Status Rating</div>
            <div className="text-xl font-bold text-white flex items-center gap-2 justify-center md:justify-start">
              <span className="relative flex h-3 w-3">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${globalScore >= 75 ? 'bg-success' : 'bg-danger'}`}></span>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${globalScore >= 90 ? 'bg-success' : globalScore >= 75 ? 'bg-warning' : 'bg-danger'}`}></span>
              </span>
              {globalScore >= 90 ? "Optimal Operations" : globalScore >= 75 ? "Elevated Load" : "Critical Emergency"}
            </div>
            <p className="text-xs text-zinc-400 font-light mt-2 max-w-xs leading-relaxed">
              Real-time calculations derived from density telemetry, transport delay headways, grid load bounds, and active incident priorities.
            </p>
          </div>
        </div>
      </div>

      {/* Subsystem Health Breakdowns */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-zinc-800/60">
        {/* Crowd Health */}
        <div className={`border rounded-xl p-3 flex flex-col justify-between transition-all duration-300 ${getHealthColor(crowdHealth)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-zinc-400">Crowd</span>
            <Users className="w-3.5 h-3.5 opacity-60" />
          </div>
          <div>
            <div className="text-lg font-bold text-white leading-tight">{crowdHealth}%</div>
            <div className="text-[10px] text-zinc-500 font-light mt-0.5">Flow Rate</div>
          </div>
        </div>

        {/* Transit Health */}
        <div className={`border rounded-xl p-3 flex flex-col justify-between transition-all duration-300 ${getHealthColor(transitHealth)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-zinc-400">Transit</span>
            <Bus className="w-3.5 h-3.5 opacity-60" />
          </div>
          <div>
            <div className="text-lg font-bold text-white leading-tight">{transitHealth}%</div>
            <div className="text-[10px] text-zinc-500 font-light mt-0.5">Schedule</div>
          </div>
        </div>

        {/* Security Health */}
        <div className={`border rounded-xl p-3 flex flex-col justify-between transition-all duration-300 ${getHealthColor(securityHealth)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-zinc-400">Security</span>
            <Shield className="w-3.5 h-3.5 opacity-60" />
          </div>
          <div>
            <div className="text-lg font-bold text-white leading-tight">{securityHealth}%</div>
            <div className="text-[10px] text-zinc-500 font-light mt-0.5">Incidents</div>
          </div>
        </div>

        {/* Energy Health */}
        <div className={`border rounded-xl p-3 flex flex-col justify-between transition-all duration-300 ${getHealthColor(sustainabilityHealth)}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-zinc-400">Energy</span>
            <Zap className="w-3.5 h-3.5 opacity-60" />
          </div>
          <div>
            <div className="text-lg font-bold text-white leading-tight">{sustainabilityHealth}%</div>
            <div className="text-[10px] text-zinc-500 font-light mt-0.5">Grid Stability</div>
          </div>
        </div>
      </div>
    </div>
  );
}
