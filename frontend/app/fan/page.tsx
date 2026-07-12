"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Smartphone, ArrowLeft, Signal, X } from "lucide-react";

// Import custom subviews
import BottomNav from "../../components/fan/BottomNav";
import HomeView from "../../components/fan/HomeView";
import FoodView from "../../components/fan/FoodView";
import AssistantView from "../../components/fan/AssistantView";
import EmergencyView from "../../components/fan/EmergencyView";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface ParkingItem {
  name: string;
  available_spots: number;
  status: string;
  occupancy_pct: number;
}

interface TransportItem {
  route: string;
  type: string;
  status: string;
  current_stop: string;
  seats_available: number;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  read: boolean;
  priority: string;
  type: string;
  created_at: string;
}

export default function FanPortal() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("home");
  const [wsConnected, setWsConnected] = useState(false);

  // Live data states
  const [parkingLots, setParkingLots] = useState<ParkingItem[]>([]);
  const [transitVehicles, setTransitVehicles] = useState<TransportItem[]>([]);
  const [sectors, setSectors] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  
  // Flash banner notification popup
  const [incomingAlert, setIncomingAlert] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  // Authenticate as FAN and fetch initial data
  useEffect(() => {
    async function loginAsFan() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: "fan1@gmail.com" }),
        });

        if (!res.ok) throw new Error();

        const data = await res.json();
        setToken(data.access_token);

        // Fetch initial data
        await fetchFanData(data.access_token);
      } catch (err) {
        console.error("Fan initialization failed:", err);
      } finally {
        setLoading(false);
      }
    }
    loginAsFan();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Establish WebSocket connection once token is available
  useEffect(() => {
    if (!token) return;

    const socket = new WebSocket(`${WS_BASE_URL}/dashboard/ws`);
    wsRef.current = socket;

    socket.onopen = () => {
      setWsConnected(true);
      console.log("[WS] Fan Portal telemetry connected");
    };

    socket.onmessage = (event) => {
      try {
        const rawEvent = JSON.parse(event.data);
        handleIncomingWsEvent(rawEvent);
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    socket.onclose = () => {
      setWsConnected(false);
      console.log("[WS] Fan connection lost");
    };

    return () => {
      socket.close();
    };
  }, [token]);

  async function fetchFanData(jwtToken: string) {
    const headers = { Authorization: `Bearer ${jwtToken}` };
    try {
      // 1. Parking
      const parkRes = await fetch(`${API_BASE_URL}/fan/parking`, { headers });
      if (parkRes.ok) {
        const parkData = await parkRes.json();
        setParkingLots(parkData.parking_lots);
      }

      // 2. Transport
      const transRes = await fetch(`${API_BASE_URL}/fan/transport`, { headers });
      if (transRes.ok) {
        const transData = await transRes.json();
        setTransitVehicles(transData.vehicles);
      }

      // 3. Crowd status
      const crowdRes = await fetch(`${API_BASE_URL}/fan/crowd-status`, { headers });
      if (crowdRes.ok) {
        const crowdData = await crowdRes.json();
        setSectors(crowdData.sectors);
      }

      // 4. Notifications
      const notifRes = await fetch(`${API_BASE_URL}/fan/notifications`, { headers });
      if (notifRes.ok) {
        const notifData = await notifRes.json();
        setNotifications(notifData.notifications);
      }
    } catch (err) {
      console.error("Fetch fan data failed:", err);
    }
  }

  function handleIncomingWsEvent(event: any) {
    const topic = event.topic || "";
    const payload = event.payload || {};

    if (topic === "parking.tick") {
      setParkingLots((prev) =>
        prev.map((lot) =>
          lot.name === payload.lot
            ? { ...lot, available_spots: payload.available, occupancy_pct: payload.pct_full, status: payload.status }
            : lot
        )
      );
    } 
    
    else if (topic === "transport.tick") {
      setTransitVehicles((prev) => {
        const exists = prev.some((v) => v.route === payload.route);
        if (!exists) {
          return [...prev, { route: payload.route, type: payload.type, status: payload.status, current_stop: payload.current_stop, seats_available: 100 - payload.occupancy_pct }];
        }
        return prev.map((v) =>
          v.route === payload.route
            ? { ...v, status: payload.status, current_stop: payload.current_stop, seats_available: 100 - payload.occupancy_pct }
            : v
        );
      });
    }

    else if (topic === "crowd.tick") {
      setSectors((prev) =>
        prev.map((sec) =>
          sec.sector === payload.sector
            ? { ...sec, density_pct: Math.round(payload.density * 100), wait_time_seconds: payload.wait_time_seconds, status: payload.status }
            : sec
        )
      );
    }

    // Capture safety notifications/alerts and trigger top banner
    else if (topic === "weather.heat_stress" || topic === "crowd.density.critical" || topic === "incident.resolved" || topic === "gate.malfunction") {
      let alertMsg = payload.message || `System alert triggered on topic ${topic}`;
      if (topic === "incident.resolved") {
        alertMsg = "Safety Notice: Reported incident has been successfully resolved by field responders.";
      }
      setIncomingAlert(alertMsg);

      // Add to notifications roster locally
      const localNotif: NotificationItem = {
        id: event.id,
        title: topic.replace(/\./g, " ").toUpperCase(),
        message: alertMsg,
        read: false,
        priority: "HIGH",
        type: "SYSTEM",
        created_at: new Date().toISOString(),
      };
      setNotifications((prev) => [localNotif, ...prev]);

      // Vibrate if supported
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
      }

      // Dismiss banner after 7 seconds
      setTimeout(() => {
        setIncomingAlert(null);
      }, 7000);
    }
  }

  // handleMarkRead has been removed as it is not actively used in the current subviews.

  const unreadCount = notifications.filter((n) => !n.read).length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 text-zinc-400">
        <Smartphone className="w-12 h-12 text-success animate-bounce mb-4" />
        <div className="text-xs font-semibold tracking-widest uppercase animate-pulse">
          Starting Fan Portal...
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center py-6 px-4">
      {/* Smartphone frame container */}
      <div className="w-full max-w-md min-h-[750px] max-h-[850px] bg-zinc-950 rounded-[40px] border-[10px] border-zinc-900 overflow-hidden flex flex-col justify-between shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8)] relative">
        
        {/* Dynamic Notch / Ear Piece */}
        <div className="absolute top-0 inset-x-0 h-6 bg-zinc-900 flex justify-center items-center z-40">
          <div className="w-24 h-4 bg-zinc-950 rounded-full" />
        </div>

        {/* Live Notification Popup Banner */}
        {incomingAlert && (
          <div className="absolute top-8 inset-x-3 bg-danger/95 backdrop-blur border border-danger/30 text-white rounded-2xl p-3.5 z-50 flex justify-between items-start shadow-xl animate-slideDown">
            <div className="flex-1 pr-3">
              <span className="text-[9px] bg-white/20 px-1.5 py-0.5 rounded font-extrabold uppercase tracking-wider block w-max mb-1.5">
                Critical Alert
              </span>
              <p className="text-[11px] font-bold leading-normal">{incomingAlert}</p>
            </div>
            <button
              onClick={() => setIncomingAlert(null)}
              className="p-1 bg-white/10 hover:bg-white/20 rounded-lg text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Portal Header Bar */}
        <header className="border-b border-zinc-900/60 bg-zinc-950/70 pt-8 pb-3 px-5 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-1.5 rounded-lg bg-zinc-900 border border-zinc-850 text-zinc-400 hover:text-white"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
            </Link>
            <div>
              <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-1">
                <Signal className={`w-2.5 h-2.5 ${wsConnected ? "text-success" : "text-zinc-650"}`} />
                {wsConnected ? "OS Synchronized" : "OS Offline"}
              </span>
              <h1 className="text-xs font-black text-white uppercase tracking-wider mt-0.5">
                ArenaMind Fan Portal
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Hard Rock</span>
          </div>
        </header>

        {/* Main Content sheet */}
        <div className="flex-1 overflow-y-auto px-5 py-4 z-10 bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-950">
          {activeTab === "home" ? (
            <HomeView parkingLots={parkingLots} transitVehicles={transitVehicles} _sectors={sectors} />
          ) : activeTab === "food" ? (
            <FoodView />
          ) : activeTab === "assistant" ? (
            <AssistantView apiUrl={API_BASE_URL} token={token} />
          ) : (
            <EmergencyView apiUrl={API_BASE_URL} token={token} />
          )}
        </div>

        {/* Bottom Nav bar */}
        <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} unreadCount={unreadCount} />
      </div>
    </main>
  );
}
