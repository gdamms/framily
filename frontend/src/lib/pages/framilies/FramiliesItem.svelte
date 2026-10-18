<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import { api } from "$lib/api";
  import { app } from "$lib/app";
  import { overlay } from "$lib/overlay";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import { type UserFramilyInfo } from "$lib/api";
  import ConfirmPopup from "$lib/popups/ConfirmPopup.svelte";
  import Avatar from "$lib/ui/Avatar.svelte";

  interface Props {
    framily: UserFramilyInfo;
    onChanged?: () => void;
  }

  let { framily, onChanged }: Props = $props();

  let error = $state("");

  async function acceptInvite(code: string) {
    error = "";
    try {
      await api.framily.join(code, true);
      onChanged?.();
    } catch (e: any) {
      error = e.message || m.framilies_accept_failed();
    }
  }

  async function declineInvite(code: string) {
    error = "";
    try {
      await api.framily.join(code, false);
      onChanged?.();
    } catch (e: any) {
      error = e.message || m.framilies_decline_failed();
    }
  }

  async function leave(code: string) {
    error = "";
    try {
      await api.framily.leave(code);
      onChanged?.();
    } catch (e: any) {
      error = e.message || m.framilies_leave_failed();
    }
  }

  function confirmLeave(code: string) {
    overlay.open(ConfirmPopup, {
      prompt: m.framilies_confirm_leave(),
      onConfirm: () => leave(code),
    });
  }

  function confirmDecline(code: string) {
    overlay.open(ConfirmPopup, {
      prompt: m.framilies_confirm_decline(),
      onConfirm: () => declineInvite(code),
    });
  }
</script>

{#if error}
  <p class="error">{error}</p>
{/if}
<div
  class="framily"
  onclick={() =>
    app.navigate({
      page: "framily",
      code: framily.code,
      section: "pictures",
    })}
  onkeypress={() => {}}
  role="button"
  tabindex="0"
>
  <div class="framily-identity">
    <Avatar kind="framily" id={framily.code} label={framily.name ?? framily.code} size={40} />
    <div class="framily-info">
      <div class="framily-name">{framily.name}</div>
      <div class="framily-code">@{framily.code}</div>
    </div>
  </div>
  <div class="framily-actions">
    {#if framily.role === "invited"}
      <div class="invite-buttons">
        <div
          class="decline"
          onclick={(e) => {
            e.stopPropagation();
            confirmDecline(framily.code);
          }}
          onkeypress={() => {}}
          role="button"
          tabindex="0"
        >
          <X />
        </div>
        <div
          class="accept"
          onclick={(e) => {
            e.stopPropagation();
            acceptInvite(framily.code);
          }}
          onkeypress={() => {}}
          role="button"
          tabindex="0"
        >
          <Check />
        </div>
      </div>
    {:else}
      <div
        class="leave"
        onclick={(e) => {
          e.stopPropagation();
          confirmLeave(framily.code);
        }}
        onkeypress={() => {}}
        role="button"
        tabindex="0"
      >
        <X />
      </div>
    {/if}
  </div>
</div>

<style>
  .error {
    color: var(--color-danger);
    margin: 0 0 0.5rem;
  }

  .framily {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--color-bg-surface);
    padding: 1rem;
    text-align: left;
    border-radius: 8px;
    box-shadow: 0 2px 4px var(--color-shadow);
  }

  .framily-identity {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .framily-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .framily-name {
    font-weight: bold;
    font-size: 1.2rem;
  }

  .framily-code {
    color: var(--color-text-secondary);
  }

  .framily-actions {
    display: flex;
    align-items: center;
  }

  .invite-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
</style>
