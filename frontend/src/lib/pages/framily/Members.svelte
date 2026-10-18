<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import { api, type FramilyMember, type Role } from "$lib/api";
  import { app } from "$lib/app";
  import { overlay } from "$lib/overlay";
  import ConfirmPopup from "$lib/popups/ConfirmPopup.svelte";
  import InvitePopup from "$lib/popups/InvitePopup.svelte";
  import Avatar from "$lib/ui/Avatar.svelte";
  import UserPlus from "@lucide/svelte/icons/user-plus";

  interface Props {
    framilyCode: string;
    members: FramilyMember[];
    currentUsername: string;
    onChanged: () => void;
  }

  let { framilyCode, members, currentUsername, onChanged }: Props = $props();

  let isAdmin = $derived(
    members.find((m) => m.username === currentUsername)?.role === "admin",
  );

  let error = $state("");

  function roleName(role: Role): string {
    switch (role) {
      case "invited":
        return m.role_invited();
      case "member":
        return m.role_member();
      case "admin":
        return m.role_admin();
      default:
        return m.role_unknown();
    }
  }

  async function kick(username: string) {
    error = "";
    try {
      await api.framily.kick(framilyCode, username);
      onChanged();
    } catch (e: any) {
      error = e.message || m.members_kick_failed();
    }
  }

  function confirmKick(username: string) {
    overlay.open(ConfirmPopup, {
      prompt: m.members_confirm_kick(),
      onConfirm: () => kick(username),
    });
  }

  async function setRole(username: string, newRole: Role) {
    error = "";
    try {
      await api.framily.promote(framilyCode, username, newRole);
      onChanged();
    } catch (e: any) {
      error = e.message || m.members_role_failed();
    }
  }
</script>

<div class="members">
  {#if isAdmin}
    <button class="invite" onclick={() => overlay.open(InvitePopup, { framilyCode, onSuccess: onChanged })}>
      <UserPlus size={16} />
      {m.members_invite()}
    </button>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <div class="members-list">
    {#each members as member}
      <div class="member">
        <button
          class="member-identity"
          onclick={() =>
            app.navigate({
              page: "profile",
              username: member.username,
              section: "pictures",
            })}
        >
          <Avatar kind="user" id={member.username} label={member.display_name ?? member.username} size={40} />
          <div class="member-names">
            <div class="member-name">{member.display_name}</div>
            <div class="member-username">@{member.username}</div>
          </div>
        </button>
        <span class="role-badge role-{member.role}">{roleName(member.role)}</span>
        {#if isAdmin && member.username !== currentUsername}
          <div class="member-actions">
            {#if member.role === "member"}
              <button onclick={() => setRole(member.username, "admin")}>{m.members_make_admin()}</button>
            {:else if member.role === "admin"}
              <button onclick={() => setRole(member.username, "member")}>{m.members_demote()}</button>
            {/if}
            <button class="kick" onclick={() => confirmKick(member.username)}>
              {member.role === "invited" ? m.members_cancel_invite() : m.members_kick()}
            </button>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .members {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .invite {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: var(--color-success);
    color: var(--color-text-inverse);
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }

  .error {
    color: var(--color-danger);
    margin: 0;
  }

  .members-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .member {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    background: var(--color-bg-surface);
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px var(--color-shadow);
  }

  .member-identity {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: none;
    border: none;
    text-align: left;
    padding: 0;
    cursor: pointer;
    flex: 1;
    min-width: 120px;
  }

  .member-name {
    font-weight: bold;
    font-size: 1.1rem;
  }

  .member-username {
    color: var(--color-text-secondary);
  }

  .role-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .role-badge.role-invited {
    background-color: var(--color-warning);
    color: #222;
  }

  .role-badge.role-member {
    background-color: var(--color-info);
    color: var(--color-text-inverse);
  }

  .role-badge.role-admin {
    background-color: var(--color-success);
    color: var(--color-text-inverse);
  }

  .member-actions {
    display: flex;
    gap: 0.5rem;
    width: 100%;
  }

  .member-actions button {
    padding: 0.35rem 0.75rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    background-color: var(--color-accent-blue);
    color: var(--color-text-inverse);
  }

  .member-actions .kick {
    background-color: var(--color-danger);
  }
</style>
