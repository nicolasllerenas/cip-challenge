import { CheckCircle2, Undo2, X } from "lucide-react";
import { useEffect } from "react";
import { Kbd } from "./ui";

export interface ToastState {
  id: number;
  message: string;
  onUndo?: () => void;
}

export function Toast({ toast, onDismiss }: { toast: ToastState | null; onDismiss: () => void }) {
  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(onDismiss, 8000);
    return () => window.clearTimeout(timer);
  }, [toast, onDismiss]);

  return (
    <div role="status" aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-14 z-30 flex justify-center px-4">
      {toast && (
        <div key={toast.id} className="rise pointer-events-auto flex items-center gap-3 rounded-xl bg-ink px-4 py-3 text-paper shadow-xl">
          <CheckCircle2 aria-hidden className="size-5 text-moss-wash" />
          <span>{toast.message}</span>
          {toast.onUndo && (
            <button
              type="button"
              onClick={toast.onUndo}
              className="ml-2 inline-flex items-center gap-1.5 rounded-lg px-2 py-1 font-bold text-accent-wash hover:bg-paper/10"
            >
              <Undo2 aria-hidden className="size-4" /> Deshacer <Kbd>Ctrl+Z</Kbd>
            </button>
          )}
          <button type="button" onClick={onDismiss} aria-label="Cerrar aviso" className="rounded-md p-1 hover:bg-paper/10">
            <X aria-hidden className="size-4" />
          </button>
        </div>
      )}
    </div>
  );
}
