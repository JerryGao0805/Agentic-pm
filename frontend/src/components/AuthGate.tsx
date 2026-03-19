"use client";

import { FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const LOCAL_AUTH_KEY = "pm-local-authenticated";
const AUTH_USERNAME = "user";
const AUTH_PASSWORD = "password";

type AuthMode = "api" | "local";
type AuthState = "loading" | "authenticated" | "unauthenticated";

type SessionResponse = {
  authenticated: boolean;
  username: string | null;
};

const canUseLocalFallback = process.env.NODE_ENV !== "production";

const readLocalAuth = () => {
  if (typeof window === "undefined") {
    return false;
  }
  return window.localStorage.getItem(LOCAL_AUTH_KEY) === "true";
};

export const AuthGate = () => {
  const [authMode, setAuthMode] = useState<AuthMode>("api");
  const [authState, setAuthState] = useState<AuthState>("loading");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    const initializeAuth = async () => {
      try {
        const response = await fetch("/api/auth/session", { credentials: "include" });

        if (response.status === 404 && canUseLocalFallback) {
          if (!active) {
            return;
          }
          setAuthMode("local");
          setAuthState(readLocalAuth() ? "authenticated" : "unauthenticated");
          return;
        }

        if (!response.ok) {
          if (!active) {
            return;
          }
          setAuthMode("api");
          setAuthState("unauthenticated");
          return;
        }

        const payload = (await response.json()) as SessionResponse;
        if (!active) {
          return;
        }
        setAuthMode("api");
        setAuthState(payload.authenticated ? "authenticated" : "unauthenticated");
      } catch {
        if (!active) {
          return;
        }
        if (canUseLocalFallback) {
          setAuthMode("local");
          setAuthState(readLocalAuth() ? "authenticated" : "unauthenticated");
        } else {
          setError("Unable to load session.");
          setAuthMode("api");
          setAuthState("unauthenticated");
        }
      }
    };

    initializeAuth();

    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const trimmedUsername = username.trim();
    if (!trimmedUsername || !password) {
      setError("Enter username and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (authMode === "local") {
        if (trimmedUsername === AUTH_USERNAME && password === AUTH_PASSWORD) {
          window.localStorage.setItem(LOCAL_AUTH_KEY, "true");
          setAuthState("authenticated");
          setPassword("");
          return;
        }
        setError("Invalid credentials.");
        return;
      }

      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username: trimmedUsername, password }),
      });

      if (!response.ok) {
        setError("Invalid credentials.");
        return;
      }

      setAuthState("authenticated");
      setPassword("");
    } catch {
      setError("Login failed. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setError(null);
    if (authMode === "local") {
      window.localStorage.removeItem(LOCAL_AUTH_KEY);
      setAuthState("unauthenticated");
      return;
    }

    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    setAuthState("unauthenticated");
  };

  if (authState === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Checking session...
        </p>
      </main>
    );
  }

  if (authState === "unauthenticated") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <section className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Project Management MVP
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in
          </h1>
          <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
            Use credentials: <strong>user</strong> / <strong>password</strong>
          </p>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label
                htmlFor="username"
                className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
              >
                Username
              </label>
              <input
                id="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="username"
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
              />
            </div>
            {error ? (
              <p className="text-sm font-semibold text-[#b42318]" role="alert">
                {error}
              </p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110 disabled:opacity-60"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <div className="pb-4">
      <div className="mx-auto max-w-[1500px] px-6 pt-6">
        <div className="flex items-center justify-between rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Signed in as <span className="text-[var(--navy-dark)]">{AUTH_USERNAME}</span>
          </p>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
          >
            Log out
          </button>
        </div>
      </div>
      <KanbanBoard />
    </div>
  );
};
