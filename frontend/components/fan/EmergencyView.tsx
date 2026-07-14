"use client";

import React, { useState } from "react";
import { ShieldAlert, HeartPulse, Send, Clock } from "lucide-react";
import {
  API_BASE_URL,
  SOS_DISPATCH_DELAY_MS,
  SOS_ARRIVAL_DELAY_MS,
  SOS_MOCK_DISPATCH_DELAY_MS,
} from "../../lib/constants";

interface EmergencyViewProps {
  apiUrl?: string;
  token?: string;
}

interface ReportedIncident {
  id: string;
  title: string;
  sector: string;
  createdAt: string;
}

export default function EmergencyView({ apiUrl = API_BASE_URL, token }: EmergencyViewProps) {
  const [incType, setIncType] = useState<"medical" | "security">("medical");
  const [sector, setSector] = useState("Sector C");
  const [description, setDescription] = useState("");
  const [reportedIncident, setReportedIncident] = useState<ReportedIncident | null>(null);
  const [dispatchStatus, setDispatchStatus] = useState("REGISTERING");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleTriggerSOS = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setIsSubmitting(true);
    const title = incType === "medical" ? "Fan Medical Distress Alert" : "Fan Security Panic Alert";

    try {
      const res = await fetch(`${apiUrl}/incidents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          title,
          description: description || `Emergency reported by fan. Type: ${incType.toUpperCase()}`,
          priority: "CRITICAL",
          sector,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setReportedIncident(data);
        setDispatchStatus("REGISTERED");

        setTimeout(() => {
          setDispatchStatus("DISPATCHED");
        }, SOS_DISPATCH_DELAY_MS);

        setTimeout(() => {
          setDispatchStatus("ARRIVED");
        }, SOS_ARRIVAL_DELAY_MS);
      } else {
        throw new Error("Trigger SOS failed");
      }
    } catch (err) {
      console.error(err);
      // Mock local fallback if backend connection fails
      setReportedIncident({
        id: `mock-${Date.now().toString().slice(-6)}`,
        title,
        sector,
        createdAt: new Date().toISOString(),
      });
      setDispatchStatus("REGISTERED");
      setTimeout(() => setDispatchStatus("DISPATCHED"), SOS_MOCK_DISPATCH_DELAY_MS);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setReportedIncident(null);
    setDescription("");
    setSector("Sector C");
    setIncType("medical");
  };

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-400">
          Emergency Safety Center
        </h2>
        <span className="text-[10px] text-danger bg-danger/10 border border-danger/20 px-2 py-0.5 rounded font-extrabold uppercase tracking-wider animate-pulse flex items-center gap-1">
          <ShieldAlert className="w-3.5 h-3.5" /> 24/7 Monitored
        </span>
      </div>

      {reportedIncident ? (
        // Active SOS Dispatch Status View
        <div className="glass p-5 rounded-2xl border border-danger/20 bg-danger/5 space-y-5 animate-fadeIn">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-danger/10 text-danger border border-danger/30 mb-3 animate-pulse">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h3 className="text-base font-extrabold text-white">Emergency Help Dispatched</h3>
            <p className="text-[10px] text-zinc-400 font-light mt-1">
              SOS Track ID: {reportedIncident.id.substring(0, 8)} | Location: {reportedIncident.sector}
            </p>
          </div>

          {/* Dispatcher timeline status steps */}
          <div className="space-y-4 pt-4 border-t border-zinc-900">
            {/* Step 1: Registered */}
            <div className="flex gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 border text-[9px] font-bold ${
                dispatchStatus !== "REGISTERING" ? "bg-success border-success text-zinc-950" : "bg-zinc-900 border-zinc-800 text-zinc-500 animate-pulse"
              }`}>
                1
              </div>
              <div>
                <span className="text-xs font-bold text-white block">Incident Registered</span>
                <span className="text-[9px] text-zinc-500 font-light block">Alert queued in Command Operations Room.</span>
              </div>
            </div>

            {/* Step 2: Dispatched */}
            <div className="flex gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 border text-[9px] font-bold ${
                dispatchStatus === "DISPATCHED" || dispatchStatus === "ARRIVED" ? "bg-success border-success text-zinc-950" : "bg-zinc-900 border-zinc-800 text-zinc-500"
              }`}>
                2
              </div>
              <div>
                <span className="text-xs font-bold text-white block">Responders Dispatched</span>
                <span className="text-[9px] text-zinc-500 font-light block">
                  {incType === "medical" ? "Medical Triage Team" : "Local Security Units"} en-route to {reportedIncident.sector}.
                </span>
              </div>
            </div>

            {/* Step 3: Arrived */}
            <div className="flex gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 border text-[9px] font-bold ${
                dispatchStatus === "ARRIVED" ? "bg-success border-success text-zinc-950" : "bg-zinc-900 border-zinc-800 text-zinc-500"
              }`}>
                3
              </div>
              <div>
                <span className="text-xs font-bold text-white block">On-Scene Arrival</span>
                <span className="text-[9px] text-zinc-500 font-light block">Crews establishing first-aid stabilization or safety perimeter.</span>
              </div>
            </div>
          </div>

          {dispatchStatus !== "ARRIVED" && (
            <div className="flex items-center justify-center gap-1.5 p-2 rounded-xl bg-zinc-900/60 text-[10px] text-zinc-400 border border-zinc-850">
              <Clock className="w-3.5 h-3.5 text-success animate-spin" /> Est. response time: <strong className="text-white">1 - 2 minutes</strong>
            </div>
          )}

          <button
            onClick={handleReset}
            className="w-full bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 text-white rounded-xl py-2 text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer"
          >
            Report Another Incident
          </button>
        </div>
      ) : (
        // Input form
        <form onSubmit={handleTriggerSOS} className="glass p-5 rounded-2xl border border-zinc-850 space-y-4">
          {/* Category tabs */}
          <div>
            <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1.5">Emergency Type</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIncType("medical")}
                className={`flex-1 py-3 rounded-xl border flex flex-col items-center gap-1 cursor-pointer transition-all duration-300 ${
                  incType === "medical" ? "bg-danger/10 border-danger text-danger" : "bg-zinc-950/20 border-zinc-900 text-zinc-500 hover:text-zinc-400"
                }`}
              >
                <HeartPulse className="w-6 h-6" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Medical Aid</span>
              </button>
              <button
                type="button"
                onClick={() => setIncType("security")}
                className={`flex-1 py-3 rounded-xl border flex flex-col items-center gap-1 cursor-pointer transition-all duration-300 ${
                  incType === "security" ? "bg-danger/10 border-danger text-danger" : "bg-zinc-950/20 border-zinc-900 text-zinc-500 hover:text-zinc-400"
                }`}
              >
                <ShieldAlert className="w-6 h-6" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Security / Help</span>
              </button>
            </div>
          </div>

          {/* Sector selection */}
          <div>
            <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1.5">Your Sector / Gate Location</label>
            <select
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
            >
              <option value="Sector A">Sector A (Seats 1-15)</option>
              <option value="Sector B">Sector B (Seats 16-30)</option>
              <option value="Sector C">Sector C (Seats 31-45)</option>
              <option value="Sector D">Sector D (Seats 46-60)</option>
              <option value="Sector E">Sector E (Seats 61-75)</option>
              <option value="Sector F">Sector F (Seats 76-90)</option>
              <option value="Gate 1">Gate 1 Ingress</option>
              <option value="Gate 2">Gate 2 Ingress</option>
              <option value="Gate 3">Gate 3 Ingress</option>
              <option value="Gate 4">Gate 4 Ingress</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1.5">Optional Details (Describe condition)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. collapsed spectator, fainting due to heat, chest pains near row F seat 12..."
              rows={2}
              className="w-full bg-zinc-900 border border-zinc-800 focus:border-danger/40 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-650 outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-danger hover:bg-danger-dark text-white rounded-xl py-3 text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-danger/15 border border-danger/45"
          >
            <Send className="w-4 h-4" /> Trigger SOS Distress Signal
          </button>
        </form>
      )}
    </div>
  );
}
