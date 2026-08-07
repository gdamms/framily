<script lang="ts">
  import { onDestroy } from "svelte";

  interface Props {
    fileInput?: HTMLInputElement;
  }

  let { fileInput = $bindable() }: Props = $props();

  const INITIAL_TEXT = "Drag and drop your file here or click to select";

  let text = $state(INITIAL_TEXT);
  let previewUrl: string | null = $state(null);

  function handleSelect() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      previewUrl = null;
    }

    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];
      text = `${file.name}`;
      previewUrl = URL.createObjectURL(file);
    } else {
      text = INITIAL_TEXT;
    }
  }

  onDestroy(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  });
</script>

<input
  bind:this={fileInput}
  class="file"
  type="file"
  id="file"
  onchange={handleSelect}
/>
<label for="file">
  <div class="box">
    <div class="inner">
      {#if previewUrl}
        <img class="preview" src={previewUrl} alt="Selected file preview" />
      {:else}
        <div class="text">
          {text}
        </div>
      {/if}
    </div>
  </div>
</label>

<style>
  .box {
    background-color: var(--color-dropzone-bg);
    padding: 10px;
    border-radius: 10px;
    transition:
      padding 0.1s ease,
      background-color 0.5s ease;
  }

  .inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 30px;
    border: 2px dashed var(--color-dropzone-border);
    border-radius: 10px;
    transition: padding 0.1s ease;
    min-width: 100px;
    min-height: 50px;
  }

  .box:hover {
    padding: 20px;
    background-color: var(--color-dropzone-bg-hover);
  }

  .box:hover .inner {
    padding: 20px;
  }

  .file {
    display: none;
  }

  .text {
    font-size: 16px;
    color: var(--color-text);
    margin-bottom: 10px;
  }

  .preview {
    max-width: 200px;
    max-height: 200px;
    border-radius: 5px;
    object-fit: contain;
  }
</style>
