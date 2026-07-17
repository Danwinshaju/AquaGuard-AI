import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { purgeExpiredOwnerMedia } from "../storage/userMediaStorage";

export interface AccountUser {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

interface AuthContextValue {
  user: AccountUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function readAccount(response: Response): Promise<AccountUser> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Account request failed (${response.status})`);
  }
  return (await response.json()) as AccountUser;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AccountUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetch("/api/v1/auth/me")
      .then(async (response) => (response.ok ? ((await response.json()) as AccountUser) : null))
      .then((account) => {
        if (active) {
          setUser(account);
          if (account) void purgeExpiredOwnerMedia(account.id);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const account = await readAccount(
          await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          }),
        );
        setUser(account);
        void purgeExpiredOwnerMedia(account.id);
      },
      signup: async (name, email, password) => {
        const account = await readAccount(
          await fetch("/api/v1/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password }),
          }),
        );
        setUser(account);
        void purgeExpiredOwnerMedia(account.id);
      },
      logout: async () => {
        await fetch("/api/v1/auth/logout", { method: "POST" });
        setUser(null);
      },
    }),
    [loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider.");
  return value;
}
