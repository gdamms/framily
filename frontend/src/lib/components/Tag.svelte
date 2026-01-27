<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    children: Snippet;
    color?: string;
    oncrossclick?: (() => void) | null;
    href?: string | null;
  }

  let {
    children,
    color = "gray",
    oncrossclick = null,
    href = null,
  }: Props = $props();
</script>

<a class="tag" style="--color: {color}" href={href}>
  {@render children()}
  {#if oncrossclick}
    <button
      class="cross-btn"
      onclick={oncrossclick}
    >
      &times;
    </button>
  {/if}
</a>

<style>
  .tag {
    display: flex;
    align-items: center;
    padding: 0.2em 0.6em;
    border: 2px solid var(--color);
    background: color-mix(in srgb, var(--color), transparent 50%);
    border-radius: 1000px;
    font-size: 0.875em;
    color: #000;
    text-decoration: none;
  }

  .cross-btn {
    background: none;
    border: none;
    color: var(--color);
    font-size: 1em;
    line-height: 1;
    margin-left: 0.4em;
    cursor: pointer;
    transform-origin: center;
    padding: 0;
    transition: transform 0.2s ease-in-out;
  }

  .cross-btn:hover {
    transform: scale(2);
  }
</style>
