/**
 * Reusable Web Speech Recognition hook.
 *
 * Encapsulates the speech-recognition setup, start/stop toggling,
 * and mock fallback that was duplicated in AssistantView and ReportView.
 */
"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseSpeechRecognitionOptions {
  /** Callback invoked with the final transcript once speech recognition ends. */
  onResult: (transcript: string) => void;
  /** Language for recognition (default: "en-US"). */
  lang?: string;
}

interface UseSpeechRecognitionResult {
  /** Whether the microphone is currently listening. */
  isListening: boolean;
  /** Toggle listening on/off. Falls back to mock phrases if API unavailable. */
  toggleListening: () => void;
}

const MOCK_PHRASES = [
  "Where is Gate 2?",
  "Where are the elevators?",
  "What is the heat index today?",
  "Show me the nearest food stand.",
];

export function useSpeechRecognition({
  onResult,
  lang = "en-US",
}: UseSpeechRecognitionOptions): UseSpeechRecognitionResult {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any | null>(null);
  const onResultRef = useRef(onResult);

  // Sync callback ref to prevent stale closures
  useEffect(() => {
    onResultRef.current = onResult;
  }, [onResult]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const SpeechRecognitionCtor =
      (window as unknown as { SpeechRecognition?: any })
        .SpeechRecognition ??
      (window as unknown as { webkitSpeechRecognition?: any })
        .webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) return;

    const recog = new SpeechRecognitionCtor();
    recog.continuous = false;
    recog.interimResults = false;
    recog.lang = lang;

    recog.onstart = () => setIsListening(true);
    recog.onend = () => setIsListening(false);

    recog.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      onResultRef.current(transcript);
    };

    recog.onerror = (err: any) => {
      console.error("Speech Recognition Error:", err);
      setIsListening(false);
    };

    recognitionRef.current = recog;

    return () => {
      recog.stop();
      recognitionRef.current = null;
    };
  }, [lang]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    if (recognitionRef.current) {
      recognitionRef.current.start();
    } else {
      // Mock fallback when Web Speech API is not available
      setIsListening(true);
      setTimeout(() => {
        const chosen =
          MOCK_PHRASES[Math.floor(Math.random() * MOCK_PHRASES.length)];
        onResultRef.current(chosen);
        setIsListening(false);
      }, 2_000);
    }
  }, [isListening]);

  return { isListening, toggleListening };
}
