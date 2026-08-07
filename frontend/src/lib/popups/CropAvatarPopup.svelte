<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import Button from "$lib/ui/Button.svelte";
  import StatusMessage from "$lib/ui/StatusMessage.svelte";
  import { createStatusMessage } from "$lib/ui/statusMessage.svelte";

  interface Props {
    file: File;
    onUpload: (file: File) => Promise<void>;
    close?: () => void;
  }

  let { file, onUpload, close = () => {} }: Props = $props();

  const OUTPUT_SIZE = 512;
  const CONTAINER_SIZE = 320;
  const MIN_BOX = 48;

  type Corner = "nw" | "ne" | "sw" | "se";
  const CORNERS: Corner[] = ["nw", "ne", "sw", "se"];

  // `file` never changes over this popup's lifetime - it's fresh per overlay.open() call.
  const previewUrl = untrack(() => URL.createObjectURL(file));
  onDestroy(() => URL.revokeObjectURL(previewUrl));

  let imgEl: HTMLImageElement | undefined = $state();
  let naturalWidth = $state(0);
  let naturalHeight = $state(0);

  // The crop square, in container-space (px), where the whole image is displayed
  // letterboxed ("contain") inside a fixed CONTAINER_SIZE x CONTAINER_SIZE box.
  let boxLeft = $state(0);
  let boxTop = $state(0);
  let boxSize = $state(0);

  let imgScale = $derived(
    naturalWidth && naturalHeight
      ? Math.min(CONTAINER_SIZE / naturalWidth, CONTAINER_SIZE / naturalHeight)
      : 0,
  );
  let imgDisplayWidth = $derived(naturalWidth * imgScale);
  let imgDisplayHeight = $derived(naturalHeight * imgScale);
  let imgLeft = $derived((CONTAINER_SIZE - imgDisplayWidth) / 2);
  let imgTop = $derived((CONTAINER_SIZE - imgDisplayHeight) / 2);
  let imgRight = $derived(imgLeft + imgDisplayWidth);
  let imgBottom = $derived(imgTop + imgDisplayHeight);

  let corners = $derived(
    CORNERS.map((id) => ({
      id,
      x: id === "nw" || id === "sw" ? boxLeft : boxLeft + boxSize,
      y: id === "nw" || id === "ne" ? boxTop : boxTop + boxSize,
    })),
  );

  const status = createStatusMessage();
  let uploading = $state(false);

  function handleImgLoad() {
    if (!imgEl) return;
    const nw = imgEl.naturalWidth;
    const nh = imgEl.naturalHeight;
    const scale = Math.min(CONTAINER_SIZE / nw, CONTAINER_SIZE / nh);
    const dw = nw * scale;
    const dh = nh * scale;
    const left = (CONTAINER_SIZE - dw) / 2;
    const top = (CONTAINER_SIZE - dh) / 2;

    naturalWidth = nw;
    naturalHeight = nh;
    boxSize = Math.min(dw, dh);
    boxLeft = left + (dw - boxSize) / 2;
    boxTop = top + (dh - boxSize) / 2;
  }

  // Body drag: move the whole box within the image bounds.
  let moveStart = { x: 0, y: 0, left: 0, top: 0 };

  function handleBoxPointerDown(event: PointerEvent) {
    moveStart = { x: event.clientX, y: event.clientY, left: boxLeft, top: boxTop };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function handleBoxPointerMove(event: PointerEvent) {
    if (!event.buttons) return;
    const dx = event.clientX - moveStart.x;
    const dy = event.clientY - moveStart.y;
    boxLeft = Math.min(imgRight - boxSize, Math.max(imgLeft, moveStart.left + dx));
    boxTop = Math.min(imgBottom - boxSize, Math.max(imgTop, moveStart.top + dy));
  }

  // Corner drag: resize the square, keeping the opposite corner fixed as the anchor.
  let resizeStart = { x: 0, y: 0, cornerX: 0, cornerY: 0, ax: 0, ay: 0, dirX: 1, dirY: 1 };

  function handleDotPointerDown(event: PointerEvent, corner: Corner) {
    event.stopPropagation();
    const dirX = corner === "ne" || corner === "se" ? 1 : -1;
    const dirY = corner === "sw" || corner === "se" ? 1 : -1;
    // Anchor is the opposite (fixed) corner of the box at drag start.
    const ax = dirX > 0 ? boxLeft : boxLeft + boxSize;
    const ay = dirY > 0 ? boxTop : boxTop + boxSize;
    resizeStart = {
      x: event.clientX,
      y: event.clientY,
      cornerX: ax + dirX * boxSize,
      cornerY: ay + dirY * boxSize,
      ax,
      ay,
      dirX,
      dirY,
    };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function handleDotPointerMove(event: PointerEvent) {
    if (!event.buttons) return;
    const { ax, ay, dirX, dirY } = resizeStart;
    const pointerX = resizeStart.cornerX + (event.clientX - resizeStart.x);
    const pointerY = resizeStart.cornerY + (event.clientY - resizeStart.y);

    const rawDeltaX = dirX > 0 ? pointerX - ax : ax - pointerX;
    const rawDeltaY = dirY > 0 ? pointerY - ay : ay - pointerY;
    const maxSide = Math.min(
      dirX > 0 ? imgRight - ax : ax - imgLeft,
      dirY > 0 ? imgBottom - ay : ay - imgTop,
    );

    const side = Math.max(MIN_BOX, Math.min(Math.min(rawDeltaX, rawDeltaY), maxSide));
    boxLeft = dirX > 0 ? ax : ax - side;
    boxTop = dirY > 0 ? ay : ay - side;
    boxSize = side;
  }

  async function handleUpload() {
    if (!imgEl || !imgScale) return;

    const sx = (boxLeft - imgLeft) / imgScale;
    const sy = (boxTop - imgTop) / imgScale;
    const sSide = boxSize / imgScale;

    const canvas = document.createElement("canvas");
    canvas.width = OUTPUT_SIZE;
    canvas.height = OUTPUT_SIZE;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(imgEl, sx, sy, sSide, sSide, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE);

    const blob: Blob | null = await new Promise((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.92),
    );
    if (!blob) {
      status.show("Failed to process image", "error");
      return;
    }

    const cropped = new File([blob], "avatar.jpg", { type: "image/jpeg" });

    uploading = true;
    status.show("Uploading...", "info", null);
    try {
      await onUpload(cropped);
      close();
    } catch (e: any) {
      status.show(e.message || "Failed to upload", "error");
    } finally {
      uploading = false;
    }
  }
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />

  <div class="viewport" style="width: {CONTAINER_SIZE}px; height: {CONTAINER_SIZE}px;">
    <img
      bind:this={imgEl}
      src={previewUrl}
      alt=""
      draggable="false"
      class="full-img"
      style="left: {imgLeft}px; top: {imgTop}px; width: {imgDisplayWidth}px; height: {imgDisplayHeight}px;"
      onload={handleImgLoad}
    />

    {#if naturalWidth && naturalHeight}
      <div
        class="dim"
        style="left: {boxLeft}px; top: {boxTop}px; width: {boxSize}px; height: {boxSize}px;"
      ></div>

      <div
        class="circle-clip"
        style="left: {boxLeft}px; top: {boxTop}px; width: {boxSize}px; height: {boxSize}px;"
      >
        <div class="circle-fill"></div>
      </div>

      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div
        class="crop-box"
        style="left: {boxLeft}px; top: {boxTop}px; width: {boxSize}px; height: {boxSize}px;"
        onpointerdown={handleBoxPointerDown}
        onpointermove={handleBoxPointerMove}
      ></div>

      {#each corners as corner (corner.id)}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="handle handle-{corner.id}"
          style="left: {corner.x}px; top: {corner.y}px;"
          onpointerdown={(event) => handleDotPointerDown(event, corner.id)}
          onpointermove={handleDotPointerMove}
        ></div>
      {/each}
    {/if}
  </div>

  <div class="buttons">
    <Button variant="secondary" onclick={close} disabled={uploading}>Cancel</Button>
    <Button variant="primary" onclick={handleUpload} disabled={uploading}>Upload</Button>
  </div>
</div>

<style>
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: var(--color-bg-surface-alt);
    color: var(--color-text);
    padding: 20px;
    border-radius: 10px;
    gap: 16px;
  }

  .viewport {
    position: relative;
    border-radius: 8px;
  }

  .full-img {
    position: absolute;
    max-width: none;
    user-select: none;
    border-radius: 8px;
    -webkit-user-drag: none;
  }

  .dim {
    position: absolute;
    pointer-events: none;
  }

  .circle-clip {
    position: absolute;
    pointer-events: none;
  }

  .circle-fill {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    box-shadow: 0 0 0 9999px var(--color-crop-handle-shadow);
    outline: 2px solid white;
    outline-offset: -2px;
  }

  .crop-box {
    position: absolute;
    box-sizing: border-box;
    touch-action: none;
    cursor: move;
  }

  .handle {
    position: absolute;
    width: 16px;
    height: 16px;
    margin: -8px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 1px 3px var(--color-crop-overlay-shadow);
    touch-action: none;
  }

  .handle-nw {
    cursor: nwse-resize;
  }

  .handle-se {
    cursor: nwse-resize;
  }

  .handle-ne {
    cursor: nesw-resize;
  }

  .handle-sw {
    cursor: nesw-resize;
  }

  .buttons {
    display: flex;
    gap: 10px;
  }
</style>
