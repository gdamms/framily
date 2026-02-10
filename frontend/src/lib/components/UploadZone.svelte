<script lang="ts">
  let text = "Drag and drop your file here or click to select";

  function handleFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      text = `${file.name}`;
    }
  }
</script>

<form method="post" action="">
  <input class="file" type="file" id="file" on:change={handleFileUpload} />
  <label for="file">
    <div class="box">
      <div class="inner">
         <div class="text">
            {text}
         </div>
         <button class="button" type="submit">Upload</button>
      </div>
    </div>
  </label>
</form>

<style>
  .box {
    background-color: #c8dadf;
    padding: 10px;
    border-radius: 10px;
    transition: padding 0.1s ease, background-color 0.5s ease;
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

  .button {
    margin-top: 10px;
    padding: 10px 20px;
    background-color: #4593e7;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }
</style>
