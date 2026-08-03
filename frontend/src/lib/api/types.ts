export interface TokenResponse {
  token: string;
}

export interface UserInfo {
  username: string;
  email?: string;
  display_name: string;
  created_at?: string;
  framilies?: UserFramilyInfo[];
  pictures?: PictureInfo[];
}

export interface UserFramilyInfo {
  code: string;
  name?: string | null;
  role: number;
  member_count: number;
  picture_count: number;
  created_at: string;
}

export interface FramilyMember {
  username: string;
  display_name?: string | null;
  role: number;
}

export interface FramilyPictureInfo {
  id: string;
  uploader_username: string;
}

export interface FramilySettingsInfo {
  orientation: "0" | "90" | "180" | "270";
  interval_minutes: number;
}

export interface FramilyInfo {
  code: string;
  name: string | null;
  members: FramilyMember[];
  pictures: FramilyPictureInfo[];
  settings: FramilySettingsInfo;
  resolution_width: number | null;
  resolution_height: number | null;
}

export interface PictureFramilyInfo {
  code: string;
  name: string;
}

export interface PictureInfo {
  id: string;
  framilies: PictureFramilyInfo[];
  uploader_username: string;
  uploader_display_name?: string | null;
  upload_date: string;
  metadata: Record<string, unknown> | null;
}
