// Re-export types
export type {
  TokenResponse,
  UserInfo,
  UserFramilyInfo,
  FramilyMember,
  FramilyInfo,
  FramilySettingsInfo,
  FramilyPictureInfo,
  PictureFramilyInfo,
  PictureInfo,
  FocusArea,
  Role,
} from "./types";

// Re-export error class
export { ApiError } from "./client";

// Import sub-APIs
import { authApi } from "./auth";
import { userApi } from "./user";
import { framilyApi } from "./framily";
import { picturesApi } from "./pictures";

// Compose the api object for backward compatibility
export const api = {
  auth: authApi,
  user: userApi,
  framily: framilyApi,
  pictures: picturesApi,
};
