import { request } from "./client";
import type { FramilyListItem, FramilyInfo, FramilySettings } from "./types";

export const framilyApi = {
  list: (token: string, username?: string) => {
    const params = username
      ? `?username=${encodeURIComponent(username)}`
      : "";
    return request<{ framilies: FramilyListItem[] }>(`/framily/list${params}`, {
      token,
    });
  },

  connect: (framily_code: string, token: string) =>
    request<{ message: string }>("/framily/connect", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
      token,
    }),

  info: (framily_code: string, token: string) =>
    request<{ framily: FramilyInfo }>(
      `/framily/info?framily_code=${framily_code}`,
      { token },
    ),

  invite: (framily_code: string, username: string, token: string) =>
    request<{ message: string }>("/framily/invite", {
      method: "POST",
      body: JSON.stringify({ framily_code, username }),
      token,
    }),

  join: (framily_code: string, accepted: boolean, token: string) =>
    request<{ message: string }>("/framily/join", {
      method: "POST",
      body: JSON.stringify({ framily_code, accepted }),
      token,
    }),

  leave: (framily_code: string, token: string) =>
    request<{ message: string }>("/framily/leave", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
      token,
    }),

  kick: (framily_code: string, username: string, token: string) =>
    request<{ message: string }>("/framily/kick", {
      method: "POST",
      body: JSON.stringify({ framily_code, username }),
      token,
    }),

  promote: (
    framily_code: string,
    username: string,
    new_role: number,
    token: string,
  ) =>
    request<{ message: string }>("/framily/promote", {
      method: "POST",
      body: JSON.stringify({ framily_code, username, new_role }),
      token,
    }),

  updateSettings: (
    framily_code: string,
    settings: Partial<FramilySettings>,
    token: string,
  ) =>
    request<{ message: string }>("/framily/settings", {
      method: "POST",
      body: JSON.stringify({ framily_code, settings }),
      token,
    }),

  delete: (framily_code: string, token: string) =>
    request<{ message: string }>("/framily/delete", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
      token,
    }),
};
