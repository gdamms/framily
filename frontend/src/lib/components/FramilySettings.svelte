<script lang="ts">
  import { api, type FramilyInfo } from "$lib/api";

  interface Props {
    framily: FramilyInfo;
    currentUsername: string;
    onChanged: () => void;
  }

  let { framily, currentUsername, onChanged }: Props = $props();

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

<div class="settings">
  {#if error}
    <p class="error">{error}</p>
  {/if}

  <div class="setting">
    <div class="setting-label">Frame resolution</div>
    <div class="setting-value">
      {#if framily.resolution_width && framily.resolution_height}
        {framily.resolution_width} × {framily.resolution_height}
      {:else}
        Not reported yet
      {/if}
    </div>
  </div>

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
      Displays "by &lt;name&gt;" in the corner of each picture on the frame.
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
