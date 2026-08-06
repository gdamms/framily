export type StatusType = "info" | "error" | "success";

export function createStatusMessage() {
  let text = $state("");
  let type: StatusType = $state("info");
  let timeout: ReturnType<typeof setTimeout> | null = null;

  function show(newText: string, newType: StatusType, ms: number | null = 3000) {
    text = newText;
    type = newType;
    if (timeout) clearTimeout(timeout);
    if (ms) {
      timeout = setTimeout(() => {
        text = "";
      }, ms);
    }
  }

  return {
    get text() {
      return text;
    },
    get type() {
      return type;
    },
    show,
  };
}
