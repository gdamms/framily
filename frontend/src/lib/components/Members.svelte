<script lang="ts">
  import { api, type FramilyMember } from "$lib/api";
  import { app } from "$lib/app";
  import ConfirmPopup from "./ConfirmPopup.svelte";
  import InvitePopup from "./InvitePopup.svelte";
  import UserPlus from "@lucide/svelte/icons/user-plus";

  interface Props {
    framilyCode: string;
    members: FramilyMember[];
    currentUsername: string;
    onChanged: () => void;
  }

  let { framilyCode, members, currentUsername, onChanged }: Props = $props();

  let isAdmin = $derived(
    members.find((m) => m.username === currentUsername)?.role === 2,
  );

  let invitePopupOpen = $state(false);
  let error = $state("");

  let confirmOpen = $state(false);
  let onConfirm: () => void = $state(() => {});

  function roleName(role: number): string {
    switch (role) {
      case 0:
        return "Invited";
      case 1:
        return "Member";
      case 2:
        return "Admin";
      default:
        return "Unknown";
    }
  }

  function confirmKick(username: string) {
    onConfirm = async () => {
      error = "";
      try {
        await api.framily.kick(framilyCode, username);
        onChanged();
      } catch (e: any) {
        error = e.message || "Failed to kick member";
      }
    };
    confirmOpen = true;
  }

  async function setRole(username: string, newRole: number) {
    error = "";
    try {
      await api.framily.promote(framilyCode, username, newRole);
      onChanged();
    } catch (e: any) {
      error = e.message || "Failed to change role";
    }
  }
</script>

<ConfirmPopup bind:isOpen={confirmOpen} prompt="Remove this member from the framily?" {onConfirm} />
<InvitePopup {framilyCode} bind:isOpen={invitePopupOpen} onClose={onChanged} />

<div class="members">
  {#if isAdmin}
    <button class="invite" onclick={() => (invitePopupOpen = true)}>
      <UserPlus size={16} />
      Invite member
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
          <div class="member-name">{member.display_name}</div>
          <div class="member-username">@{member.username}</div>
        </button>
        <span class="role-badge role-{member.role}">{roleName(member.role)}</span>
        {#if isAdmin && member.username !== currentUsername}
          <div class="member-actions">
            {#if member.role === 1}
              <button onclick={() => setRole(member.username, 2)}>Make admin</button>
            {:else if member.role === 2}
              <button onclick={() => setRole(member.username, 1)}>Demote</button>
            {/if}
            <button class="kick" onclick={() => confirmKick(member.username)}>
              {member.role === 0 ? "Cancel invite" : "Kick"}
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
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }

  .error {
    color: #dc3545;
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
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .member-identity {
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
    color: #666;
  }

  .role-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .role-badge.role-0 {
    background-color: #ffc107;
    color: #333;
  }

  .role-badge.role-1 {
    background-color: #17a2b8;
    color: white;
  }

  .role-badge.role-2 {
    background-color: #28a745;
    color: white;
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
    background-color: #007bff;
    color: white;
  }

  .member-actions .kick {
    background-color: #dc3545;
  }
</style>
