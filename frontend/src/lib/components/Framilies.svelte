<script lang="ts">
  import { type FramilyInfo, type FramilyListItem } from "$lib/api";
  import { app } from "$lib/app";
  import { Check, X } from "@lucide/svelte";
  import { api } from "$lib/api";

  interface Props {
    framilies: FramilyInfo[] | FramilyListItem[];
  }

  let { framilies }: Props = $props();

  async function acceptInvite(code: string) {
    await api.framily.join(code, true);
  }

  async function declineInvite(code: string) {
    await api.framily.join(code, false);
  }

  async function leave(code: string) {
    await api.framily.leave(code);
  }
</script>

<div class="framilies">
  {#each framilies as framily}
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
      <div class="framily-name">{framily.name}</div>
      <div class="framily-code">@{framily.code}</div>
      {#if framily.role === 0}
        <div class="invite-buttons">
          <div
            class="decline"
            onclick={(e) => {
              e.stopPropagation();
              declineInvite(framily.code);
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
            leave(framily.code);
          }}
          onkeypress={() => {}}
          role="button"
          tabindex="0"
        >
          <X />
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .framilies {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }

  .framily {
    background: white;
    padding: 1rem;
    text-align: left;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .framily-name {
    font-weight: bold;
    font-size: 1.2rem;
  }

  .framily-code {
    color: #666;
  }

  .invite-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
</style>
