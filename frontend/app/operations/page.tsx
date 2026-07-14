"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Bot, ArrowLeft, RefreshCw, Radio } from "lucide-react";

import HealthScore from "../../components/dashboard/HealthScore";
import IncidentsList from "../../components/dashboard/IncidentsList";
import DecisionFeed from "../../components/dashboard/DecisionFeed";
import LiveCharts from "../../components/dashboard/LiveCharts";
import StadiumHeatmap from "../../components/dashboard/StadiumHeatmap";
import AiMissionControl from "../../components/dashboard/AiMissionControl";

import { Incident, Decision } from "../../types/stadium";
import type { SectorData, GateData, TimelineEvent, TimelineEventType, PredictionItem } from "../../lib/types";
import {
  API_BASE_URL,
  MANAGER_EMAIL,
  SECURITY_INCIDENT_DEDUCTION,
  SECURITY_CRITICAL_DEDUCTION,
  TRANSIT_DELAY_DEDUCTION,
  TRANSPORT_DELAY_PROBABILITY,
  ENERGY_ALERT_DEDUCTION,
  ENERGY_FORECAST_PROBABILITY,
  CROWD_HEALTH_DENSITY_FACTOR,
  TRANSIT_BASE_SCORE,
  ENERGY_BASE_SCORE,
  TELEMETRY_HISTORY_LIMIT,
} from "../../lib/constants";
import { clampScore } from "../../lib/utils";
import { useAuth } from "../../hooks/useAuth";
import { useWebSocket } from "../../hooks/useWebSocket";



export default function OperationsDashboard() {
  const [sectors, setSectors] = useState<SectorData[]>([]);
  const [gates, setGates] = useState<GateData[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);

  // Telemetry history lists for Recharts
  const [crowdHistory, setCrowdHistory] = useState<{ timestamp: string; [sector: string]: any }[]>([]);
  const [energyHistory, setEnergyHistory] = useState<{ timestamp: string; active_power: number; solar_offset: number }[]>([]);

  // Health scores
  const [healthScores, setHealthScores] = useState({
    global: 95,
    crowd: 96,
    transit: 98,
    security: 94,
    energy: 92,
  });

  // Authenticate and fetch initial data
  const { token, loading, setLoading } = useAuth(
    MANAGER_EMAIL,
    async (jwtToken: string) => {
      await fetchInitialDashboard(jwtToken);
    },
  );

  // Add event helper to timeline state
  const addTimelineEvent = useCallback(
    (id: string, topic: string, message: string, type: TimelineEventType) => {
      const timeStr = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      setTimeline((prev) => [
        { id, time: timeStr, topic, source: "bus.event", message, type },
        ...prev,
      ]);
    },
    [],
  );

  // WebSocket connection via shared hook
  const handleWsMessage = useCallback(
    (rawEvent: { id: string; topic: string; timestamp?: string; payload: Record<string, unknown> }) => {
      handleIncomingWsEvent(rawEvent);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sectors],
  );

  const { connected: wsConnected } = useWebSocket({
    token,
    onMessage: handleWsMessage,
  });

  /** Fetch initial REST APIs for the dashboard. */
  async function fetchInitialDashboard(jwtToken: string) {
    const headers = { Authorization: `Bearer ${jwtToken}` };

    try {
      const dashRes = await fetch(`${API_BASE_URL}/dashboard`, { headers });
      if (dashRes.ok) {
        const dash = await dashRes.json();

        const initialSectors: SectorData[] = dash.sectors.map(
          (s: Record<string, unknown>) => ({
            sector: s.sector as string,
            count: s.count as number,
            capacity: s.capacity as number,
            density: s.density as number,
            status: s.status as string,
          }),
        );
        setSectors(initialSectors);

        const baseTimestamp = new Date().toISOString();
        const initialCrowdHistory = [
          {
            timestamp: baseTimestamp,
            ...initialSectors.reduce<Record<string, number>>((acc, s) => {
              acc[s.sector] = Math.round(s.density * 100);
              return acc;
            }, {}),
          },
        ];
        setCrowdHistory(initialCrowdHistory);

        const initialEnergyHistory = [
          {
            timestamp: baseTimestamp,
            active_power: dash.energy.reduce(
              (sum: number, e: Record<string, number>) => sum + e.active_power_kw,
              0,
            ),
            solar_offset: dash.energy.reduce(
              (sum: number, e: Record<string, number>) => sum + (e.solar_offset_kw || 30),
              0,
            ),
          },
        ];
        setEnergyHistory(initialEnergyHistory);
      }

      const incRes = await fetch(`${API_BASE_URL}/incidents?page_size=30`, { headers });
      if (incRes.ok) {
        const incData = await incRes.json();
        setIncidents(
          incData.items.filter((i: Incident) => i.status !== "RESOLVED"),
        );
      }

      const decRes = await fetch(`${API_BASE_URL}/decisions?page_size=20`, { headers });
      if (decRes.ok) {
        const decData = await decRes.json();
        setDecisions(decData.items);
      }

      const predRes = await fetch(`${API_BASE_URL}/predictions?page_size=30`, { headers });
      if (predRes.ok) {
        const predData = await predRes.json();
        setPredictions(predData.items);
      }

      const historyRes = await fetch(
        `${API_BASE_URL}/operations/crowd/history?limit=60`,
        { headers },
      );
      if (historyRes.ok) {
        const histData = await historyRes.json();
        const grouped: Record<string, { timestamp: string; [sector: string]: any }> = {};
        histData.records.forEach((r: Record<string, unknown>) => {
          const ts = r.timestamp as string;
          if (!grouped[ts]) {
            grouped[ts] = { timestamp: ts };
          }
          grouped[ts][r.sector as string] = r.density;
        });

        const list = Object.values(grouped).sort(
          (a, b) =>
            new Date(a.timestamp).getTime() -
            new Date(b.timestamp).getTime(),
        );
        setCrowdHistory(list.slice(-12));
      }
    } catch (err) {
      console.error("Fetch dashboard error:", err);
    }
  }

  // Recalculate health scores when telemetries update
  useEffect(() => {
    if (sectors.length === 0) return;

    const avgDensity =
      sectors.reduce((sum, s) => sum + s.density, 0) / sectors.length;
    const crowd = clampScore(100 - avgDensity * CROWD_HEALTH_DENSITY_FACTOR);

    const activeCount = incidents.filter((i) => i.status !== "RESOLVED").length;
    const criticalCount = incidents.filter(
      (i) => i.status !== "RESOLVED" && i.priority === "CRITICAL",
    ).length;
    const security = clampScore(
      100 - activeCount * SECURITY_INCIDENT_DEDUCTION - criticalCount * SECURITY_CRITICAL_DEDUCTION,
    );

    const transportDelayCount = predictions.filter(
      (p) => p.type === "TRANSPORT_DELAY" && p.probability >= TRANSPORT_DELAY_PROBABILITY,
    ).length;
    const transit = clampScore(TRANSIT_BASE_SCORE - transportDelayCount * TRANSIT_DELAY_DEDUCTION);

    const gridAlertCount = predictions.filter(
      (p) => p.type === "ENERGY_FORECAST" && p.probability >= ENERGY_FORECAST_PROBABILITY,
    ).length;
    const energy = clampScore(ENERGY_BASE_SCORE - gridAlertCount * ENERGY_ALERT_DEDUCTION);

    const global = Math.round((crowd + security + transit + energy) / 4);

    setHealthScores({ global, crowd, transit, security, energy });
  }, [sectors, incidents, predictions]);

  // Handle incoming WebSocket messages dynamically
  function handleIncomingWsEvent(event: Record<string, unknown>) {
    const topic = (event.topic as string) || "";
    const payload = (event.payload as Record<string, unknown>) || {};
    const timestamp = (event.timestamp as string) || new Date().toISOString();

    if (topic === "crowd.tick") {
      const sectorName = payload.sector as string;
      const count = payload.count as number;
      const density = payload.density as number;
      const status = (payload.status as string) || "NORMAL";

      setSectors((prev) => {
        const exists = prev.some((s) => s.sector === sectorName);
        if (!exists) {
          return [...prev, { sector: sectorName, count, capacity: (payload.capacity as number) || 8000, density, status }];
        }
        return prev.map((s) =>
          s.sector === sectorName ? { ...s, count, density, status } : s,
        );
      });

      setCrowdHistory((prev) => {
        const lastRecord = prev[prev.length - 1];
        const isSameTime =
          lastRecord &&
          new Date(lastRecord.timestamp).getTime() ===
            new Date(timestamp).getTime();

        if (isSameTime && lastRecord) {
          const updated = { ...lastRecord, [sectorName]: Math.round(density * 100) };
          return [...prev.slice(0, -1), updated];
        }

        const newRecord: { timestamp: string; [sector: string]: any } = {
          timestamp,
          [sectorName]: Math.round(density * 100),
        };
        if (lastRecord) {
          sectors.forEach((s) => {
            if (s.sector !== sectorName) {
              newRecord[s.sector] =
                (lastRecord[s.sector] as number) || Math.round(s.density * 100);
            }
          });
        }
        return [...prev, newRecord].slice(-TELEMETRY_HISTORY_LIMIT);
      });
    } else if (topic === "gate.queue.tick") {
      const gateName = payload.gate as string;
      const queueDepth = payload.queue_depth as number;
      const serviceRate = payload.service_rate_per_min as number;
      const waitTime = payload.wait_time_seconds as number;
      const malfunctioning = payload.malfunctioning as boolean;

      setGates((prev) => {
        const exists = prev.some((g) => g.gate === gateName);
        if (!exists) {
          return [...prev, { gate: gateName, queueDepth, serviceRate, waitTime, malfunctioning }];
        }
        return prev.map((g) =>
          g.gate === gateName ? { ...g, queueDepth, serviceRate, waitTime, malfunctioning } : g,
        );
      });

      if (malfunctioning) {
        addTimelineEvent(
          event.id as string,
          topic,
          `Turnstile failure detected at checkpoint ${gateName}. Ingress rates restricted.`,
          "error",
        );
      }
    } else if (topic === "energy.tick") {
      const activeKw = payload.active_power_kw as number;
      const solarKw = (payload.solar_offset_kw as number) || 30;

      setEnergyHistory((prev) => {
        const lastRecord = prev[prev.length - 1];
        const isSameTime =
          lastRecord &&
          new Date(lastRecord.timestamp as string).getTime() ===
            new Date(timestamp).getTime();

        if (isSameTime && lastRecord) {
          const updated = {
            ...lastRecord,
            active_power: (lastRecord.active_power as number) + activeKw,
            solar_offset: (lastRecord.solar_offset as number) + solarKw,
          };
          return [...prev.slice(0, -1), updated];
        }

        const newRecord = { timestamp, active_power: activeKw, solar_offset: solarKw };
        return [...prev, newRecord].slice(-TELEMETRY_HISTORY_LIMIT);
      });
    } else if (topic === "incident.raised") {
      const newInc: Incident = {
        id: payload.incident_id as string,
        title: payload.title as string,
        description: payload.description as string,
        status: "ACTIVE",
        priority: payload.priority as "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
        sector: payload.sector as string,
        createdAt: timestamp,
      };

      setIncidents((prev) => [newInc, ...prev.filter((i) => i.id !== newInc.id)]);
      addTimelineEvent(
        event.id as string,
        topic,
        `New ${newInc.priority} incident raised: "${newInc.title}" in ${newInc.sector}.`,
        newInc.priority === "CRITICAL" || newInc.priority === "HIGH" ? "error" : "raised",
      );
    } else if (topic === "incident.resolved") {
      const incId = payload.incident_id as string;
      setIncidents((prev) => prev.filter((i) => i.id !== incId));
      addTimelineEvent(
        event.id as string,
        topic,
        `Incident ${incId.substring(0, 8)} successfully resolved by operations on-scene crew.`,
        "resolved",
      );
    } else if (topic === "decision.created") {
      const newDec: Decision = {
        id: payload.id as string,
        decision: payload.decision as string,
        reason: payload.reason as string,
        expected_impact: payload.expected_impact as string,
        responsible_team: payload.responsible_team as string,
        eta: payload.eta as number,
        action_type: payload.action_type as string,
        created_at: payload.created_at as string,
      };

      setDecisions((prev) => [newDec, ...prev.filter((d) => d.id !== newDec.id)]);
      addTimelineEvent(
        event.id as string,
        topic,
        `Mitigation rule triggered: [${newDec.action_type}] proposed to ${newDec.responsible_team}.`,
        "warning",
      );
    } else if (
      topic.includes("warning") ||
      topic.includes("alert") ||
      topic.includes("malfunction") ||
      topic.includes("delay")
    ) {
      const msg = (payload.message as string) || `System alert triggered on topic ${topic}`;
      addTimelineEvent(event.id as string, topic, msg, "warning");
    }
  }

  // Resolve active incident
  const handleResolveIncident = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: "RESOLVED" }),
      });

      if (res.ok) {
        // Remove locally
        setIncidents((prev) => prev.filter((i) => i.id !== id));
        // Publish incident.resolved event locally for connection timeline logging
        addTimelineEvent(id, "incident.resolved", `Manual resolution triggered for incident ${id.substring(0, 8)}.`, "resolved");
      }
    } catch (err) {
      console.error("Resolve incident failed:", err);
    }
  };

  // Approve prediction recommendations
  const handleAcceptRecommendation = async (predId: string, recId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/predictions/${predId}/recommendations/${recId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: "ACCEPTED" }),
      });

      if (res.ok) {
        // Refresh predictions list
        const headers = { Authorization: `Bearer ${token}` };
        const predRes = await fetch(`${API_BASE_URL}/predictions?page_size=30`, { headers });
        if (predRes.ok) {
          const predData = await predRes.json();
          setPredictions(predData.items);
        }
        addTimelineEvent(recId, "recommendation.accepted", `AI Recommendation ${recId.substring(0, 8)} approved and executed.`, "info");
      }
    } catch (err) {
      console.error("Accept recommendation error:", err);
    }
  };

  const handleManualRefresh = async () => {
    if (!token) return;
    setLoading(true);
    await fetchInitialDashboard(token);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background text-zinc-400">
        <Bot className="w-12 h-12 text-primary animate-bounce mb-4" />
        <div className="text-sm font-light uppercase tracking-wider animate-pulse">
          Loading ArenaMind Intelligence console...
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-background relative overflow-hidden flex flex-col">
      {/* Background radial overlays */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-success/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Header Bar */}
      <header className="border-b border-zinc-900 bg-zinc-950/40 backdrop-blur-md px-6 py-4 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all duration-300"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] bg-primary/10 border border-primary/20 text-primary px-2 py-0.5 rounded font-extrabold uppercase tracking-wider">
                Operations Center
              </span>
              <div className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-success animate-pulse" : "bg-warning animate-ping"}`} />
                {wsConnected ? "Telemetry Connected" : "Polling Mode"}
              </div>
            </div>
            <h1 className="text-xl font-black text-white tracking-tight mt-0.5">
              ArenaMind AI Executive Command
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleManualRefresh}
            className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all duration-300 cursor-pointer"
            title="Force refresh initial values"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="hidden md:flex items-center gap-2 bg-zinc-900/60 border border-zinc-850 px-3.5 py-1.5 rounded-xl text-xs">
            <Radio className="w-3.5 h-3.5 text-success animate-pulse" />
            <span className="text-zinc-500 font-light">Simulation clock:</span>
            <span className="text-white font-bold uppercase">Live Ticks</span>
          </div>
        </div>
      </header>

      {/* Main Grid Panels */}
      <div className="flex-1 overflow-y-auto p-6 z-10 space-y-6">
        {/* Top summary row: Health index card & Incidents Timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2">
            <HealthScore
              globalScore={healthScores.global}
              crowdHealth={healthScores.crowd}
              transitHealth={healthScores.transit}
              securityHealth={healthScores.security}
              sustainabilityHealth={healthScores.energy}
            />
          </div>
          <div className="lg:col-span-3">
            <IncidentsList
              incidents={incidents}
              timeline={timeline}
              onResolve={handleResolveIncident}
            />
          </div>
        </div>

        {/* Heatmap & Checkpoints */}
        <div className="w-full">
          <StadiumHeatmap sectors={sectors} gates={gates} />
        </div>

        {/* Live Recharts Graphs */}
        <div className="w-full">
          <LiveCharts crowdHistory={crowdHistory} energyHistory={energyHistory} />
        </div>

        {/* AI Mission Control and Decision Feed */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          <div className="xl:col-span-3">
            <AiMissionControl apiUrl={API_BASE_URL} token={token} />
          </div>
          <div className="xl:col-span-2">
            <DecisionFeed
              decisions={decisions}
              predictions={predictions}
              onAcceptRecommendation={handleAcceptRecommendation}
            />
          </div>
        </div>
      </div>

      {/* Footer bar */}
      <footer className="border-t border-zinc-950 bg-zinc-950/20 px-6 py-3 text-[10px] text-zinc-600 font-light flex justify-between items-center z-10 shrink-0">
        <span>ArenaMind OS v1.0.0 &bull; FIFA World Cup 2026 Operations Console</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-success rounded-full" /> All subsystems normal
        </span>
      </footer>
    </main>
  );
}
