import { request, requestBlob, requestFormData, getApiBaseUrl } from "./client";
import type { FocusArea, PictureInfo } from "./types";

type PictureListOptions = { framily_code?: string; username?: string };

export const picturesApi = {
  list: (options: PictureListOptions = {}) => {

    const params = new URLSearchParams();
    if (options.framily_code) params.set("framily_code", options.framily_code);
    if (options.username) params.set("username", options.username);
    return request<{ pictures: PictureInfo[] }>(
      `/pictures/list?${params.toString()}`,
    );
  },

  listAll: () => request<{ pictures: PictureInfo[] }>("/pictures/list-all"),

  upload: (framily_codes: string[], file: File) => {
    const formData = new FormData();
    formData.append("framily_codes", framily_codes.join(","));
    formData.append("file", file);
    return requestFormData<{ picture: PictureInfo }>("/pictures/upload", formData);
  },

  addVisibility: (picture_id: string, framily_codes: string[]) =>
    request<{ message: string; picture: PictureInfo }>(
      "/pictures/add-visibility",
      {
        method: "POST",
        body: JSON.stringify({ picture_id, framily_codes }),
      },
    ),

  removeVisibility: (picture_id: string, framily_codes: string[]) =>
    request<{ message: string; picture: PictureInfo; warning?: string }>(
      "/pictures/remove-visibility",
      {
        method: "POST",
        body: JSON.stringify({ picture_id, framily_codes }),
      },
    ),

  updateDescription: (picture_id: string, description: string) =>
    request<{ message: string; picture: PictureInfo }>(
      "/pictures/description",
      {
        method: "PUT",
        body: JSON.stringify({ picture_id, description }),
      },
    ),

  updateFocusArea: (picture_id: string, focus_area: FocusArea | null) =>
    request<{ message: string; picture: PictureInfo }>(
      "/pictures/focus-area",
      {
        method: "PUT",
        body: JSON.stringify({ picture_id, focus_area }),
      },
    ),

  delete: (picture_id: string) => {
    const url = `/pictures/${picture_id}`;
    return request<{ message: string }>(url, {
      method: "DELETE",
    });
  },

  getImageUrl: (picture: PictureInfo): string => {
    return `${getApiBaseUrl()}/pictures/${picture.id}`;
  },

  getImageBlob: (picture_id: string) => requestBlob(`/pictures/${picture_id}`),
};
