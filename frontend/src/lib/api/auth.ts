import { request } from "./client";
import type { AuthFeatures, MessageResponse, TokenResponse, UserInfo } from "./types";

export const authApi = {
  register: (username: string, email: string, password: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    }),

  login: (usernameOrEmail: string, password: string, rememberMe: boolean = true) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username_or_email: usernameOrEmail,
        password,
        remember_me: rememberMe,
      }),
    }),

  me: () => request<UserInfo>("/auth/me"),

  features: () => request<AuthFeatures>("/auth/features"),

  forgotPassword: (email: string) =>
    request<MessageResponse>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, password: string) =>
    request<MessageResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    }),
};
