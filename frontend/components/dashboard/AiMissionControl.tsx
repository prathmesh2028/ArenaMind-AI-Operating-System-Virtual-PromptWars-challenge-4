"use client";

import React, { useState, useEffect, useRef } from "react";
import { Send, Bot, Shield, Users, Heart, Zap, Truck, Sparkles, User, Accessibility } from "lucide-react";
import type { ChatMessage } from "../../lib/types";
import { API_BASE_URL } from "../../lib/constants";

interface Agent {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  badgeStyle: string;
}

interface AiMissionControlProps {
  apiUrl?: string;
  token?: string;
}

export default function AiMissionControl({ apiUrl = API_BASE_URL, token }: AiMissionControlProps) {
  const [activeAgent, setActiveAgent] = useState("executive");
  const [messages, setMessages] = useState<Record<string, ChatMessage[]>>({
    executive: [
      {
        id: "init",
        sender: "bot",
        text: "I am the Executive Insights Copilot. I analyze the stadium telemetry to provide macro operational summaries and incident alerts. How can I assist you with the FIFA operations brief?",
        timestamp: new Date(),
      },
    ],
  });
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const agents: Agent[] = [
    {
      id: "executive",
      name: "Executive Insights",
      icon: <Sparkles className="w-4 h-4" />,
      description: "Macro status updates, system health anomalies, and strategic mitigation matrix rules logs.",
      badgeStyle: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    },
    {
      id: "crowd",
      name: "Crowd Intelligence",
      icon: <Users className="w-4 h-4" />,
      description: "Ingress waves monitoring, sector flow patterns, gate check-in congestion, and signages reroutes.",
      badgeStyle: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    },
    {
      id: "volunteer",
      name: "Volunteer Copilot",
      icon: <Bot className="w-4 h-4" />,
      description: " Roster tracking, shift tasks list assignments, check-in delays, and crew routing guidance.",
      badgeStyle: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    },
    {
      id: "security",
      name: "Security Command",
      icon: <Shield className="w-4 h-4" />,
      description: "Perimeter breach logs, lockups coordination, disruptive fans containment, and staff advisories.",
      badgeStyle: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    },
    {
      id: "medical",
      name: "Medical Response",
      icon: <Heart className="w-4 h-4" />,
      description: "Heat index stress warnings, hydration tent activations, and paramedic dispatch coordination.",
      badgeStyle: "bg-rose-600/10 text-rose-500 border-rose-600/20",
    },
    {
      id: "transportation",
      name: "Transit Logistics",
      icon: <Truck className="w-4 h-4" />,
      description: "Shuttle and train GPS fleet trackers, route delay warnings, and terminal queue congestion.",
      badgeStyle: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    },
    {
      id: "sustainability",
      name: "Energy & Carbon",
      icon: <Zap className="w-4 h-4" />,
      description: "Power grids load monitoring, solar offset generation tracking, and Carbon offset reporting.",
      badgeStyle: "bg-warning/10 text-warning border-warning/20",
    },
    {
      id: "accessibility",
      name: "Accessibility guide",
      icon: <Accessibility className="w-4 h-4" />,
      description: "Elevators, companion seats, sensory rooms, and wheelchair waypoint guidance.",
      badgeStyle: "bg-teal-500/10 text-teal-400 border-teal-500/20",
    },
  ];

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Lazy-initialize chat logs for newly opened agents
  useEffect(() => {
    if (!messages[activeAgent]) {
      const selectedAgent = agents.find((a) => a.id === activeAgent);
      setMessages((prev) => ({
        ...prev,
        [activeAgent]: [
          {
            id: `init-${activeAgent}`,
            sender: "bot",
            text: `I am the ArenaMind ${selectedAgent?.name} Agent. ${selectedAgent?.description} How can I assist you with this subsystem today?`,
            timestamp: new Date(),
          },
        ],
      }));
    }
  }, [activeAgent]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userText = inputValue;
    setInputValue("");
    setIsTyping(true);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: new Date(),
    };

    // Add user message to state
    setMessages((prev) => ({
      ...prev,
      [activeAgent]: [...(prev[activeAgent] || []), userMessage],
    }));

    // Create an empty bot message to stream into
    const botMsgId = `bot-${Date.now()}`;
    const initialBotMessage: ChatMessage = {
      id: botMsgId,
      sender: "bot",
      text: "",
      timestamp: new Date(),
    };

    setMessages((prev) => ({
      ...prev,
      [activeAgent]: [...(prev[activeAgent] || []), initialBotMessage],
    }));

    try {
      const chatEndpoint = `${apiUrl}/copilot/chat`;
      const response = await fetch(chatEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          agent_id: activeAgent,
          message: userText,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to stream chat explanation");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let streamedText = "";

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          streamedText += chunk;

          // Update messages in-place
          setMessages((prev) => {
            const list = prev[activeAgent] || [];
            return {
              ...prev,
              [activeAgent]: list.map((msg) =>
                msg.id === botMsgId ? { ...msg, text: streamedText } : msg
              ),
            };
          });
        }
      }
    } catch (err) {
      console.error(err);
      // Fallback on request failure
      setMessages((prev) => {
        const list = prev[activeAgent] || [];
        return {
          ...prev,
          [activeAgent]: list.map((msg) =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  text: "**[Error]** Failed to contact the AI engine. Ensure that the backend FastAPI server is running on port 8000.",
                }
              : msg
          ),
        };
      });
    } finally {
      setIsTyping(false);
    }
  };

  const currentAgent = agents.find((a) => a.id === activeAgent) || agents[0];
  const chatMessages = messages[activeAgent] || [];

  return (
    <div className="glass rounded-2xl p-6 flex flex-col lg:flex-row gap-6 h-[500px] overflow-hidden">
      {/* Agents Selection Panel */}
      <div className="lg:w-1/3 flex flex-col border-b lg:border-b-0 lg:border-r border-zinc-800 pb-4 lg:pb-0 lg:pr-6 h-1/3 lg:h-full overflow-y-auto">
        <h3 className="text-xs font-semibold tracking-wider text-zinc-500 uppercase mb-4 flex items-center gap-1.5 shrink-0">
          <Bot className="w-4 h-4 text-primary animate-pulse" />
          Specialized Gemini Agents
        </h3>
        <div className="space-y-1.5 flex-1 pr-1">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setActiveAgent(agent.id)}
              className={`w-full flex items-center gap-3 p-2.5 rounded-xl border text-left transition-all duration-300 ${
                activeAgent === agent.id
                  ? "bg-zinc-900 border-primary text-white shadow-[0_0_10px_rgba(99,102,241,0.15)]"
                  : "bg-zinc-950/20 border-zinc-900/60 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800"
              }`}
            >
              <div className={`p-2 rounded-lg border ${
                activeAgent === agent.id ? "bg-primary/20 border-primary/30 text-primary" : "bg-zinc-900 border-zinc-800 text-zinc-400"
              }`}>
                {agent.icon}
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-bold truncate">{agent.name}</div>
                <div className="text-[10px] text-zinc-500 font-light truncate mt-0.5">{agent.description}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Console */}
      <div className="flex-1 flex flex-col justify-between h-2/3 lg:h-full overflow-hidden">
        {/* Agent Info bar */}
        <div className="flex justify-between items-center pb-3 border-b border-zinc-850 mb-3 shrink-0">
          <div>
            <span className={`px-2.5 py-0.5 rounded-full border text-[9px] font-bold tracking-wider uppercase inline-flex items-center gap-1.5 ${currentAgent.badgeStyle}`}>
              {currentAgent.icon}
              {currentAgent.name} Active
            </span>
          </div>
          <span className="text-[10px] text-zinc-500 font-light italic">
            Streaming Context Mode
          </span>
        </div>

        {/* Message Log */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4 scroll-smooth">
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.sender === "bot" && (
                <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-primary shrink-0 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div className={`p-3.5 rounded-2xl max-w-md text-xs leading-relaxed font-light ${
                msg.sender === "user"
                  ? "bg-primary border border-primary-dark/40 text-white rounded-tr-none"
                  : "bg-zinc-900 border border-zinc-800/80 text-zinc-200 rounded-tl-none whitespace-pre-wrap"
              }`}>
                {msg.text || (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                )}
              </div>
              {msg.sender === "user" && (
                <div className="w-8 h-8 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Action input bar */}
        <form onSubmit={handleSendMessage} className="flex gap-2 shrink-0">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isTyping}
            placeholder={`Ask the ${currentAgent.name} agent...`}
            className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-primary/60 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 outline-none transition-all duration-300"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className="bg-primary hover:bg-primary-dark text-white rounded-xl px-4 py-2.5 flex items-center justify-center transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
