const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options?: RequestInit & { token?: string },
): Promise<T> {
  const { token, ...fetchOptions } = options || {};

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Request failed" }));
    throw new ApiError(
      response.status,
      error.detail || error.message || "Request failed",
    );
  }

  return response.json();
}

async function requestFormData<T>(
  endpoint: string,
  formData: FormData,
  token?: string,
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Request failed" }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  return response.json();
}

export interface TokenResponse {
  token: string;
}

export interface UserInfo {
  username: string;
  email?: string;
  display_name: string;
  created_at?: string;
}

export interface FramilyListItem {
  id: number;
  code: string;
  name: string | null;
  role: number;
  member_count: number;
  created_at: string;
}

export interface FramilyMember {
  username: string;
  display_name: string;
  role: number;
  joined_date: string;
}

export interface FramilySettings {
  picture_duration: number;
  shuffle_mode: string;
  transition_effect: string;
  overlays: Array<{ type: string; position: string }>;
}

export interface FramilyInfo {
  code: string;
  name: string | null;
  created_at: string;
  settings?: FramilySettings;
  members?: FramilyMember[];
  member_count?: number;
}

export interface PictureInfo {
  id: string;
  framily_ids: number[];
  framily_codes: string[];
  uploader_username: string;
  uploader_display_name: string;
  upload_date: string;
  metadata: Record<string, unknown>;
}

export const api = {
  auth: {
    register: (username: string, email: string, password: string) =>
      request<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ username, email, password }),
      }),
    login: (username: string, password: string) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      }),
    me: (token: string) => request<UserInfo>("/auth/me", { token }),
  },

  user: {
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
      return requestFormData<{ message: string; profile_picture_url: string }>(
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

    // Helper to get full profile picture URL
    getProfilePictureUrl: (user: UserInfo | FramilyMember): string => {
      return `${API_BASE_URL}/user/profile-picture?username=${user.username}&t=${new Date().getTime()}`; // Cache buster
    },
  },

  framily: {
    list: (token: string) =>
      request<{ framilies: FramilyListItem[] }>("/framily/list", { token }),

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
  },

  pictures: {
    list: (framily_code: string, token: string) =>
      request<{ pictures: PictureInfo[] }>(
        `/pictures/list?framily_code=${framily_code}`,
        { token },
      ),

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

    // Helper to get picture full URL
    getImageUrl: (picture: PictureInfo): string => {
      return `${API_BASE_URL}/pictures/${picture.id}`;
    },
  },
};
