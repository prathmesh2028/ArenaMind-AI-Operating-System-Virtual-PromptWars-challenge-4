"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Smartphone, ArrowLeft, Bot, Signal, Wifi, WifiOff, RefreshCw, X, Radio } from "lucide-react";

// Import custom subviews
import BottomNav from "../../components/volunteer/BottomNav";
import TaskBoard from "../../components/volunteer/TaskBoard";
import ReportView from "../../components/volunteer/ReportView";
import MapView from "../../components/volunteer/MapView";
import CopilotView from "../../components/volunteer/CopilotView";

import { VolunteerTask } from "../../types/stadium";

const API_BASE_URL = "http://localhost:8000";
const WS_BASE_URL = "ws://localhost:8000";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  read: boolean;
  priority: string;
  type: string;
  created_at: string;
}

export default function VolunteerCopilot() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("tasks");
  const [wsConnected, setWsConnected] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  // Volunteer Data states
  const [tasks, setTasks] = useState<VolunteerTask[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  
  // Notification pop-up alerts
  const [alertMessage, setAlertMessage] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  // Authenticate as Volunteer on mount
  useEffect(() => {
    async function loginAsVolunteer() {
      try {
        setLoading(true);
        // Login as volunteer1
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: "volunteer1@fifa.com" }),
        });

        if (!res.ok) throw new Error("Volunteer auth failed");
        const data = await res.json();
        setToken(data.access_token);

        // Fetch initial values
        await syncData(data.access_token, false);
      } catch (err) {
        console.error("Volunteer login failed:", err);
        // Fallback to cache immediately if backend down
        setIsOffline(true);
        loadFromCache();
      } finally {
        setLoading(false);
      }
    }
    loginAsVolunteer();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Establish WebSocket connection when online
  useEffect(() => {
    if (!token || isOffline) {
      if (wsRef.current) {
        wsRef.current.close();
        setWsConnected(false);
      }
      return;
    }

    const socket = new WebSocket(`${WS_BASE_URL}/dashboard/ws`);
    wsRef.current = socket;

    socket.onopen = () => {
      setWsConnected(true);
      console.log("[WS] Volunteer Copilot connected to Event Bus");
    };

    socket.onmessage = (event) => {
      try {
        const rawEvent = JSON.parse(event.data);
        handleIncomingWsEvent(rawEvent);
      } catch (err) {
        console.error("WS error parsing:", err);
      }
    };

    socket.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [token, isOffline]);

  // Synchronize outbox when turning back online
  useEffect(() => {
    if (!isOffline && token) {
      syncOfflineOutbox();
    }
  }, [isOffline]);

  // Load datasets from LocalStorage
  const loadFromCache = () => {
    if (typeof window === "undefined") return;
    const cachedTasks = localStorage.getItem("volunteer_tasks");
    if (cachedTasks) {
      setTasks(JSON.parse(cachedTasks));
    }
    const cachedNotifs = localStorage.getItem("volunteer_notifications");
    if (cachedNotifs) {
      setNotifications(JSON.parse(cachedNotifs));
    }
  };

  // Sync data with backend REST APIs
  async function syncData(jwtToken: string, showBanner = true) {
    const headers = { Authorization: `Bearer ${jwtToken}` };
    try {
      // 1. Fetch my tasks
      const taskRes = await fetch(`${API_BASE_URL}/volunteer/tasks`, { headers });
      if (taskRes.ok) {
        const taskData = await taskRes.json();
        setTasks(taskData);
        localStorage.setItem("volunteer_tasks", JSON.stringify(taskData));
      }

      // 2. Fetch my notifications
      const notifRes = await fetch(`${API_BASE_URL}/volunteer/notifications`, { headers });
      if (notifRes.ok) {
        const notifData = await notifRes.json();
        setNotifications(notifData.notifications);
        localStorage.setItem("volunteer_notifications", JSON.stringify(notifData.notifications));
      }

      if (showBanner) {
        setAlertMessage("Synchronization completed. Active tasks updated.");
        dismissAlert();
      }
    } catch (err) {
      console.error("Failed to sync volunteer database:", err);
    }
  }

  // Handle incoming websocket dispatches
  function handleIncomingWsEvent(event: any) {
    const topic = event.topic || "";
    const payload = event.payload || {};

    // When operations raises a task dispatch warning (e.g. system notifies a volunteer)
    if (topic === "volunteer.position" && payload.volunteer_id === "V001") {
      // Re-trigger task fetch to show the newly assigned task
      if (token) syncData(token, false);
      
      setAlertMessage("New Dispatch: Check your board for a new assigned task!");
      dismissAlert();
    }

    else if (topic === "incident.resolved" && payload.volunteer_id === "V001") {
      // Mark local tasks related to this incident as completed
      setTasks((prev) => prev.filter((t) => t.incidentId !== payload.incident_id));
      setAlertMessage("Operations Alert: Incident has been resolved. You are cleared.");
      dismissAlert();
    }
  }

  const dismissAlert = () => {
    setTimeout(() => {
      setAlertMessage(null);
    }, 6000);
  };

  // SOS/Incident Report Dispatcher
  const handleReportIncident = async (incident: {
    title: string;
    description: string;
    priority: string;
    sector: string;
    photo?: string;
  }) => {
    if (isOffline) {
      // Save incident to offline outbox cache
      const outboxItem = {
        ...incident,
        id: `outbox-${Date.now()}`,
        timestamp: new Date().toISOString(),
      };
      const currentOutbox = JSON.parse(localStorage.getItem("volunteer_outbox") || "[]");
      const nextOutbox = [...currentOutbox, outboxItem];
      localStorage.setItem("volunteer_outbox", JSON.stringify(nextOutbox));

      setAlertMessage("Offline Alert: Issue queued in outbox. Switch online to sync.");
      dismissAlert();
    } else {
      // Post directly
      try {
        const res = await fetch(`${API_BASE_URL}/incidents`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: incident.title,
            description: incident.description,
            priority: incident.priority,
            sector: incident.sector,
          }),
        });

        if (res.ok) {
          setAlertMessage("Success: Incident reported live to Command Room.");
          dismissAlert();
        } else {
          throw new Error("REST post failed");
        }
      } catch (err) {
        console.error("SOS report failed:", err);
      }
    }
  };

  // Sync offline outbox to DB
  async function syncOfflineOutbox() {
    const outbox = JSON.parse(localStorage.getItem("volunteer_outbox") || "[]");
    if (outbox.length === 0) return;

    setAlertMessage("Syncing queued outbox incidents...");
    let successCount = 0;

    for (const item of outbox) {
      try {
        const res = await fetch(`${API_BASE_URL}/incidents`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: item.title,
            description: item.description,
            priority: item.priority,
            sector: item.sector,
          }),
        });
        if (res.ok) successCount++;
      } catch (err) {
        console.error("Outbox sync failed for item:", item, err);
      }
    }

    if (successCount > 0) {
      localStorage.setItem("volunteer_outbox", "[]");
      setAlertMessage(`Sync Done: ${successCount} outbox incidents sent successfully.`);
      dismissAlert();
      syncData(token, false);
    }
  }

  // Accept a PENDING task
  const handleAcceptTask = async (id: string) => {
    if (isOffline) {
      // Local state progression when offline
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, status: "ACCEPTED" } : t))
      );
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/volunteer/tasks/${id}/accept`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setTasks((prev) =>
          prev.map((t) => (t.id === id ? { ...t, status: "ACCEPTED" } : t))
        );
        addLocalTimelineEvent("Task accepted and dispatch chronometer started.", "warning");
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Complete an ACCEPTED task
  const handleCompleteTask = async (id: string) => {
    if (isOffline) {
      setTasks((prev) => prev.filter((t) => t.id !== id));
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/volunteer/tasks/${id}/complete`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setTasks((prev) => prev.filter((t) => t.id !== id));
        addLocalTimelineEvent("Task completed successfully. Redeployed to standby.", "success");
      }
    } catch (err) {
      console.error(err);
    }
  };

  function addLocalTimelineEvent(msg: string, priority: string) {
    const localNotif: NotificationItem = {
      id: `local-${Date.now()}`,
      title: "Task Progress Log",
      message: msg,
      read: false,
      priority: priority.toUpperCase(),
      type: "SYSTEM",
      created_at: new Date().toISOString(),
    };
    setNotifications((prev) => [localNotif, ...prev]);
  }

  const handleToggleOfflineMode = () => {
    const nextOffline = !isOffline;
    setIsOffline(nextOffline);
    if (nextOffline) {
      setAlertMessage("Switched to Offline Mode. Database reads cached.");
      loadFromCache();
    } else {
      setAlertMessage("Reconnected. Synchronizing dashboard datasets...");
      if (token) syncData(token, false);
    }
    dismissAlert();
  };

  const currentActiveTask = tasks.find((t) => t.status === "ACCEPTED") || tasks[0];
  const activeTaskTitle = currentActiveTask ? currentActiveTask.title : undefined;
  const activeTaskLocation = currentActiveTask ? currentActiveTask.description?.match(/Sector [A-F]|Gate [1-6]/)?.[0] || "Sector E" : "Sector E";
  const unreadCount = notifications.filter((n) => !n.read).length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 text-zinc-400">
        <Smartphone className="w-12 h-12 text-warning animate-bounce mb-4" />
        <div className="text-xs font-semibold tracking-widest uppercase animate-pulse">
          Starting Volunteer Copilot...
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center py-6 px-4">
      {/* Smartphone Frame viewport shell */}
      <div className="w-full max-w-md min-h-[750px] max-h-[850px] bg-zinc-950 rounded-[40px] border-[10px] border-zinc-900 overflow-hidden flex flex-col justify-between shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8)] relative">
        
        {/* Notch bezel */}
        <div className="absolute top-0 inset-x-0 h-6 bg-zinc-900 flex justify-center items-center z-45">
          <div className="w-24 h-4 bg-zinc-950 rounded-full" />
        </div>

        {/* Live Notification pop-up bar */}
        {alertMessage && (
          <div className="absolute top-8 inset-x-3 bg-warning/95 backdrop-blur border border-warning/30 text-zinc-950 rounded-2xl p-3.5 z-50 flex justify-between items-start shadow-xl animate-slideDown">
            <div className="flex-1 pr-3">
              <span className="text-[9px] bg-zinc-950/20 px-1.5 py-0.5 rounded font-extrabold uppercase tracking-wider block w-max mb-1.5">
                Copilot Brief
              </span>
              <p className="text-[11.5px] font-extrabold leading-normal">{alertMessage}</p>
            </div>
            <button
              onClick={() => setAlertMessage(null)}
              className="p-1 bg-zinc-950/10 hover:bg-zinc-950/20 rounded-lg text-zinc-950"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Portal Header */}
        <header className="border-b border-zinc-900 bg-zinc-950/70 pt-8 pb-3 px-5 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-1.5 rounded-lg bg-zinc-900 border border-zinc-850 text-zinc-400 hover:text-white"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
            </Link>
            <div>
              <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Signal className={`w-2.5 h-2.5 ${wsConnected ? "text-success" : "text-zinc-650"}`} />
                {wsConnected ? "OS Synchronized" : "OS Offline"}
              </span>
              <h1 className="text-xs font-black text-white uppercase tracking-wider mt-0.5">
                Volunteer Copilot
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Offline-Friendly Toggle Switch */}
            <button
              onClick={handleToggleOfflineMode}
              className={`p-1.5 rounded-lg border flex items-center justify-center transition-all duration-300 cursor-pointer ${
                isOffline
                  ? "bg-danger/10 border-danger/35 text-danger"
                  : "bg-zinc-900 border-zinc-850 text-zinc-400 hover:text-white"
              }`}
              title={isOffline ? "Go Online" : "Go Offline"}
            >
              {isOffline ? <WifiOff className="w-3.5 h-3.5" /> : <Wifi className="w-3.5 h-3.5" />}
            </button>
          </div>
        </header>

        {/* Main Content sheet */}
        <div className="flex-1 overflow-y-auto px-5 py-4 z-10 bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-950">
          {activeTab === "tasks" ? (
            <TaskBoard tasks={tasks} onAccept={handleAcceptTask} onComplete={handleCompleteTask} />
          ) : activeTab === "report" ? (
            <ReportView onReportIncident={handleReportIncident} isOffline={isOffline} />
          ) : activeTab === "map" ? (
            <MapView activeTaskLocation={activeTaskLocation} />
          ) : (
            <CopilotView apiUrl={API_BASE_URL} token={token} activeTaskTitle={activeTaskTitle} />
          )}
        </div>

        {/* Bottom Navigation */}
        <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} unreadCount={unreadCount} />
      </div>
    </main>
  );
}
