import React, { useState } from "react";
import { Shield, BrainCircuit, Users, Heart, Zap, Truck, Check } from "lucide-react";
import { Decision } from "../../types/stadium";

interface PredictionItem {
  id: string;
  type: string;
  probability: number;
  confidence: number;
  severity: string;
  reasoning: string;
  targetSector: string;
  recommendations: Array<{ id: string; title: string; description: string; status: string }>;
}

interface DecisionFeedProps {
  decisions: Decision[];
  predictions: PredictionItem[];
  onAcceptRecommendation?: (_predId: string, _recId: string) => void;
}

export default function DecisionFeed({
  decisions = [],
  predictions = [],
  onAcceptRecommendation,
}: DecisionFeedProps) {
  const [activeTab, setActiveTab] = useState<"decisions" | "predictions">("decisions");

  const getTeamIcon = (team: string) => {
    switch (team?.toUpperCase()) {
      case "VOLUNTEER":
        return <Users className="w-4 h-4 text-primary" />;
      case "SECURITY":
        return <Shield className="w-4 h-4 text-rose-400" />;
      case "MEDICAL":
        return <Heart className="w-4 h-4 text-danger" />;
      case "TRANSPORT":
      case "TRANSPORTATION":
        return <Truck className="w-4 h-4 text-blue-400" />;
      default:
        return <Zap className="w-4 h-4 text-warning" />;
    }
  };

  const getTeamBadgeStyle = (team: string) => {
    switch (team?.toUpperCase()) {
      case "VOLUNTEER":
        return "bg-primary/10 text-primary border-primary/20";
      case "SECURITY":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "MEDICAL":
        return "bg-danger/10 text-danger border-danger/20";
      case "TRANSPORT":
      case "TRANSPORTATION":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      default:
        return "bg-warning/10 text-warning border-warning/20";
    }
  };

  const formatPredictionType = (type: string) => {
    return type?.replace(/_/g, " ");
  };

  return (
    <div className="glass rounded-2xl p-6 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80 mb-4">
        <div className="flex gap-2 p-1 rounded-xl bg-zinc-900/60 border border-zinc-800">
          <button
            onClick={() => setActiveTab("decisions")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide uppercase transition-all duration-300 ${
              activeTab === "decisions"
                ? "bg-zinc-800 text-white shadow-md border border-zinc-700/50"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Decision Feed ({decisions.length})
          </button>
          <button
            onClick={() => setActiveTab("predictions")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide uppercase transition-all duration-300 ${
              activeTab === "predictions"
                ? "bg-zinc-800 text-white shadow-md border border-zinc-700/50"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            AI Predictions ({predictions.length})
          </button>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-semibold tracking-wider text-warning uppercase">
          <BrainCircuit className="w-4 h-4 text-warning" />
          Mitigation Matrix
        </div>
      </div>

      {/* Content body */}
      <div className="flex-1 overflow-y-auto pr-1">
        {activeTab === "decisions" ? (
          decisions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-sm font-light">
              <BrainCircuit className="w-8 h-8 text-zinc-700 mb-3 animate-pulse" />
              Evaluating telemetry. No decisions logged yet.
            </div>
          ) : (
            <div className="space-y-4">
              {decisions.map((dec) => (
                <div
                  key={dec.id}
                  className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/40 hover:bg-zinc-900/30 hover:border-zinc-700/50 transition-all duration-300 relative overflow-hidden group"
                >
                  {/* Visual accent left line */}
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-warning/80 shadow-[0_0_8px_#f59e0b]" />

                  <div className="pl-2">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                      <span className={`px-2.5 py-0.5 rounded-full border text-[9px] font-bold tracking-wider uppercase flex items-center gap-1.5 ${getTeamBadgeStyle(dec.responsible_team)}`}>
                        {getTeamIcon(dec.responsible_team)}
                        {dec.responsible_team}
                      </span>
                      <span className="text-[10px] text-zinc-500 font-medium">
                        ETA: <strong className="text-zinc-300 font-semibold">{dec.eta}</strong>
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white mb-2 leading-relaxed tracking-wide group-hover:text-warning transition-colors duration-300">
                      {dec.decision}
                    </h4>

                    <div className="space-y-2 mt-3 pt-3 border-t border-zinc-900/80 text-xs">
                      <div>
                        <span className="text-zinc-500 font-medium uppercase text-[10px] tracking-wider block mb-0.5">Trigger Condition</span>
                        <p className="text-zinc-400 font-light leading-relaxed">{dec.reason}</p>
                      </div>
                      <div>
                        <span className="text-zinc-500 font-medium uppercase text-[10px] tracking-wider block mb-0.5">Target Impact</span>
                        <p className="text-zinc-400 font-light leading-relaxed text-success/90">{dec.expected_impact}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          predictions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-sm font-light">
              <BrainCircuit className="w-8 h-8 text-zinc-700 mb-3 animate-pulse" />
              Warming up AI heuristic engines...
            </div>
          ) : (
            <div className="space-y-4">
              {predictions.map((pred) => (
                <div
                  key={pred.id}
                  className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/20 hover:border-zinc-800 transition-all duration-300"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">
                        {formatPredictionType(pred.type)}
                      </h4>
                      <div className="text-[10px] text-zinc-500 mt-0.5">
                        Sector: <strong className="text-zinc-400">{pred.targetSector}</strong>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        pred.probability >= 0.85
                          ? "bg-danger/10 border-danger/25 text-danger"
                          : pred.probability >= 0.65
                          ? "bg-warning/10 border-warning/25 text-warning"
                          : "bg-success/10 border-success/25 text-success"
                      }`}>
                        {(pred.probability * 100).toFixed(0)}% Probability
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-zinc-400 font-light leading-relaxed mb-3 mt-1">
                    {pred.reasoning}
                  </p>

                  {/* Recommendations */}
                  {pred.recommendations && pred.recommendations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-zinc-900 space-y-2">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 block">Proposed Action Reroute</span>
                      {pred.recommendations.map((rec) => (
                        <div key={rec.id} className="p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800 flex justify-between items-center gap-3">
                          <div>
                            <div className="text-xs font-bold text-white">{rec.title}</div>
                            <div className="text-[10px] text-zinc-400 font-light mt-0.5">{rec.description}</div>
                          </div>
                          {rec.status === "PENDING" && onAcceptRecommendation ? (
                            <button
                              onClick={() => onAcceptRecommendation(pred.id, rec.id)}
                              className="px-2 py-1 rounded bg-zinc-800 hover:bg-success/10 hover:text-success hover:border-success/30 border border-zinc-700/50 text-[10px] font-semibold uppercase tracking-wider text-zinc-300 transition-all duration-300"
                            >
                              Approve
                            </button>
                          ) : (
                            <span className="text-[10px] font-bold text-success flex items-center gap-1">
                              <Check className="w-3.5 h-3.5" /> Checked
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
