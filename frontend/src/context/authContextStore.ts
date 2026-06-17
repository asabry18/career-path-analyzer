import { createContext } from "react";
import type { AuthTokens, AuthUser, LoginRequest, SignupRequest } from "../types";

export interface AuthState {
  user: AuthUser | null;
  tokens: AuthTokens | null;
  loading: boolean;
  error: string | null;

  login: (req: LoginRequest) => Promise<boolean>;
  signup: (req: SignupRequest) => Promise<boolean>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);
