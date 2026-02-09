import { request, requestFormData, API_BASE_URL } from "./client";
import type { PictureInfo } from "./types";

export const picturesApi = {
  list: (
    token: string,
    options: { framily_code?: string; username?: string },
  ) => {
    const params = new URLSearchParams();
    if (options.framily_code) params.set("framily_code", options.framily_code);
    if (options.username) params.set("username", options.username);
    return request<{ pictures: PictureInfo[] }>(
      `/pictures/list?${params.toString()}`,
      { token },
    );
  },

  listAll: (token: string) =>
    request<{ pictures: PictureInfo[] }>("/pictures/list-all", { token }),

  upload: (framily_codes: string[], file: File, token: string) => {
    const formData = new FormData();
    formData.append("framily_codes", framily_codes.join(","));
    formData.append("file", file);
    return requestFormData<{ picture: PictureInfo }>(
      "/pictures/upload",
      formData,
      token,
    );
  },

  addVisibility: (
    picture_id: string,
    framily_codes: string[],
    token: string,
  ) =>
    request<{ message: string; picture: PictureInfo }>(
      "/pictures/add-visibility",
      {
        method: "POST",
        body: JSON.stringify({ picture_id, framily_codes }),
        token,
      },
    ),

  removeVisibility: (
    picture_id: string,
    framily_codes: string[],
    token: string,
  ) =>
    request<{ message: string; picture: PictureInfo; warning?: string }>(
      "/pictures/remove-visibility",
      {
        method: "POST",
        body: JSON.stringify({ picture_id, framily_codes }),
        token,
      },
    ),

  delete: (picture_id: string, token: string) => {
    const url = `/pictures/${picture_id}`;
    return request<{ message: string }>(url, {
      method: "DELETE",
      token,
    });
  },

  getImageUrl: (picture: PictureInfo): string => {
    return `${API_BASE_URL}/pictures/${picture.id}`;
  },
};
