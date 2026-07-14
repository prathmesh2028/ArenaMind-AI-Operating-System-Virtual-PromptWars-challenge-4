"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Globe, Accessibility, Send, Bot, Volume2 } from "lucide-react";
import type { ChatMessage } from "../../lib/types";
import { API_BASE_URL } from "../../lib/constants";
import { speakText } from "../../lib/utils";

interface AssistantViewProps {
  apiUrl?: string;
  token?: string;
}

export default function AssistantView({ apiUrl = API_BASE_URL, token }: AssistantViewProps) {
  const [activeMode, setActiveMode] = useState<"voice" | "translation" | "accessibility">("voice");

  // Voice Assistant states
  const [isListening, setIsListening] = useState(false);
  const [voiceQuery, setVoiceQuery] = useState("");
  const [voiceResponse, setVoiceResponse] = useState("Click the microphone to start asking questions about tickets, food, gates, or bathroom directions.");
  const [audioPulsing, setAudioPulsing] = useState(false);

  // Translation states
  const [transInput, setTransInput] = useState("");
  const [selectedLang, setSelectedLang] = useState("es");
  const [transOutput, setTransOutput] = useState("");

  // Accessibility Chat states
  const [accMessages, setAccMessages] = useState<ChatMessage[]>([
    { id: "1", sender: "bot", text: "Welcome to Stadium Accessibility Services. I can guide you on wheelchair ramps, elevator sectors, sensory booths, and special headsets. Ask me any assistance questions." }
  ]);
  const [accInput, setAccInput] = useState("");
  const [accTyping, setAccTyping] = useState(false);

  // Web Speech API refs
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    // Initialize Web Speech Recognition
    if (typeof window !== "undefined") {
      const SpeechRecognitionCtor =
        (window as unknown as { SpeechRecognition?: typeof SpeechRecognition }).SpeechRecognition ??
        (window as unknown as { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition;
      if (SpeechRecognitionCtor) {
        const recog = new SpeechRecognitionCtor();
        recog.continuous = false;
        recog.interimResults = false;
        recog.lang = "en-US";

        recog.onstart = () => {
          setIsListening(true);
          setAudioPulsing(true);
          setVoiceQuery("Listening...");
        };

        recog.onresult = async (event: SpeechRecognitionEvent) => {
          const transcript = event.results[0][0].transcript;
          setVoiceQuery(`"${transcript}"`);
          await processVoiceCommand(transcript);
        };

        recog.onerror = (err: SpeechRecognitionErrorEvent) => {
          console.error("Speech Recognition Error:", err);
          setIsListening(false);
          setAudioPulsing(false);
          setVoiceQuery("Failed to record audio. Try typing in accessibility chat.");
        };

        recog.onend = () => {
          setIsListening(false);
          setAudioPulsing(false);
        };

        recognitionRef.current = recog;
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleToggleVoice = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.start();
      } else {
        // Mock fallback if Web Speech isn't supported/permitted
        setIsListening(true);
        setAudioPulsing(true);
        setVoiceQuery("Listening (Mock)...");
        setTimeout(async () => {
          const mockPhrases = [
            "Where is Gate 2?",
            "Where are the elevators?",
            "What is the heat index today?",
            "Show me the nearest food stand."
          ];
          const chosen = mockPhrases[Math.floor(Math.random() * mockPhrases.length)];
          setVoiceQuery(`"${chosen}"`);
          setIsListening(false);
          setAudioPulsing(false);
          await processVoiceCommand(chosen);
        }, 3000);
      }
    }
  };



  const processVoiceCommand = async (query: string) => {
    setVoiceResponse("Generating explanation...");
    try {
      const response = await fetch(`${apiUrl}/copilot/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          agent_id: "crowd",
          message: `Respond briefly to this fan question: ${query}`,
        }),
      });

      if (!response.ok) throw new Error();

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let completeText = "";

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          completeText += decoder.decode(value);
        }
      }

      setVoiceResponse(completeText);
      speakText(completeText);
    } catch {
      // Simple default local response fallback
      const reply = `I located details for you: Access turnstiles at Gate 2 and Gate 5 are fully open. Elevators are situated on the concourse level at Sector A and E. Let me know if you need paramedic mapping.`;
      setVoiceResponse(reply);
      speakText(reply);
    }
  };

  // Translation handler
  const handleTranslate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transInput.trim()) return;

    setTransOutput("Translating...");

    // Mock/Direct Translation Logic
    setTimeout(() => {
      const dict: Record<string, Record<string, string>> = {
        es: {
          "where is my seat": "Dónde está mi asiento?",
          "where are the bathrooms": "Dónde están los baños?",
          "i need medical assistance": "Necesito asistencia médica.",
          "how long is the gate queue": "Cuánto dura la fila en la puerta?",
          "thank you": "Gracias"
        },
        pt: {
          "where is my seat": "Onde fica o meu assento?",
          "where are the bathrooms": "Onde ficam os banheiros?",
          "i need medical assistance": "Preciso de ajuda médica.",
          "how long is the gate queue": "Quanto tempo dura a fila do portão?",
          "thank you": "Obrigado"
        },
        fr: {
          "where is my seat": "Où est mon siège?",
          "where are the bathrooms": "Où sont les toilettes?",
          "i need medical assistance": "J'ai besoin d'une assistance médicale.",
          "how long is the gate queue": "Combien de temps dure la file d'attente à la porte?",
          "thank you": "Merci"
        }
      };

      const key = transInput.toLowerCase().trim().replace(/[?.!]/g, "");
      const langDict = dict[selectedLang];
      let translated = "";
      if (langDict && langDict[key]) {
        translated = langDict[key];
      } else {
        // Basic template translation fallback generator
        if (selectedLang === "es") translated = `[Traducido] ${transInput} (Traducido al Español)`;
        else if (selectedLang === "pt") translated = `[Traduzido] ${transInput} (Traduzido para o Português)`;
        else translated = `[Traduit] ${transInput} (Traduit en Français)`;
      }

      setTransOutput(translated);
      speakText(translated);
    }, 800);
  };

  // Accessibility Chat handler
  const handleSendAccMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accInput.trim() || accTyping) return;

    const userText = accInput;
    setAccInput("");
    setAccTyping(true);

    const userMsg: ChatMessage = { id: `u-${Date.now()}`, sender: "user", text: userText };
    setAccMessages((prev) => [...prev, userMsg]);

    const botMsgId = `b-${Date.now()}`;
    const initialBot: ChatMessage = { id: botMsgId, sender: "bot", text: "" };
    setAccMessages((prev) => [...prev, initialBot]);

    try {
      const response = await fetch(`${apiUrl}/copilot/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          agent_id: "accessibility",
          message: userText,
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

          setAccMessages((prev) =>
            prev.map((m) => (m.id === botMsgId ? { ...m, text: streamed } : m))
          );
        }
      }
    } catch {
      setAccMessages((prev) =>
        prev.map((m) =>
          m.id === botMsgId
            ? { ...m, text: "Elevators are located on the Concourse levels in Sectors A, C, and E. Wheelchair accessible ramps are open at the North and South main entrances." }
            : m
        )
      );
    } finally {
      setAccTyping(false);
    }
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Toggle View Header */}
      <div className="flex gap-2 p-1 rounded-xl bg-zinc-900 border border-zinc-800">
        <button
          onClick={() => setActiveMode("voice")}
          className={`flex-1 py-2 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all duration-300 ${
            activeMode === "voice" ? "bg-zinc-800 text-success" : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Voice Control
        </button>
        <button
          onClick={() => setActiveMode("translation")}
          className={`flex-1 py-2 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all duration-300 ${
            activeMode === "translation" ? "bg-zinc-800 text-success" : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Translator
        </button>
        <button
          onClick={() => setActiveMode("accessibility")}
          className={`flex-1 py-2 text-[10px] font-bold tracking-wider uppercase rounded-lg transition-all duration-300 ${
            activeMode === "accessibility" ? "bg-zinc-800 text-success" : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Accessibility
        </button>
      </div>

      {activeMode === "voice" ? (
        // Voice Assistant view
        <div className="glass p-6 rounded-2xl border border-zinc-850 flex flex-col items-center text-center space-y-6">
          <div className="relative">
            {/* Audio pulsation animation rings */}
            {audioPulsing && (
              <>
                <div className="absolute inset-0 bg-success/20 rounded-full animate-ping scale-150" />
                <div className="absolute inset-0 bg-success/15 rounded-full animate-pulse scale-125" />
              </>
            )}

            <button
              onClick={handleToggleVoice}
              className={`w-20 h-20 rounded-full border-4 flex items-center justify-center relative cursor-pointer shadow-lg shadow-success/10 transition-all duration-300 ${
                isListening
                  ? "bg-danger border-danger/45 text-white"
                  : "bg-success border-success/45 text-white hover:scale-105"
              }`}
            >
              {isListening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
            </button>
          </div>

          <div>
            <div className="text-[10px] font-bold tracking-wider uppercase text-zinc-500 mb-2">Query Input</div>
            <div className="text-sm font-bold text-white max-w-xs min-h-6 flex items-center justify-center italic">
              {voiceQuery || '"What are the closest gate entry points?"'}
            </div>
          </div>

          <div className="w-full pt-4 border-t border-zinc-900 text-left">
            <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 block mb-2 flex items-center gap-1">
              <Bot className="w-3.5 h-3.5" /> AI Response Voiceover
            </span>
            <p className="text-xs text-zinc-300 font-light leading-relaxed min-h-16">
              {voiceResponse}
            </p>
            {voiceResponse && voiceResponse !== "Generating explanation..." && (
              <button
                onClick={() => speakText(voiceResponse)}
                className="mt-3 inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-success hover:text-success-light cursor-pointer"
              >
                <Volume2 className="w-3.5 h-3.5" /> Read Aloud
              </button>
            )}
          </div>
        </div>
      ) : activeMode === "translation" ? (
        // Translation View
        <div className="glass p-5 rounded-2xl border border-zinc-850 space-y-4">
          <form onSubmit={handleTranslate} className="space-y-4">
            <div>
              <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1">Select Language</label>
              <select
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
              >
                <option value="es">Spanish (Español)</option>
                <option value="pt">Portuguese (Português)</option>
                <option value="fr">French (Français)</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-zinc-500 font-semibold uppercase block mb-1">Translate English Text</label>
              <input
                type="text"
                required
                value={transInput}
                onChange={(e) => setTransInput(e.target.value)}
                placeholder="e.g. where are the bathrooms?"
                className="w-full bg-zinc-900 border border-zinc-800 focus:border-success/50 rounded-xl px-3 py-2.5 text-xs text-white placeholder-zinc-650 outline-none"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-success hover:bg-success-dark text-white rounded-xl py-2.5 text-xs font-bold uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-success/15"
            >
              <Globe className="w-4.5 h-4.5" /> Translate & Speak
            </button>
          </form>

          {transOutput && (
            <div className="p-3.5 rounded-xl bg-zinc-950/40 border border-zinc-900 animate-fadeIn">
              <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">Translation Result</span>
              <div className="text-xs font-extrabold text-white flex justify-between items-center">
                <span>{transOutput}</span>
                <button
                  onClick={() => speakText(transOutput)}
                  className="p-1 bg-zinc-900 rounded hover:bg-zinc-850 hover:text-success text-zinc-400"
                >
                  <Volume2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        // Accessibility Assistant view
        <div className="glass p-5 rounded-2xl border border-zinc-850 h-[380px] flex flex-col overflow-hidden">
          <div className="flex items-center gap-2 pb-3 border-b border-zinc-900 mb-3 shrink-0">
            <Accessibility className="w-5 h-5 text-success animate-pulse" />
            <div>
              <h3 className="text-xs font-bold text-white">Accessibility Services</h3>
              <p className="text-[9px] text-zinc-500 font-light mt-0.5">Assisting neurodivergent and disabled fans</p>
            </div>
          </div>

          {/* Accessibility message log */}
          <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
            {accMessages.map((m) => (
              <div key={m.id} className={`flex gap-2.5 ${m.sender === "user" ? "justify-end" : "justify-start"}`}>
                {m.sender === "bot" && (
                  <div className="w-7 h-7 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-success shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}
                <div className={`p-3 rounded-2xl max-w-[240px] text-[11px] leading-relaxed font-light ${
                  m.sender === "user" ? "bg-success text-white rounded-tr-none" : "bg-zinc-900 border border-zinc-850 text-zinc-200 rounded-tl-none"
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          {/* Chat input form */}
          <form onSubmit={handleSendAccMessage} className="flex gap-2 shrink-0">
            <input
              type="text"
              value={accInput}
              onChange={(e) => setAccInput(e.target.value)}
              disabled={accTyping}
              placeholder="Ask about ramps, elevators, sensory room..."
              className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-success/50 rounded-xl px-3 py-2 text-[11px] text-white outline-none"
            />
            <button
              type="submit"
              disabled={!accInput.trim() || accTyping}
              className="bg-success text-white rounded-xl px-3 flex items-center justify-center transition-all duration-300 disabled:opacity-40 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
