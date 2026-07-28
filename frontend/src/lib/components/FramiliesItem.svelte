<script lang="ts">
  import { api } from "$lib/api";
  import { app } from "$lib/app";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import { type UserFramilyInfo } from "$lib/api";
  import ConfirmPopup from "./ConfirmPopup.svelte";

  interface Props {
    framily: UserFramilyInfo;
  }

  let { framily }: Props = $props();

  async function acceptInvite(code: string) {
    await api.framily.join(code, true);
  }

  async function declineInvite(code: string) {
    await api.framily.join(code, false);
  }

  async function leave(code: string) {
    await api.framily.leave(code);
  }

  let confirmOpen = $state(false);
  let onCancel: () => void = $state(() => {});
  let onConfirm: () => void = $state(() => {});

  function confirmLeave(code: string) {
    onCancel = () => {};
    onConfirm = async () => {
      await leave(code);
    };
    confirmOpen = true;
  }

  function confirmDecline(code: string) {
    onCancel = () => {};
    onConfirm = async () => {
      await declineInvite(code);
    };
    confirmOpen = true;
  }
</script>

<ConfirmPopup bind:isOpen={confirmOpen} {onCancel} {onConfirm} />
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
  <div class="framily-info">
    <div class="framily-name">{framily.name}</div>
    <div class="framily-code">@{framily.code}</div>
  </div>
  <div class="framily-actions">
    {#if framily.role === 0}
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
  .framily {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
    padding: 1rem;
    text-align: left;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
    color: #666;
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
