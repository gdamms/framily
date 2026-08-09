import { Capacitor } from "@capacitor/core";
import type { Action } from "svelte/action";

interface AuthImageSrcParams {
  url: string;
  fetchBlob: () => Promise<Blob>;
}

// <img src> can't carry the Bearer header native builds authenticate with
// (see api/client.ts) - a cross-origin cookie doesn't exist there either.
// On native this fetches the image through the authenticated request path
// and points the element at an object URL instead; on web it's a no-op
// passthrough to the plain URL (cookie auth still applies there).
export const authImageSrc: Action<HTMLImageElement, AuthImageSrcParams> = (node, params) => {
  let objectUrl: string | null = null;
  let lastUrl: string | null = null;
  let cancelled = false;

  function revoke() {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
  }

  async function apply(p: AuthImageSrcParams) {
    if (p.url === lastUrl) {
      return;
    }
    lastUrl = p.url;

    if (!Capacitor.isNativePlatform()) {
      node.src = p.url;
      return;
    }

    try {
      const blob = await p.fetchBlob();
      if (cancelled || lastUrl !== p.url) {
        return;
      }
      const url = URL.createObjectURL(blob);
      revoke();
      objectUrl = url;
      node.src = url;
    } catch {
      // Leave src unset - equivalent to a failed <img> load on web.
    }
  }

  apply(params);

  return {
    update(p) {
      apply(p);
    },
    destroy() {
      cancelled = true;
      revoke();
    },
  };
};
