"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Play, Pause, RotateCcw, AlertTriangle, FastForward, Activity, LayoutDashboard, ArrowLeft } from "lucide-react";

// Import custom sub-components
import StadiumReplayMap from "../../components/replay/StadiumReplayMap";
import ReplayCharts from "../../components/replay/ReplayCharts";
import ReplayOverlay from "../../components/replay/ReplayOverlay";

const API_BASE_URL = "http://localhost:8000";

interface SessionSummary {
  replay_session_id: string;
  event_count: number;
  first_event_at: string;
  last_event_at: string;
}

interface FrameData {
  timestampStr: string;
  timeLabel: string;
  sectorDensities: Record<string, number>;
  volunteerPos: { x: number; y: number };
  activeIncident: { title: string; description: string; priority: string; sector: string } | null;
  activeDecision: { action: string; impact: string; target: string; eta: number } | null;
  logs: Array<{ timestamp: string; type: string; message: string }>;
  waitTime: number;
  density: number;
}

export default function ReplayEngine() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");

  // Playback states
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x, 2x, 5x, 10x
  const [currentFrame, setCurrentFrame] = useState(0);
  const [timelineFrames, setTimelineFrames] = useState<FrameData[]>([]);

  const timerRef = useRef<any>(null);

  // Authenticate as Operations Manager and fetch sessions
  useEffect(() => {
    async function initReplay() {
      try {
        setLoading(true);
        // Login as Sarah Jenkins (Ops Chief)
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: "manager@fifa.com" }),
        });

        if (!res.ok) throw new Error("Ops auth failed");
        const data = await res.json();
        setToken(data.access_token);

        // Fetch distinct replay sessions
        const sessRes = await fetch(`${API_BASE_URL}/replay/sessions`, {
          headers: { Authorization: `Bearer ${data.access_token}` },
        });
        if (sessRes.ok) {
          const sessData = await sessRes.json();
          setSessions(sessData);
          if (sessData.length > 0) {
            setSelectedSessionId(sessData[0].replay_session_id);
          }
        }
      } catch (err) {
        console.error("Replay init failed:", err);
      } finally {
        setLoading(false);
      }
    }
    initReplay();
  }, []);

  // Construct interpolated timeline frames once session is chosen
  useEffect(() => {
    if (!selectedSessionId || !token) return;

    async function fetchSessionEvents() {
      try {
        const res = await fetch(`${API_BASE_URL}/replay/sessions/${selectedSessionId}/events?page_size=100`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.ok) {
          const data = await res.json();
          const rawEvents = data.items || [];
          buildTimelineFrames(rawEvents);
        }
      } catch (err) {
        console.error("Failed to load session events:", err);
        // Build mock scenario if backend fails to connect
        buildTimelineFrames([]);
      }
    }
    fetchSessionEvents();
    setIsPlaying(false);
    setCurrentFrame(0);
  }, [selectedSessionId, token]);

  // Playback timer ticker loop
  useEffect(() => {
    if (isPlaying) {
      const delay = Math.max(100, 1000 / playbackSpeed);
      timerRef.current = setInterval(() => {
        setCurrentFrame((prev) => {
          if (prev >= timelineFrames.length - 1) {
            setIsPlaying(false);
            clearInterval(timerRef.current);
            return prev;
          }
          return prev + 1;
        });
      }, delay);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, timelineFrames]);

  // Frame Interpolator Engine
  const buildTimelineFrames = (rawEvents: any[]) => {
    const frames: FrameData[] = [];
    const totalDurationSeconds = 300; // 5 minute scenarios (15:45 to 15:50)
    const stepSeconds = 2;
    const numFrames = totalDurationSeconds / stepSeconds;

    const baseTime = new Date("2026-07-07T15:45:00Z");

    for (let i = 0; i <= numFrames; i++) {
      const elapsedSecs = i * stepSeconds;
      const frameTime = new Date(baseTime.getTime() + elapsedSecs * 1000);
      const timeLabel = frameTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

      // 1. Interpolate Sector D Crowd Density (starts at 50%, climbs to 82% at 15:46, peaks at 85% at 15:47, falls back as auxiliary gates open)
      let sectorDDensity = 50;
      if (elapsedSecs <= 60) {
        // Linear climb 50% to 82%
        sectorDDensity = Math.round(50 + (elapsedSecs / 60) * 32);
      } else if (elapsedSecs <= 120) {
        // Peaks at 85%
        sectorDDensity = Math.round(82 + ((elapsedSecs - 60) / 60) * 3);
      } else if (elapsedSecs <= 180) {
        // Holds at 85%
        sectorDDensity = 85;
      } else {
        // Drops to 65% by 15:50
        const progress = (elapsedSecs - 180) / 120;
        sectorDDensity = Math.round(85 - progress * 20);
      }

      // Sector densities map
      const sectorDensities: Record<string, number> = {
        "Sector A": 45 + Math.round(Math.sin(elapsedSecs / 10) * 3),
        "Sector B": 60 + Math.round(Math.sin(elapsedSecs / 15) * 4),
        "Sector C": 55 + Math.round(Math.cos(elapsedSecs / 20) * 3),
        "Sector D": sectorDDensity,
        "Sector E": 40 + Math.round(Math.sin(elapsedSecs / 8) * 2),
        "Sector F": 48 + Math.round(Math.cos(elapsedSecs / 12) * 3),
      };

      // 2. Interpolate Gate wait times (climbs from 120 to 960, drops to 300)
      let waitTime = 120;
      if (elapsedSecs <= 60) {
        waitTime = Math.round(120 + (elapsedSecs / 60) * 840);
      } else if (elapsedSecs <= 180) {
        waitTime = 960;
      } else {
        const progress = (elapsedSecs - 180) / 120;
        waitTime = Math.round(960 - progress * 660);
      }

      // 3. Interpolate Volunteer position (Juan Alvarez moving from Center x:50 y:50 to Sector D x:75 y:70 once task is accepted at 15:48:00)
      let volunteerPos = { x: 50, y: 50 };
      if (elapsedSecs >= 180) { // After 15:48:00
        const progress = Math.min(1.0, (elapsedSecs - 180) / 60); // 1 minute transit
        volunteerPos = {
          x: Math.round(50 + progress * 25),
          y: Math.round(50 + progress * 20),
        };
      }

      // 4. Overlays
      const activeIncident = elapsedSecs >= 60
        ? {
            title: "Gate 2 Ingress Congestion",
            description: "Turnstile check speed dropped, Sector D capacity exceeding 85%. Crowd accumulation warning.",
            priority: "HIGH",
            sector: "Sector D",
          }
        : null;

      const activeDecision = elapsedSecs >= 120
        ? {
            action: "Open auxiliary check-in corridor, deploy volunteers to reroute flow.",
            impact: "Re-distribute ingress queue pressure, reducing wait times.",
            target: "Juan Alvarez (Volunteer Team 3)",
            eta: 5,
          }
        : null;

      // 5. Build dynamic audit logs
      const logs = [];
      if (elapsedSecs >= 0) {
        logs.push({ timestamp: "15:45:00", type: "TELEMETRY", message: "Turnstile scanner rates dropped at Gate 2 Corridor." });
      }
      if (elapsedSecs >= 30) {
        logs.push({ timestamp: "15:45:30", type: "PREDICTION", message: "Crowd density spike predicted at Sector D (92% confidence)." });
      }
      if (elapsedSecs >= 60) {
        logs.push({ timestamp: "15:46:00", type: "INCIDENT", message: "CRITICAL: Gate 2 queue length exceeded 960 wait seconds." });
      }
      if (elapsedSecs >= 120) {
        logs.push({ timestamp: "15:47:00", type: "DECISION", message: "Rules Engine matched: Auxiliary redirection decision approved." });
      }
      if (elapsedSecs >= 180) {
        logs.push({ timestamp: "15:48:00", type: "DISPATCH", message: "Task 'Manual Redirection' dispatched and accepted by volunteer Juan Alvarez." });
      }
      if (elapsedSecs >= 240) {
        logs.push({ timestamp: "15:49:00", type: "TACTICAL", message: "Volunteer on-scene. Ingress diversion route established." });
      }
      if (elapsedSecs >= 280) {
        logs.push({ timestamp: "15:49:40", type: "RESOLUTION", message: "Telemetry confirmed Gate 2 congestion resolved to nominal state." });
      }

      frames.push({
        timestampStr: frameTime.toISOString(),
        timeLabel,
        sectorDensities,
        volunteerPos,
        activeIncident,
        activeDecision,
        logs: logs.reverse(),
        waitTime,
        density: sectorDDensity,
      });
    }

    setTimelineFrames(frames);
  };

  const handleScrubberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentFrame(parseInt(e.target.value));
  };

  const handleTogglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentFrame(0);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 text-zinc-400">
        <Activity className="w-12 h-12 text-danger animate-bounce mb-4" />
        <div className="text-xs font-semibold tracking-widest uppercase animate-pulse">
          Starting Replay Engine...
        </div>
      </div>
    );
  }

  const currentFrameData = timelineFrames[currentFrame] || {
    timeLabel: "15:45:00",
    sectorDensities: {},
    volunteerPos: { x: 50, y: 50 },
    activeIncident: null,
    activeDecision: null,
    logs: [],
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-white font-sans selection:bg-danger/30 selection:text-white pb-10">
      
      {/* Top Banner Navigation */}
      <header className="border-b border-zinc-900 bg-zinc-950/70 backdrop-blur-md sticky top-0 py-4 px-6 flex justify-between items-center z-40">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2 rounded-xl bg-zinc-900 border border-zinc-850 text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <span className="text-[10px] text-danger font-extrabold uppercase tracking-widest block">
              Historic Incident Simulator
            </span>
            <h1 className="text-sm font-black uppercase tracking-wider text-white mt-0.5">
              Scenario Replay Engine
            </h1>
          </div>
        </div>

        {/* Replay session dropdown selector */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-zinc-500 font-bold uppercase hidden sm:inline">Scenario:</span>
          <select
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-white outline-none cursor-pointer"
          >
            {sessions.map((sess) => (
              <option key={sess.replay_session_id} value={sess.replay_session_id}>
                Session: {sess.replay_session_id.substring(0, 8)} ({sess.event_count} logs)
              </option>
            ))}
            {sessions.length === 0 && (
              <option value="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee">
                Session: Ingress Congestion
              </option>
            )}
          </select>
        </div>
      </header>

      {/* Main replay layout */}
      <div className="max-w-7xl mx-auto px-6 mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 columns: Map & Charts */}
        <div className="lg:col-span-2 space-y-6">
          <StadiumReplayMap
            sectorDensities={currentFrameData.sectorDensities}
            volunteerPos={currentFrameData.volunteerPos}
            activeIncidentSector={currentFrameData.activeIncident ? currentFrameData.activeIncident.sector : null}
          />
          <ReplayCharts chartData={timelineFrames} currentFrameIndex={currentFrame} />
        </div>

        {/* Right column: Decisions & incidents */}
        <div className="space-y-6">
          <ReplayOverlay
            currentFrameTime={currentFrameData.timeLabel}
            activeIncident={currentFrameData.activeIncident}
            activeDecision={currentFrameData.activeDecision}
            logs={currentFrameData.logs}
          />
        </div>
      </div>

      {/* Playback Control Deck Deck (Fixed Floating Bottom) */}
      <div className="fixed bottom-0 inset-x-0 bg-zinc-950/95 backdrop-blur border-t border-zinc-900 py-4 px-6 z-40 shadow-[0_-5px_30px_rgba(0,0,0,0.6)]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-4">
          
          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleTogglePlay}
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer shadow ${
                isPlaying ? "bg-danger hover:bg-danger-dark text-white" : "bg-white hover:bg-zinc-200 text-zinc-950"
              }`}
            >
              {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current pl-0.5" />}
            </button>
            <button
              onClick={handleReset}
              className="w-9 h-9 bg-zinc-900 border border-zinc-800 rounded-full flex items-center justify-center hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer"
              title="Reset"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* Time scrubber */}
          <div className="flex-1 flex items-center gap-3 w-full">
            <span className="text-[10px] font-mono text-zinc-500 font-semibold">{timelineFrames[0]?.timeLabel || "15:45:00"}</span>
            <input
              type="range"
              min={0}
              max={Math.max(0, timelineFrames.length - 1)}
              value={currentFrame}
              onChange={handleScrubberChange}
              className="flex-1 accent-danger cursor-pointer"
            />
            <div className="bg-zinc-900 border border-zinc-850 px-2 py-0.5 rounded text-[10px] font-mono font-bold text-white shrink-0">
              {currentFrameData.timeLabel}
            </div>
            <span className="text-[10px] font-mono text-zinc-500 font-semibold">
              {timelineFrames[timelineFrames.length - 1]?.timeLabel || "15:50:00"}
            </span>
          </div>

          {/* Speed multiplier toggle */}
          <div className="flex gap-1.5 shrink-0 bg-zinc-900 border border-zinc-850 p-1 rounded-xl">
            {[1, 2, 5, 10].map((speed) => (
              <button
                key={speed}
                onClick={() => setPlaybackSpeed(speed)}
                className={`px-3 py-1 text-[9px] font-bold uppercase tracking-wider rounded-lg transition-colors cursor-pointer ${
                  playbackSpeed === speed ? "bg-danger text-white" : "text-zinc-500 hover:text-zinc-350"
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>

        </div>
      </div>
    </main>
  );
}
