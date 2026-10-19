import {
  BleClient,
  dataViewToText,
  numbersToDataView,
  textToDataView,
  type ScanResult,
} from "@capacitor-community/bluetooth-le";

// Must match the UUIDs frame/ble/main.py advertises.
export const SERVICE_UUID = "7e6a1000-a2f0-4a9e-8f3c-1a2b3c4d5e00";
const SSID_CHAR_UUID = "7e6a1001-a2f0-4a9e-8f3c-1a2b3c4d5e00";
const PASSWORD_CHAR_UUID = "7e6a1002-a2f0-4a9e-8f3c-1a2b3c4d5e00";
const SERVER_URL_CHAR_UUID = "7e6a1003-a2f0-4a9e-8f3c-1a2b3c4d5e00";
const SUBMIT_CHAR_UUID = "7e6a1004-a2f0-4a9e-8f3c-1a2b3c4d5e00";
const STATUS_CHAR_UUID = "7e6a1005-a2f0-4a9e-8f3c-1a2b3c4d5e00";

export type ProvisioningStatus =
  | "idle"
  | "connecting_wifi"
  | "wifi_failed"
  | "registering"
  | "server_failed"
  | "success";

export interface ProvisioningState {
  status: ProvisioningStatus;
  message: string;
  framily_code: string;
  created_new_framily: boolean;
}

export interface DiscoveredFrame {
  deviceId: string;
  name: string;
}

let initialized = false;

async function ensureInitialized(): Promise<void> {
  if (initialized) return;
  await BleClient.initialize();
  initialized = true;
}

export async function scanForFrames(
  onDiscovered: (frame: DiscoveredFrame) => void,
): Promise<void> {
  await ensureInitialized();
  const seen = new Set<string>();
  await BleClient.requestLEScan({ services: [SERVICE_UUID] }, (result: ScanResult) => {
    if (seen.has(result.device.deviceId)) return;
    seen.add(result.device.deviceId);
    onDiscovered({
      deviceId: result.device.deviceId,
      name: result.localName || result.device.name || "Unknown frame",
    });
  });
}

export async function stopScan(): Promise<void> {
  await BleClient.stopLEScan();
}

export async function connectToFrame(
  deviceId: string,
  onDisconnect?: () => void,
): Promise<void> {
  await BleClient.connect(deviceId, onDisconnect ? () => onDisconnect() : undefined);
}

export async function disconnectFromFrame(deviceId: string): Promise<void> {
  await BleClient.disconnect(deviceId);
}

export async function submitCredentials(
  deviceId: string,
  ssid: string,
  password: string,
  serverUrl: string,
): Promise<void> {
  await BleClient.write(deviceId, SERVICE_UUID, SSID_CHAR_UUID, textToDataView(ssid));
  await BleClient.write(deviceId, SERVICE_UUID, PASSWORD_CHAR_UUID, textToDataView(password));
  await BleClient.write(deviceId, SERVICE_UUID, SERVER_URL_CHAR_UUID, textToDataView(serverUrl));
  // Payload doesn't matter - the frame treats any write to this characteristic
  // as "apply the three fields above now".
  await BleClient.write(deviceId, SERVICE_UUID, SUBMIT_CHAR_UUID, numbersToDataView([1]));
}

function parseStatus(value: DataView): ProvisioningState {
  try {
    const parsed = JSON.parse(dataViewToText(value));
    return {
      status: parsed.status ?? "idle",
      message: parsed.message ?? "",
      framily_code: parsed.framily_code ?? "",
      created_new_framily: !!parsed.created_new_framily,
    };
  } catch {
    return { status: "idle", message: "", framily_code: "", created_new_framily: false };
  }
}

export async function watchProvisioningStatus(
  deviceId: string,
  onUpdate: (state: ProvisioningState) => void,
): Promise<void> {
  await BleClient.startNotifications(deviceId, SERVICE_UUID, STATUS_CHAR_UUID, (value) => {
    onUpdate(parseStatus(value));
  });
}

export async function readProvisioningStatus(deviceId: string): Promise<ProvisioningState> {
  const value = await BleClient.read(deviceId, SERVICE_UUID, STATUS_CHAR_UUID);
  return parseStatus(value);
}
