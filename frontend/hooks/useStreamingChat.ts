/**
 * Reusable streaming-chat hook.
 *
 * Encapsulates the common pattern of:
 *  1. Adding a user message
 *  2. Creating an empty bot message
 *  3. Streaming the response body chunk-by-chunk into that message
 *  4. Handling errors with a fallback message
 *
 * Previously this ~60-line pattern was duplicated in AiMissionControl,
 * AssistantView (accessibility chat), and CopilotView.
 */
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { ChatMessage } from "../lib/types";

interface UseStreamingChatOptions {
  /** REST endpoint for the chat API. */
  apiUrl: string;
  /** JWT bearer token (optional; omitted header if empty). */
  token?: string;
  /** Agent identifier sent in the request body. */
  agentId: string;
  /** Initial greeting messages to seed the conversation. */
  initialMessages?: ChatMessage[];
  /** Fallback text displayed on network / API errors. */
  errorFallback?: string;
}

interface UseStreamingChatResult {
  messages: ChatMessage[];
  inputValue: string;
  setInputValue: React.Dispatch<React.SetStateAction<string>>;
  isTyping: boolean;
  handleSendMessage: (e: React.FormEvent) => Promise<void>;
  chatEndRef: React.MutableRefObject<HTMLDivElement | null>;
}

export function useStreamingChat({
  apiUrl,
  token,
  agentId,
  initialMessages = [],
  errorFallback = "An error occurred. Please try again.",
}: UseStreamingChatOptions): UseStreamingChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const inputValueRef = useRef(inputValue);
  const isTypingRef = useRef(isTyping);

  useEffect(() => {
    inputValueRef.current = inputValue;
  }, [inputValue]);

  useEffect(() => {
    isTypingRef.current = isTyping;
  }, [isTyping]);

  const handleSendMessage = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const currentInput = inputValueRef.current;
      if (!currentInput.trim() || isTypingRef.current) return;

      const userText = currentInput;
      setInputValue("");
      setIsTyping(true);

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        sender: "user",
        text: userText,
        timestamp: new Date(),
      };

      const botMsgId = `bot-${Date.now()}`;
      const initialBot: ChatMessage = {
        id: botMsgId,
        sender: "bot",
        text: "",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg, initialBot]);

      try {
        const response = await fetch(`${apiUrl}/copilot/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ agent_id: agentId, message: userText }),
        });

        if (!response.ok) throw new Error("Chat request failed");

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let streamed = "";

        if (reader) {
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            streamed += decoder.decode(value, { stream: true });

            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId ? { ...m, text: streamed } : m,
              ),
            );
          }
        }
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsgId ? { ...m, text: errorFallback } : m,
          ),
        );
      } finally {
        setIsTyping(false);
      }
    },
    [apiUrl, token, agentId, errorFallback],
  );

  return {
    messages,
    inputValue,
    setInputValue,
    isTyping,
    handleSendMessage,
    chatEndRef,
  };
}
