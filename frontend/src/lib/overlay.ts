import { writable } from "svelte/store";
import type { Component } from "svelte";

export interface OverlayEntry {
  id: number;
  component: Component<any>;
  props: Record<string, any>;
}

function createOverlay() {
  const stack = writable<OverlayEntry[]>([]);
  let nextId = 0;

  function open(component: Component<any>, props: Record<string, any> = {}): number {
    const id = nextId++;
    stack.update((entries) => [...entries, { id, component, props }]);
    return id;
  }

  function close(id: number) {
    stack.update((entries) => entries.filter((entry) => entry.id !== id));
  }

  function closeTop() {
    stack.update((entries) => entries.slice(0, -1));
  }

  return { stack, open, close, closeTop };
}

export const overlay = createOverlay();
