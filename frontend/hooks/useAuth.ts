/**
 * Reusable API-authentication hook.
 *
 * Handles the common login-fetch-token pattern that was previously
 * duplicated in every page-level component (operations, fan, volunteer, replay).
 */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { API_BASE_URL } from "../lib/constants";

interface UseAuthResult {
  /** JWT access token, empty string until authentication succeeds. */
  token: string;
  /** Whether the initial auth + data load is still in progress. */
  loading: boolean;
  /** Set loading flag externally (e.g. for manual refresh). */
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

/**
 * Authenticates with the backend and runs `onAuthenticated` with the JWT.
 *
 * @param email  Demo user email to log in with.
 * @param onAuthenticated  Callback invoked with the JWT once login succeeds.
 * @param onError  Optional callback invoked on auth failure.
 */
export function useAuth(
  email: string,
  onAuthenticated?: (token: string) => Promise<void>,
  onError?: () => void,
): UseAuthResult {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(true);

  const onAuthenticatedRef = useRef(onAuthenticated);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onAuthenticatedRef.current = onAuthenticated;
  }, [onAuthenticated]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    let cancelled = false;

    async function authenticate() {
      try {
        setLoading(true);

        const res = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });

        if (!res.ok) throw new Error("Authentication failed");

        const data = await res.json();
        if (cancelled) return;

        setToken(data.access_token);

        if (onAuthenticatedRef.current) {
          await onAuthenticatedRef.current(data.access_token);
        }
      } catch (err) {
        console.error("Auth error:", err);
        if (!cancelled) onErrorRef.current?.();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    authenticate();

    return () => {
      cancelled = true;
    };
  }, [email]);

  return { token, loading, setLoading };
}
