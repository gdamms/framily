<script lang="ts">
  import { type Snippet } from "svelte";

  interface Props {
    children: Snippet;
    onclick?: (() => void);
    type?: "button" | "submit" | "reset";
    color?: string;
    class?: string;
  }

  let {
    children,
    onclick,
    type,
    color = "#84c8f7",
    class: _class,
  }: Props = $props();
</script>

<button class={"button" + (_class || "")} {onclick} style="--color: {color}" {type}>
  <div class="button-content">
    {@render children()}
  </div>
</button>

<style>
  .button {
    border: none;
    background: color-mix(in srgb, var(--color), #000 50%);
    padding: 0;
    border-radius: 1000px;
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.3);
  }

  .button-content {
    box-sizing: border-box;
    width: calc(100% + 2px);
    height: calc(100% + 2px);
    border-radius: 1000px;
    background-color: var(--color);
    padding: 0.75rem 1.5rem;
    transform: translate(-1px, 0px);
    transition: transform 0.1s ease;
  }

  .button:hover .button-content,
  .button:focus .button-content {
    transform: translate(-1px, -5px);
  }

  .button:active .button-content {
    transform: translate(-1px, -2px);
  }
</style>
