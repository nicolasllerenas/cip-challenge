import { isTauri } from "@tauri-apps/api/core";

export const inDesktop = (): boolean => isTauri();

export const gatewayBase = (): string => (inDesktop() ? "http://127.0.0.1:8000" : "");

export async function pickFolder(): Promise<string | null> {
  if (!inDesktop()) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const selected = await open({ directory: true, multiple: false, title: "Elige la carpeta con tus artículos en PDF" });
  return typeof selected === "string" ? selected : null;
}

export async function openLocalFile(path: string, browserUrl: string): Promise<void> {
  if (!inDesktop()) {
    window.open(browserUrl, "_blank", "noopener");
    return;
  }
  const { openPath } = await import("@tauri-apps/plugin-opener");
  await openPath(path);
}

export async function revealLocalFile(path: string): Promise<void> {
  if (!inDesktop()) return;
  const { revealItemInDir } = await import("@tauri-apps/plugin-opener");
  await revealItemInDir(path);
}

export async function openExternal(url: string): Promise<void> {
  if (!inDesktop()) {
    window.open(url, "_blank", "noopener");
    return;
  }
  const { openUrl } = await import("@tauri-apps/plugin-opener");
  await openUrl(url);
}

export async function prepareNotifications(): Promise<void> {
  try {
    if (inDesktop()) {
      const { isPermissionGranted, requestPermission } = await import("@tauri-apps/plugin-notification");
      if (!(await isPermissionGranted())) await requestPermission();
      return;
    }
    if ("Notification" in window && Notification.permission === "default") await Notification.requestPermission();
  } catch {
    return;
  }
}

export async function notifyInBackground(title: string, body: string): Promise<void> {
  if (!document.hidden && document.hasFocus()) return;
  try {
    if (inDesktop()) {
      const { isPermissionGranted, sendNotification } = await import("@tauri-apps/plugin-notification");
      if (await isPermissionGranted()) sendNotification({ title, body });
      return;
    }
    if ("Notification" in window && Notification.permission === "granted") new Notification(title, { body });
  } catch {
    return;
  }
}
