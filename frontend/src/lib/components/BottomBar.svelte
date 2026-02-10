<script lang="ts">
  import UploadButton from "$lib/components/UploadButton.svelte";

</script>

<div class="bottomBar">
  <div class="content">
    <div class="choiceContainer">
      <input type="radio" name="choice" id="left" checked />
      <label for="left" class="choice leftChoice"> Pictures </label>
    </div>
    <div class="divider">
      <UploadButton class="uploadButton" />
    </div>
    <div class="choiceContainer">
      <input type="radio" name="choice" id="right" />
      <label for="right" class="choice rightChoice"> Framilies </label>
    </div>
  </div>
</div>

<style>
  .bottomBar {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 3rem;
    border-top: 1px solid #ccc;
  }

  .content {
    max-width: 800px;
    height: 100%;
    margin: 0 auto;
    display: flex;
  }

  .choiceContainer {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .divider {
    position: relative;
  }

  :global(.uploadButton) {
    position: absolute;
    transform: translateY(-50%);
  }

  input[type="radio"] {
    display: none;
  }

  .choice {
    text-align: center;
    cursor: pointer;
    transition: background-color 0.2s ease;
    padding: 0.75rem;
    border-radius: 1000px;
  }

  .choice:hover {
    background-color: #d7efff;
  }

  input[type="radio"]:checked + label {
    background-color: #d7efff;
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.3);
  }
</style>
