"use client";
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import api from "@/services/api";
import type { User, AuthState, LoginPayload, RegisterPayload, TokenResponse } from "@/types";

interface AuthContextValue extends AuthState {
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Rehydrate from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    const stored = localStorage.getItem("auth_user");
    if (token && stored) {
      try {
        const user: User = JSON.parse(stored);
        setState({ user, token, isAuthenticated: true, isLoading: false });
      } catch {
        setState((s) => ({ ...s, isLoading: false }));
      }
    } else {
      setState((s) => ({ ...s, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const { data } = await api.post<TokenResponse>("/auth/login", payload);
    const user: User = {
      user_id: data.user_id,
      name: data.name,
      email: payload.email,
      role: data.role as User["role"],
    };
    localStorage.setItem("auth_token", data.token);
    localStorage.setItem("auth_user", JSON.stringify(user));
    setState({ user, token: data.token, isAuthenticated: true, isLoading: false });
    router.push("/chat");
  }, [router]);

  const register = useCallback(async (payload: RegisterPayload) => {
    const { data } = await api.post<TokenResponse>("/auth/register", payload);
    const user: User = {
      user_id: data.user_id,
      name: data.name,
      email: payload.email,
      role: data.role as User["role"],
    };
    localStorage.setItem("auth_token", data.token);
    localStorage.setItem("auth_user", JSON.stringify(user));
    setState({ user, token: data.token, isAuthenticated: true, isLoading: false });
    router.push("/chat");
  }, [router]);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    setState({ user: null, token: null, isAuthenticated: false, isLoading: false });
    toast.success("Logged out successfully");
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
