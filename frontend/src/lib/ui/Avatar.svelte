<script lang="ts">
  import { api } from "$lib/api";
  import Pencil from "@lucide/svelte/icons/pencil";

  interface Props {
    kind: "user" | "framily";
    id: string;
    label: string;
    editable?: boolean;
    size?: number;
  }

  let { kind, id, label, editable = false, size = 64 }: Props = $props();

  let fileInput: HTMLInputElement | undefined = $state();
  let uploading = $state(false);
  let error = $state("");
  let loaded = $state(false);
  // A cache-busting token. Must stay unique across page reloads, not just within
  // a session: the server sends a 24h Cache-Control on avatar responses, so a
  // counter that resets to 0 on every mount would collide with a URL cached by
  // an earlier page load and silently serve a stale image.
  let version = $state(Date.now());

  let baseUrl = $derived(
    kind === "user" ? api.user.getAvatarUrl(id) : api.framily.getAvatarUrl(id),
  );
  let src = $derived(`${baseUrl}&v=${version}`);

  let initials = $derived(label.trim().slice(0, 2).toUpperCase());

  $effect(() => {
    // Reset the placeholder/image state whenever we're pointed at a different avatar.
    id;
    loaded = false;
  });

  function handleLoad() {
    loaded = true;
  }

  function handleError() {
    loaded = false;
  }

  function handleClick() {
    if (!editable || uploading) return;
    fileInput?.click();
  }

  async function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = "";
    if (!file) return;

    error = "";
    uploading = true;
    try {
      if (kind === "user") {
        await api.user.uploadAvatar(id, file);
      } else {
        await api.framily.uploadAvatar(id, file);
      }
      version = Date.now();
    } catch (e: any) {
      error = e.message || "Failed to upload avatar";
    } finally {
      uploading = false;
    }
  }
</script>

<div class="avatar-wrap">
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <div
    class="avatar"
    class:editable
    style="width: {size}px; height: {size}px; font-size: {size * 0.4}px;"
    onclick={handleClick}
    onkeydown={editable ? (e) => e.key === "Enter" && handleClick() : undefined}
    role={editable ? "button" : undefined}
    tabindex={editable ? 0 : undefined}
    title={editable ? "Change avatar" : undefined}
  >
    <img
      {src}
      alt="{label}'s avatar"
      class="avatar-img"
      class:visible={loaded}
      crossorigin="use-credentials"
      onload={handleLoad}
      onerror={handleError}
    />
    <div class="avatar-placeholder" class:hidden={loaded}>{initials}</div>
    {#if editable}
      <div class="avatar-overlay">
        <Pencil size={size * 0.35} />
      </div>
    {/if}
  </div>
  {#if editable}
    <input
      type="file"
      accept="image/jpeg,image/png,image/webp,image/gif"
      bind:this={fileInput}
      onchange={handleFileChange}
      hidden
    />
  {/if}
  {#if error}
    <p class="avatar-error">{error}</p>
  {/if}
</div>

<style>
  .avatar-wrap {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
  }

  .avatar {
    position: relative;
    border-radius: 50%;
    flex-shrink: 0;
    overflow: hidden;
  }

  .avatar,
  .avatar-img {
    outline: 2px solid #ffffff;
    outline-offset: -3px;
  }

  .avatar.editable {
    cursor: pointer;
  }

  .avatar-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  .avatar-img.visible {
    opacity: 1;
  }

  .avatar-placeholder {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-color: #007bff;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
  }

  .avatar-placeholder.hidden {
    visibility: hidden;
  }

  .avatar-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    background: rgba(0, 0, 0, 0.35);
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  .avatar.editable:hover .avatar-overlay,
  .avatar.editable:focus-visible .avatar-overlay {
    opacity: 1;
  }

  .avatar-error {
    color: #dc3545;
    font-size: 0.75rem;
    margin: 0.25rem 0 0;
    text-align: center;
  }
</style>
