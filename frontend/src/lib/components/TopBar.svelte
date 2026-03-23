<script lang="ts">
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
</script>

<div class="top-bar">
  <h1>Framily</h1>
  <ThemeToggle />
</div>

<style>
  .top-bar {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: var(--color-primary);
    color: white;
    position: sticky;
    top: 0;
    z-index: 10;
    background-color: #2c3e50;
  }

  .top-bar h1 {
    margin: 0;
    font-size: 1.5rem;
  }
</style>
