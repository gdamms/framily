export interface TokenResponse {
  token: string;
}

export type Role = "invited" | "member" | "admin";

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
  role: Role;
  member_count: number;
  picture_count: number;
  created_at: string;
}

export interface FramilyMember {
  username: string;
  display_name?: string | null;
  role: Role;
}

export interface FramilyPictureInfo {
  id: string;
  uploader_username: string;
}

export interface FramilySettingsInfo {
  orientation: "0" | "90" | "180" | "270";
  interval_minutes: number;
  show_uploader_name: boolean;
  show_date: boolean;
  preprocess_level: number;
  show_caption: boolean;
}

export interface FramilyInfo {
  code: string;
  name: string | null;
  members: FramilyMember[];
  pictures: FramilyPictureInfo[];
  settings: FramilySettingsInfo;
  resolution_width: number | null;
  resolution_height: number | null;
  ip_address: string | null;
}

export interface PictureFramilyInfo {
  code: string;
  name: string;
}

export interface PictureMetadata {
  width?: number | null;
  height?: number | null;
  format?: string | null;
  file_size?: number | null;
  original_filename?: string | null;
}

export interface FocusArea {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PictureInfo {
  id: string;
  framilies: PictureFramilyInfo[];
  uploader_username: string;
  uploader_display_name?: string | null;
  upload_date: string;
  metadata: PictureMetadata | null;
  description?: string | null;
  focus_area?: FocusArea | null;
}

export const CAPTION_MAX_LENGTH = 300;
