<script lang="ts">
  interface Props {
    fileInput?: HTMLInputElement;
  }

  let { fileInput = $bindable() }: Props = $props();

  const INITIAL_TEXT = "Drag and drop your file here or click to select";

  let text = $state(INITIAL_TEXT);

  async function handleSelect() {
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];
      text = `${file.name}`;
    } else {
      text = INITIAL_TEXT;
    }
  }
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
      <div class="text">
        {text}
      </div>
    </div>
  </div>
</label>

<style>
  .box {
    background-color: #c8dadf;
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
    border: 2px dashed #92b0b3;
    border-radius: 10px;
    transition: padding 0.1s ease;
    min-width: 300px;
    min-height: 150px;
  }

  .box:hover {
    padding: 20px;
    background-color: #f4fdff;
  }

  .box:hover .inner {
    padding: 20px;
  }

  .file {
    display: none;
  }

  .text {
    font-size: 16px;
    color: #333;
    margin-bottom: 10px;
  }
</style>
