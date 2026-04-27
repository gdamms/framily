import { request, requestFormData, API_BASE_URL } from "./client";
import type { UserInfo, FramilyMember } from "./types";

export const userApi = {
  getInfo: (username: string) =>
    request<{ user: UserInfo }>(`/user/info?username=${encodeURIComponent(username)}`),

  updateProfile: (data: { display_name?: string; email?: string }) =>
    request<{ user: UserInfo }>("/user/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  uploadProfilePicture: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestFormData<{ message: string }>("/user/profile-picture", formData);
  },

  deleteProfilePicture: () =>
    request<{ message: string }>("/user/profile-picture", {
      method: "DELETE",
    }),

  getProfilePictureUrl: (user: UserInfo | FramilyMember): string => {
    return `${API_BASE_URL}/user/profile-picture?username=${user.username}&t=${new Date().getTime()}`;
  },
};
