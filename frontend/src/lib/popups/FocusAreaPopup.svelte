<script lang="ts">
  import { api, type FocusArea, type PictureInfo } from "$lib/api";
  import Button from "$lib/ui/Button.svelte";
  import StatusMessage from "$lib/ui/StatusMessage.svelte";
  import { createStatusMessage } from "$lib/ui/statusMessage.svelte";

  interface Props {
    picture: PictureInfo;
    onChanged?: () => void;
    close?: () => void;
  }

  let { picture, onChanged, close = () => {} }: Props = $props();

  const MIN_BOX = 24; // px, in container space

  type Corner = "nw" | "ne" | "sw" | "se";
  const CORNERS: Corner[] = ["nw", "ne", "sw", "se"];

  let imgEl: HTMLImageElement | undefined = $state();
  let viewportEl: HTMLDivElement | undefined = $state();
  let viewportWidth = $state(0);
  let viewportHeight = $state(0);
  let naturalWidth = $state(0);
  let naturalHeight = $state(0);
  let boxInitialized = $state(false);

  // The picture is displayed letterboxed ("contain") inside the viewport.
  let imgScale = $derived(
    naturalWidth && naturalHeight && viewportWidth && viewportHeight
      ? Math.min(viewportWidth / naturalWidth, viewportHeight / naturalHeight)
      : 0,
  );
  let imgDisplayWidth = $derived(naturalWidth * imgScale);
  let imgDisplayHeight = $derived(naturalHeight * imgScale);
  let imgLeft = $derived((viewportWidth - imgDisplayWidth) / 2);
  let imgTop = $derived((viewportHeight - imgDisplayHeight) / 2);
  let imgRight = $derived(imgLeft + imgDisplayWidth);
  let imgBottom = $derived(imgTop + imgDisplayHeight);

  // The focus box, in container-space (px).
  let boxLeft = $state(0);
  let boxTop = $state(0);
  let boxWidth = $state(0);
  let boxHeight = $state(0);

  let corners = $derived(
    CORNERS.map((id) => ({
      id,
      x: id === "nw" || id === "sw" ? boxLeft : boxLeft + boxWidth,
      y: id === "nw" || id === "ne" ? boxTop : boxTop + boxHeight,
    })),
  );

  const status = createStatusMessage();
  let saving = $state(false);

  function initBox() {
    const area = picture.focus_area;
    if (area) {
      boxLeft = imgLeft + area.x * imgDisplayWidth;
      boxTop = imgTop + area.y * imgDisplayHeight;
      boxWidth = area.width * imgDisplayWidth;
      boxHeight = area.height * imgDisplayHeight;
    } else {
      boxLeft = imgLeft;
      boxTop = imgTop;
      boxWidth = imgDisplayWidth;
      boxHeight = imgDisplayHeight;
    }
  }

  function handleImgLoad() {
    if (!imgEl) return;
    naturalWidth = imgEl.naturalWidth;
    naturalHeight = imgEl.naturalHeight;
  }

  // Wait for both the viewport size and the image's natural size before
  // placing the initial box - both are needed to compute imgLeft/imgTop.
  $effect(() => {
    if (!boxInitialized && naturalWidth && naturalHeight && viewportWidth && viewportHeight) {
      boxInitialized = true;
      initBox();
    }
  });

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
    boxLeft = Math.min(imgRight - boxWidth, Math.max(imgLeft, moveStart.left + dx));
    boxTop = Math.min(imgBottom - boxHeight, Math.max(imgTop, moveStart.top + dy));
  }

  // Corner drag: resize the box, keeping the opposite corner fixed as the
  // anchor. Width and height resize independently (unlike the avatar
  // cropper, this box isn't locked to a square). `cornerX`/`cornerY` record
  // the *dragged* corner's own starting position (not the anchor's) - the
  // pointer's current position is tracked relative to that, so the box
  // doesn't jump when the initial click isn't pixel-perfect on the handle.
  let resizeStart = { x: 0, y: 0, ax: 0, ay: 0, cornerX: 0, cornerY: 0, dirX: 1, dirY: 1 };

  function handleDotPointerDown(event: PointerEvent, corner: Corner) {
    event.stopPropagation();
    const dirX = corner === "ne" || corner === "se" ? 1 : -1;
    const dirY = corner === "sw" || corner === "se" ? 1 : -1;
    const ax = dirX > 0 ? boxLeft : boxLeft + boxWidth;
    const ay = dirY > 0 ? boxTop : boxTop + boxHeight;
    const cornerX = dirX > 0 ? boxLeft + boxWidth : boxLeft;
    const cornerY = dirY > 0 ? boxTop + boxHeight : boxTop;
    resizeStart = { x: event.clientX, y: event.clientY, ax, ay, cornerX, cornerY, dirX, dirY };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function handleDotPointerMove(event: PointerEvent) {
    if (!event.buttons) return;
    const { ax, ay, cornerX, cornerY, dirX, dirY, x, y } = resizeStart;
    const pointerX = cornerX + (event.clientX - x);
    const pointerY = cornerY + (event.clientY - y);

    if (dirX > 0) {
      const right = Math.min(imgRight, Math.max(ax + MIN_BOX, pointerX));
      boxLeft = ax;
      boxWidth = right - ax;
    } else {
      const left = Math.max(imgLeft, Math.min(ax - MIN_BOX, pointerX));
      boxLeft = left;
      boxWidth = ax - left;
    }

    if (dirY > 0) {
      const bottom = Math.min(imgBottom, Math.max(ay + MIN_BOX, pointerY));
      boxTop = ay;
      boxHeight = bottom - ay;
    } else {
      const top = Math.max(imgTop, Math.min(ay - MIN_BOX, pointerY));
      boxTop = top;
      boxHeight = ay - top;
    }
  }

  function useWholePicture() {
    boxLeft = imgLeft;
    boxTop = imgTop;
    boxWidth = imgDisplayWidth;
    boxHeight = imgDisplayHeight;
  }

  async function persist(focus_area: FocusArea | null) {
    saving = true;
    status.show("Saving...", "info", null);
    try {
      const response = await api.pictures.updateFocusArea(picture.id, focus_area);
      picture.focus_area = response.picture.focus_area ?? null;
      onChanged?.();
      close();
    } catch (e: any) {
      status.show(e.message || "Failed to save focus area", "error");
    } finally {
      saving = false;
    }
  }

  function handleSave() {
    if (!imgScale) return;
    persist({
      x: (boxLeft - imgLeft) / imgDisplayWidth,
      y: (boxTop - imgTop) / imgDisplayHeight,
      width: boxWidth / imgDisplayWidth,
      height: boxHeight / imgDisplayHeight,
    });
  }

  function handleClear() {
    persist(null);
  }
</script>

<div class="content">
  <p class="hint">
    Drag a rectangle over the part of the picture that should always stay in frame. When the
    frame's shape doesn't match the picture, it crops around this area instead of the center -
    adding black bars if needed to keep it fully visible.
  </p>

  <StatusMessage text={status.text} type={status.type} />

  <div class="viewport" bind:this={viewportEl} bind:clientWidth={viewportWidth} bind:clientHeight={viewportHeight}>
    <img
      bind:this={imgEl}
      src={api.pictures.getImageUrl(picture)}
      alt=""
      draggable="false"
      class="full-img"
      style="left: {imgLeft}px; top: {imgTop}px; width: {imgDisplayWidth}px; height: {imgDisplayHeight}px;"
      onload={handleImgLoad}
    />

    {#if naturalWidth && naturalHeight && boxInitialized}
      <div class="dim" style="clip-path: polygon(0% 0%, 0% 100%, {boxLeft}px 100%, {boxLeft}px {boxTop}px, {boxLeft + boxWidth}px {boxTop}px, {boxLeft + boxWidth}px {boxTop + boxHeight}px, {boxLeft}px {boxTop + boxHeight}px, {boxLeft}px 100%, 100% 100%, 100% 0%);"></div>

      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div
        class="crop-box"
        style="left: {boxLeft}px; top: {boxTop}px; width: {boxWidth}px; height: {boxHeight}px;"
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
    <Button class="small" variant="secondary" onclick={useWholePicture} disabled={saving}
      >Whole picture</Button
    >
    <Button class="small" variant="secondary" onclick={handleClear} disabled={saving}>Clear</Button>
    <div class="spacer"></div>
    <Button class="small" variant="secondary" onclick={close} disabled={saving}>Cancel</Button>
    <Button class="small" variant="primary" onclick={handleSave} disabled={saving}>Save</Button>
  </div>
</div>

<style>
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: var(--color-bg-surface-alt);
    color: var(--color-text);
    padding: 14px;
    border-radius: 10px;
    gap: 10px;
    width: fit-content;
    max-width: min(90vw, 480px);
  }

  .hint {
    margin: 0;
    width: 100%;
    font-size: 0.8rem;
    color: var(--color-text-secondary);
  }

  .viewport {
    position: relative;
    width: min(80vw, 420px);
    height: min(40vh, 320px);
  }

  .full-img {
    position: absolute;
    max-width: none;
    user-select: none;
    -webkit-user-drag: none;
    border-radius: 8px;
  }

  .dim {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .crop-box {
    position: absolute;
    box-sizing: border-box;
    border: 2px solid white;
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

  .handle-nw,
  .handle-se {
    cursor: nwse-resize;
  }

  .handle-ne,
  .handle-sw {
    cursor: nesw-resize;
  }

  .buttons {
    display: flex;
    align-items: center;
    width: 100%;
    gap: 8px;
    flex-wrap: wrap;
  }

  .spacer {
    flex: 1;
  }

  :global(.btn.small) {
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
  }
</style>
