import { request } from "./client";
import type { TokenResponse, UserInfo } from "./types";

export const authApi = {
  register: (username: string, email: string, password: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    }),

  login: (usernameOrEmail: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
    }),

  me: () => request<UserInfo>("/auth/me"),
};
