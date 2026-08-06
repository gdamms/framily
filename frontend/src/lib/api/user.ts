import { request, requestFormData, API_BASE_URL } from "./client";
import type { UserInfo } from "./types";

export const userApi = {
  getInfo: (username: string) =>
    request<{ user: UserInfo }>(`/user/info?username=${encodeURIComponent(username)}`),

  updateProfile: (data: { display_name?: string; email?: string }) =>
    request<{ user: UserInfo }>("/user/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteAccount: (password: string) =>
    request<{ message: string }>("/user/delete", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  uploadAvatar: (username: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestFormData<{ message: string }>(
      `/avatars/user?username=${encodeURIComponent(username)}`,
      formData,
    );
  },

  deleteAvatar: (username: string) =>
    request<{ message: string }>(`/avatars/user?username=${encodeURIComponent(username)}`, {
      method: "DELETE",
    }),

  getAvatarUrl: (username: string): string => {
    return `${API_BASE_URL}/avatars/user?username=${encodeURIComponent(username)}`;
  },
};
