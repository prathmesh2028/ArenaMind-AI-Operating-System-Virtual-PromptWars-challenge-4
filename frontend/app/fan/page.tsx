"use client";

import React, { useState, useCallback } from "react";
import Link from "next/link";
import { Smartphone, ArrowLeft, Signal, X } from "lucide-react";

import BottomNav from "../../components/fan/BottomNav";
import HomeView from "../../components/fan/HomeView";
import FoodView from "../../components/fan/FoodView";
import AssistantView from "../../components/fan/AssistantView";
import EmergencyView from "../../components/fan/EmergencyView";

import type { ParkingItem, TransportItem, NotificationItem, SectorData } from "../../lib/types";
import { API_BASE_URL, FAN_EMAIL, ALERT_DISMISS_DELAY_MS } from "../../lib/constants";
import { useAuth } from "../../hooks/useAuth";
import { useWebSocket } from "../../hooks/useWebSocket";

export default function FanPortal() {
  const [activeTab, setActiveTab] = useState("home");

  // Live data states
  const [parkingLots, setParkingLots] = useState<ParkingItem[]>([]);
  const [transitVehicles, setTransitVehicles] = useState<TransportItem[]>([]);
  const [_sectors, setSectors] = useState<SectorData[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Flash banner notification popup
  const [incomingAlert, setIncomingAlert] = useState<string | null>(null);

  // Authenticate as FAN and fetch initial data
  const { token, loading } = useAuth(
    FAN_EMAIL,
    async (jwtToken: string) => {
      await fetchFanData(jwtToken);
    },
  );

  // WebSocket handler
  const handleWsMessage = useCallback(
    (rawEvent: { id: string; topic: string; timestamp?: string; payload: Record<string, unknown> }) => {
      handleIncomingWsEvent(rawEvent);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const { connected: wsConnected } = useWebSocket({
    token,
    onMessage: handleWsMessage,
  });

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

  function handleIncomingWsEvent(event: Record<string, unknown>) {
    const topic = (event.topic as string) || "";
    const payload = (event.payload as Record<string, unknown>) || {};

    if (topic === "parking.tick") {
      setParkingLots((prev) =>
        prev.map((lot) =>
          lot.name === (payload.lot as string)
            ? {
                ...lot,
                available_spots: payload.available as number,
                occupancy_pct: payload.pct_full as number,
                status: payload.status as string,
              }
            : lot,
        ),
      );
    } else if (topic === "transport.tick") {
      setTransitVehicles((prev) => {
        const route = payload.route as string;
        const exists = prev.some((v) => v.route === route);
        if (!exists) {
          return [
            ...prev,
            {
              route,
              type: payload.type as string,
              status: payload.status as string,
              current_stop: payload.current_stop as string,
              seats_available: 100 - (payload.occupancy_pct as number),
            },
          ];
        }
        return prev.map((v) =>
          v.route === route
            ? {
                ...v,
                status: payload.status as string,
                current_stop: payload.current_stop as string,
                seats_available: 100 - (payload.occupancy_pct as number),
              }
            : v,
        );
      });
    } else if (topic === "crowd.tick") {
      setSectors((prev) =>
        prev.map((sec) =>
          sec.sector === (payload.sector as string)
            ? {
                ...sec,
                density: payload.density as number,
                status: (payload.status as string) || sec.status,
              }
            : sec,
        ),
      );
    } else if (
      topic === "weather.heat_stress" ||
      topic === "crowd.density.critical" ||
      topic === "incident.resolved" ||
      topic === "gate.malfunction"
    ) {
      let alertMsg =
        (payload.message as string) || `System alert triggered on topic ${topic}`;
      if (topic === "incident.resolved") {
        alertMsg =
          "Safety Notice: Reported incident has been successfully resolved by field responders.";
      }
      setIncomingAlert(alertMsg);

      const localNotif: NotificationItem = {
        id: event.id as string,
        title: topic.replace(/\./g, " ").toUpperCase(),
        message: alertMsg,
        read: false,
        priority: "HIGH",
        type: "SYSTEM",
        created_at: new Date().toISOString(),
      };
      setNotifications((prev) => [localNotif, ...prev]);

      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
      }

      setTimeout(() => {
        setIncomingAlert(null);
      }, ALERT_DISMISS_DELAY_MS);
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
            <HomeView parkingLots={parkingLots} transitVehicles={transitVehicles} />
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
