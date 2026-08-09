import { request, requestBlob, requestFormData, getApiBaseUrl } from "./client";
import type { FramilyInfo, Role } from "./types";

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
    new_role: Role,
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
    data: {
      name?: string;
      orientation?: string;
      interval_minutes?: number;
      show_uploader_name?: boolean;
      show_date?: boolean;
      preprocess_level?: number;
      show_caption?: boolean;
    },
  ) =>
    request<{ message: string }>("/framily/settings", {
      method: "PUT",
      body: JSON.stringify({ framily_code, ...data }),
    }),

  uploadAvatar: (framily_code: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestFormData<{ message: string }>(
      `/avatars/framily?framily_code=${encodeURIComponent(framily_code)}`,
      formData,
    );
  },

  deleteAvatar: (framily_code: string) =>
    request<{ message: string }>(
      `/avatars/framily?framily_code=${encodeURIComponent(framily_code)}`,
      { method: "DELETE" },
    ),

  getAvatarUrl: (framily_code: string): string => {
    return `${getApiBaseUrl()}/avatars/framily?framily_code=${encodeURIComponent(framily_code)}`;
  },

  getAvatarBlob: (framily_code: string) =>
    requestBlob(`/avatars/framily?framily_code=${encodeURIComponent(framily_code)}`),
};
