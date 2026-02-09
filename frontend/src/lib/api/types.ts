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

export interface PictureFramilyInfo {
  code: string;
  name: string;
}

export interface PictureInfo {
  id: string;
  framilies: PictureFramilyInfo[];
  uploader_username: string;
  uploader_display_name: string;
  upload_date: string;
  metadata: Record<string, unknown>;
}
