import { request } from "./client";
import type { FramilyInfo } from "./types";

export const framilyApi = {
  connect: (framily_code: string) =>
    request<{ message: string }>("/framily/connect", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
    }),

  info: (framily_code: string) =>
    request<FramilyInfo>(`/framily/info?framily_code=${framily_code}`),

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

  delete: (framily_code: string) =>
    request<{ message: string }>("/framily/delete", {
      method: "POST",
      body: JSON.stringify({ framily_code }),
    }),

  updateSettings: (
    framily_code: string,
    data: { name?: string; orientation?: string; interval_minutes?: number },
  ) =>
    request<{ message: string }>("/framily/settings", {
      method: "PUT",
      body: JSON.stringify({ framily_code, ...data }),
    }),
};
