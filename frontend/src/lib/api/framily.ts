import { request } from "./client";
import type { FramilyListItem, FramilyInfo, FramilySettings } from "./types";

export const framilyApi = {
  list: (username?: string) => {
    const params = username
      ? `?username=${encodeURIComponent(username)}`
      : "";
    return request<{ framilies: FramilyListItem[] }>(`/framily/list${params}`);
  },

  connect: (framily_code: string) =>
    request<{ message: string }>("/framily/connect", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
    }),

  info: (framily_code: string) =>
    request<{ framily: FramilyInfo }>(`/framily/info?framily_code=${framily_code}`),

  invite: (framily_code: string, username: string) =>
    request<{ message: string }>("/framily/invite", {
      method: "POST",
      body: JSON.stringify({ framily_code, username }),
    }),

  join: (framily_code: string, accepted: boolean) =>
    request<{ message: string }>("/framily/join", {
      method: "POST",
      body: JSON.stringify({ framily_code, accepted }),
    }),

  leave: (framily_code: string) =>
    request<{ message: string }>("/framily/leave", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
    }),

  kick: (framily_code: string, username: string) =>
    request<{ message: string }>("/framily/kick", {
      method: "POST",
      body: JSON.stringify({ framily_code, username }),
    }),

  promote: (
    framily_code: string,
    username: string,
    new_role: number,
  ) =>
    request<{ message: string }>("/framily/promote", {
      method: "POST",
      body: JSON.stringify({ framily_code, username, new_role }),
    }),

  updateSettings: (
    framily_code: string,
    settings: Partial<FramilySettings>,
  ) =>
    request<{ message: string }>("/framily/settings", {
      method: "POST",
      body: JSON.stringify({ framily_code, settings }),
    }),

  delete: (framily_code: string) =>
    request<{ message: string }>("/framily/delete", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
    }),
};
