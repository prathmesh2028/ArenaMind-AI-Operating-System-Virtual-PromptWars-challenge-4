"use client";

import React, { useState, useEffect, useRef } from "react";
import { Bot, Send, User, Sparkles, Volume2 } from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
}

interface CopilotViewProps {
  apiUrl?: string;
  token?: string;
  activeTaskTitle?: string;
}

export default function CopilotView({ apiUrl = "http://localhost:8000", token, activeTaskTitle }: CopilotViewProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      sender: "bot",
      text: "I am the Volunteer Copilot Agent. Tell me which sector or task you are working on, and I will prepare a translation brief, crowd density waypoints checklist, or safety procedures outline.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Trigger helper prompt when volunteer has an active task assigned
  useEffect(() => {
    if (activeTaskTitle) {
      setMessages((prev) => [
        ...prev,
        {
          id: `task-alert-${Date.now()}`,
          sender: "bot",
          text: `🚨 **Task Alert Context Activated**: I see you have been assigned to: "${activeTaskTitle}". Ask me for the operational brief or translation phrases for this sector!`,
        },
      ]);
    }
  }, [activeTaskTitle]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userText = inputValue;
    setInputValue("");
    setIsTyping(true);

    const userMsg: Message = { id: `u-${Date.now()}`, sender: "user", text: userText };
    setMessages((prev) => [...prev, userMsg]);

    const botMsgId = `b-${Date.now()}`;
    const initialBot: Message = { id: botMsgId, sender: "bot", text: "" };
    setMessages((prev) => [...prev, initialBot]);

    try {
      const response = await fetch(`${apiUrl}/copilot/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          agent_id: "volunteer",
          message: userText,
          context: activeTaskTitle ? { active_task: activeTaskTitle } : undefined,
        }),
      });

      if (!response.ok) throw new Error();

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let streamed = "";

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          streamed += decoder.decode(value);

          setMessages((prev) =>
            prev.map((m) => (m.id === botMsgId ? { ...m, text: streamed } : m))
          );
        }
      }
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botMsgId
            ? {
                ...m,
                text: "For crowd control tasks: physically direct spectators into parallel turnstile check-in rows, maintain positive wayfinding directions, and keep exit pathways fully clear. Complete the task on your board once resolved.",
              }
            : m
        )
      );
    } finally {
      setIsTyping(false);
    }
  };

  const speakText = (text: string) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const clean = text.replace(/\*\*|\[|\]/g, "");
      const utterance = new SpeechSynthesisUtterance(clean);
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="glass p-5 rounded-2xl border border-zinc-850 h-[380px] flex flex-col overflow-hidden relative">
      <div className="flex justify-between items-center pb-3 border-b border-zinc-900 mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-warning animate-pulse" />
          <h3 className="text-xs font-bold text-white">AI Volunteer Advisor</h3>
        </div>
        <span className="text-[9px] text-zinc-500 font-mono">Volunteer Agent</span>
      </div>

      {/* Message logs */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {messages.map((m) => (
          <div key={m.id} className={`flex gap-3.5 ${m.sender === "user" ? "justify-end" : "justify-start"}`}>
            {m.sender === "bot" && (
              <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-850 flex items-center justify-center text-warning shrink-0 mt-0.5">
                <Bot className="w-4.5 h-4.5" />
              </div>
            )}
            <div className={`p-3 rounded-2xl max-w-[250px] text-xs leading-relaxed font-light ${
              m.sender === "user" ? "bg-warning text-zinc-950 rounded-tr-none font-bold" : "bg-zinc-900/60 border border-zinc-850 text-zinc-200 rounded-tl-none whitespace-pre-wrap"
            }`}>
              {m.text || (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
              )}
              {m.sender === "bot" && m.text && (
                <button
                  onClick={() => speakText(m.text)}
                  className="mt-2 block text-[9px] font-bold uppercase tracking-wider text-warning hover:text-warning-light cursor-pointer"
                >
                  <Volume2 className="w-3.5 h-3.5 inline-block mr-1" /> Read text
                </button>
              )}
            </div>
            {m.sender === "user" && (
              <div className="w-8 h-8 rounded-lg bg-warning/20 border border-warning/30 flex items-center justify-center text-warning shrink-0 mt-0.5">
                <User className="w-4.5 h-4.5" />
              </div>
            )}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSendMessage} className="flex gap-2 shrink-0">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isTyping}
          placeholder="Ask for checklists, instructions, translations..."
          className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-warning/50 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-550 outline-none transition-all duration-300"
        />
        <button
          type="submit"
          disabled={!inputValue.trim() || isTyping}
          className="bg-warning text-zinc-950 rounded-xl px-4 flex items-center justify-center transition-all duration-300 disabled:opacity-40 cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
