"use client";

import React, { useState, useEffect, useRef } from "react";
import { AlertCircle, Mic, MicOff, Camera, Send, X, CheckCircle } from "lucide-react";

interface ReportViewProps {
  onReportIncident: (incident: {
    title: string;
    description: string;
    priority: string;
    sector: string;
    photo?: string;
  }) => void;
  isOffline: boolean;
}

export default function ReportView({ onReportIncident, isOffline }: ReportViewProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [sector, setSector] = useState("Sector A");
  
  // Camera photo upload states
  const [photo, setPhoto] = useState<string | null>(null);
  
  // Voice transcription states
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recog = new SpeechRecognition();
        recog.continuous = false;
        recog.interimResults = false;
        recog.lang = "en-US";

        recog.onstart = () => {
          setIsListening(true);
        };

        recog.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setDescription((prev) => (prev ? `${prev} ${transcript}` : transcript));
        };

        recog.onerror = (err: any) => {
          console.error("Speech Recognition Error:", err);
          setIsListening(false);
        };

        recog.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recog;
      }
    }
  }, []);

  const handleToggleVoice = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.start();
      } else {
        // Mock fallback transcription
        setIsListening(true);
        setTimeout(() => {
          const mockPhrases = [
            "Concourse queue is spilling over turnstiles due to scanner delay.",
            "Debris blocking Sector D escalator pathway.",
            "Minor crowd altercation reported near Concession Section F.",
            "Elevator call button in Sector B is unresponsive."
          ];
          const chosen = mockPhrases[Math.floor(Math.random() * mockPhrases.length)];
          setDescription((prev) => (prev ? `${prev} ${chosen}` : chosen));
          setIsListening(false);
        }, 2000);
      }
    }
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      setPhoto(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !sector) return;

    onReportIncident({
      title,
      description,
      priority,
      sector,
      photo: photo || undefined,
    });

    // Reset Form
    setTitle("");
    setDescription("");
    setPriority("MEDIUM");
    setSector("Sector A");
    setPhoto(null);
  };

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-400">
          Report Field Incident
        </h2>
        {isOffline ? (
          <span className="text-[10px] bg-danger/10 border border-danger/20 text-danger px-2 py-0.5 rounded font-extrabold uppercase tracking-wider">
            Offline Cache Enabled
          </span>
        ) : (
          <span className="text-[10px] bg-success/10 border border-success/20 text-success px-2 py-0.5 rounded font-extrabold uppercase tracking-wider">
            OS Synced Live
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="glass p-5 rounded-2xl border border-zinc-850 space-y-4">
        {/* Title */}
        <div>
          <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1">Issue Title</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Concourse Crowding / Turnstile Delay"
            className="w-full bg-zinc-900 border border-zinc-800 focus:border-warning/50 rounded-xl px-3 py-2.5 text-xs text-white placeholder-zinc-650 outline-none"
          />
        </div>

        {/* Priority & Sector */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1">Sector</label>
            <select
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
            >
              <option value="Sector A">Sector A</option>
              <option value="Sector B">Sector B</option>
              <option value="Sector C">Sector C</option>
              <option value="Sector D">Sector D</option>
              <option value="Sector E">Sector E</option>
              <option value="Sector F">Sector F</option>
              <option value="Gate 1">Gate 1</option>
              <option value="Gate 2">Gate 2</option>
            </select>
          </div>
        </div>

        {/* Description & Speech input */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-[10px] text-zinc-500 font-semibold uppercase">Description details</label>
            <button
              type="button"
              onClick={handleToggleVoice}
              className={`inline-flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border transition-all duration-300 ${
                isListening
                  ? "bg-danger border-danger/30 text-white animate-pulse"
                  : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {isListening ? <MicOff className="w-3 h-3" /> : <Mic className="w-3 h-3" />}
              {isListening ? "Listening..." : "Dictate"}
            </button>
          </div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the incident in detail (escalator malfunction, crowd blockage, debris)..."
            rows={3}
            className="w-full bg-zinc-900 border border-zinc-800 focus:border-warning/40 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-650 outline-none resize-none"
          />
        </div>

        {/* Camera / Photo Upload section */}
        <div>
          <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1.5">Attach Photo Evidence</label>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 hover:border-warning/30 hover:bg-zinc-900/60 px-3.5 py-2.5 rounded-xl text-xs text-zinc-400 font-semibold uppercase tracking-wider cursor-pointer transition-all duration-300">
              <Camera className="w-4 h-4 text-warning" />
              <span>Camera Upload</span>
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                className="hidden"
              />
            </label>

            {photo && (
              <div className="relative w-14 h-14 rounded-lg overflow-hidden border border-zinc-800 shrink-0">
                <img src={photo} alt="Upload preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => setPhoto(null)}
                  className="absolute top-0.5 right-0.5 p-0.5 bg-zinc-950/80 rounded-full text-zinc-400 hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="w-full bg-warning hover:bg-warning-dark text-zinc-950 rounded-xl py-3 text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-warning/15 border border-warning/35"
        >
          <Send className="w-4 h-4" />
          {isOffline ? "Queue to Outbox" : "Submit Incident"}
        </button>
      </form>
    </div>
  );
}
