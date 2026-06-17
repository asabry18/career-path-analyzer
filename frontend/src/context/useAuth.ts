import { useContext } from "react";
import type { AuthState } from "./authContextStore";
import { AuthContext } from "./authContextStore";

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
