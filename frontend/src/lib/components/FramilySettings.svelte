<script lang="ts">
  import { api, type FramilyInfo } from "$lib/api";
  import ConfirmPopup from "./ConfirmPopup.svelte";

  interface Props {
    framily: FramilyInfo;
    currentUsername: string;
    onChanged: () => void;
    onDeleted?: () => void;
  }

  let { framily, currentUsername, onChanged, onDeleted }: Props = $props();

  let isAdmin = $derived(
    framily.members.find((m) => m.username === currentUsername)?.role === 2,
  );

  const ORIENTATIONS = ["0", "90", "180", "270"] as const;

  let intervalDraft = $state(framily.settings.interval_minutes);
  $effect(() => {
    intervalDraft = framily.settings.interval_minutes;
  });

  let error = $state("");
  let savingInterval = $state(false);

  let deleteConfirmOpen = $state(false);
  let deleteError = $state("");

  async function deleteFramily() {
    deleteError = "";
    try {
      await api.framily.delete(framily.code);
      onDeleted?.();
    } catch (e: any) {
      deleteError = e.message || "Failed to delete framily";
    }
  }

  async function setOrientation(orientation: (typeof ORIENTATIONS)[number]) {
    if (orientation === framily.settings.orientation) return;
    error = "";
    try {
      await api.framily.updateSettings(framily.code, { orientation });
      onChanged();
    } catch (e: any) {
      error = e.message || "Failed to update orientation";
    }
  }

  async function toggleShowUploaderName() {
    const show_uploader_name = !framily.settings.show_uploader_name;
    error = "";
    try {
      await api.framily.updateSettings(framily.code, { show_uploader_name });
      onChanged();
    } catch (e: any) {
      error = e.message || "Failed to update setting";
    }
  }

  async function toggleShowDate() {
    const show_date = !framily.settings.show_date;
    error = "";
    try {
      await api.framily.updateSettings(framily.code, { show_date });
      onChanged();
    } catch (e: any) {
      error = e.message || "Failed to update setting";
    }
  }

  async function saveInterval() {
    error = "";
    const minutes = Math.round(Number(intervalDraft));
    if (!Number.isFinite(minutes) || minutes < 1 || minutes > 1440) {
      error = "Interval must be between 1 and 1440 minutes";
      return;
    }
    if (minutes === framily.settings.interval_minutes) return;
    savingInterval = true;
    try {
      await api.framily.updateSettings(framily.code, { interval_minutes: minutes });
      onChanged();
    } catch (e: any) {
      error = e.message || "Failed to update interval";
    } finally {
      savingInterval = false;
    }
  }
</script>

<ConfirmPopup
  bind:isOpen={deleteConfirmOpen}
  prompt="Delete this framily? This disbands it for every member and cannot be undone. Uploaded pictures are kept in members' own galleries, but will no longer be visible to this framily."
  onConfirm={deleteFramily}
/>

<div class="settings">
  {#if error}
    <p class="error">{error}</p>
  {/if}

  <section class="section">
    <h3 class="section-title">Display</h3>

    <div class="setting">
      <div class="setting-label">Display interval</div>
      {#if isAdmin}
        <div class="interval-row">
          <input
            type="number"
            min="1"
            max="1440"
            bind:value={intervalDraft}
            disabled={savingInterval}
            onchange={saveInterval}
          />
          <span class="unit">minutes</span>
        </div>
      {:else}
        <div class="setting-value">{framily.settings.interval_minutes} minutes</div>
      {/if}
    </div>

    <div class="setting">
      <div class="setting-label">Orientation</div>
      {#if isAdmin}
        <div class="orientation-row">
          {#each ORIENTATIONS as orientation}
            <button
              class="orientation-button"
              class:selected={framily.settings.orientation === orientation}
              onclick={() => setOrientation(orientation)}
            >
              {orientation}°
            </button>
          {/each}
        </div>
      {:else}
        <div class="setting-value">{framily.settings.orientation}°</div>
      {/if}
    </div>

    <div class="setting">
      <div class="setting-label">Show uploader name</div>
      <div class="setting-description">
        Displays the uploader's name in the corner of each picture on the frame.
      </div>
      {#if isAdmin}
        <label class="toggle-row">
          <input
            type="checkbox"
            checked={framily.settings.show_uploader_name}
            onchange={toggleShowUploaderName}
          />
          <span>{framily.settings.show_uploader_name ? "On" : "Off"}</span>
        </label>
      {:else}
        <div class="setting-value">{framily.settings.show_uploader_name ? "On" : "Off"}</div>
      {/if}
    </div>

    <div class="setting">
      <div class="setting-label">Show date</div>
      <div class="setting-description">
        Displays the picture's upload date in the corner of each picture on the frame.
      </div>
      {#if isAdmin}
        <label class="toggle-row">
          <input
            type="checkbox"
            checked={framily.settings.show_date}
            onchange={toggleShowDate}
          />
          <span>{framily.settings.show_date ? "On" : "Off"}</span>
        </label>
      {:else}
        <div class="setting-value">{framily.settings.show_date ? "On" : "Off"}</div>
      {/if}
    </div>
  </section>

  <section class="section">
    <h3 class="section-title">Frame status</h3>

    <div class="setting">
      <div class="setting-label">Resolution</div>
      <div class="setting-value">
        {#if framily.resolution_width && framily.resolution_height}
          {framily.resolution_width} × {framily.resolution_height}
        {:else}
          Not reported yet
        {/if}
      </div>
    </div>

    <div class="setting">
      <div class="setting-label">IP address</div>
      <div class="setting-value">
        {#if framily.ip_address}
          <a href={`http://${framily.ip_address}`} target="_blank" rel="noreferrer">{framily.ip_address}</a>
        {:else}
          Not reported yet
        {/if}
      </div>
    </div>
  </section>

  {#if isAdmin}
    <section class="section danger-zone">
      <h3 class="section-title">Danger zone</h3>

      {#if deleteError}
        <p class="error">{deleteError}</p>
      {/if}

      <div class="setting">
        <div class="setting-label">Delete framily</div>
        <div class="setting-description">
          Permanently disbands this framily for all members. This cannot be undone.
        </div>
        <button class="delete-button" onclick={() => (deleteConfirmOpen = true)}>
          Delete framily
        </button>
      </div>
    </section>
  {/if}
</div>

<style>
  .settings {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .error {
    color: #dc3545;
    margin: 0;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-title {
    margin: 0;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #666;
  }

  .danger-zone .section-title {
    color: #dc3545;
  }

  .delete-button {
    align-self: flex-start;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }

  .setting {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .setting-label {
    font-weight: bold;
  }

  .setting-value {
    color: #333;
  }

  .setting-description {
    color: #666;
    font-size: 0.85rem;
    margin: -0.25rem 0 0;
  }

  .toggle-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    width: fit-content;
  }

  .toggle-row input {
    width: 1.1rem;
    height: 1.1rem;
    cursor: pointer;
  }

  .interval-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .interval-row input {
    width: 5rem;
    padding: 0.35rem 0.5rem;
  }

  .unit {
    color: #666;
  }

  .orientation-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .orientation-button {
    padding: 0.5rem 1rem;
    border: 1px solid #ccc;
    border-radius: 6px;
    background: white;
    cursor: pointer;
  }

  .orientation-button.selected {
    background-color: #4593e7;
    border-color: #4593e7;
    color: white;
    font-weight: bold;
  }
</style>
