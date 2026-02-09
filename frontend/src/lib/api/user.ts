import { request, requestFormData, API_BASE_URL } from "./client";
import type { UserInfo, FramilyMember } from "./types";

export const userApi = {
  getInfo: (username: string, token: string) =>
    request<{ user: UserInfo }>(
      `/user/info?username=${encodeURIComponent(username)}`,
      { token },
    ),

  updateProfile: (
    data: { display_name?: string; email?: string },
    token: string,
  ) =>
    request<{ user: UserInfo }>("/user/profile", {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  uploadProfilePicture: (file: File, token: string) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestFormData<{ message: string }>(
      "/user/profile-picture",
      formData,
      token,
    );
  },

  deleteProfilePicture: (token: string) =>
    request<{ message: string }>("/user/profile-picture", {
      method: "DELETE",
      token,
    }),

  getProfilePictureUrl: (user: UserInfo | FramilyMember): string => {
    return `${API_BASE_URL}/user/profile-picture?username=${user.username}&t=${new Date().getTime()}`;
  },
};
