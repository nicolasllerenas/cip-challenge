import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "./api/client";
import type { LibrarySummary } from "./api/types";
import { Shell, type Section } from "./components/Shell";
import { Banner } from "./components/ui";
import { useConnection, useStored, useUiScale } from "./hooks";
import { ComposeScreen } from "./screens/ComposeScreen";
import { DraftsScreen } from "./screens/DraftsScreen";
import { LibraryScreen } from "./screens/LibraryScreen";
import { Onboarding } from "./screens/Onboarding";
import { ReviewScreen } from "./screens/ReviewScreen";
import { RunScreen } from "./screens/RunScreen";

type View =
  | { name: "onboarding" }
  | { name: "library" }
  | { name: "compose" }
  | { name: "run"; jobId: string }
  | { name: "review"; draftId: string }
  | { name: "drafts" };

const SECTION_OF: Record<View["name"], Section | null> = {
  onboarding: null,
  library: "library",
  compose: "compose",
  run: "compose",
  review: "drafts",
  drafts: "drafts",
};

export function App() {
  const [onboarded, setOnboarded] = useStored("cip.onboarded", false);
  const [libraryId, setLibraryId] = useStored<string | null>("cip.libraryId", null);
  const [ingestJobId, setIngestJobId] = useStored<string | null>("cip.ingestJob", null);
  const [activeRun, setActiveRun] = useStored<string | null>("cip.activeRun", null);
  const [runPrompt, setRunPrompt] = useStored("cip.runPrompt", "");
  const [library, setLibrary] = useState<LibrarySummary | null>(null);
  const [libraryError, setLibraryError] = useState<string | null>(null);
  const [view, setView] = useState<View>(() =>
    !onboarded ? { name: "onboarding" } : activeRun ? { name: "run", jobId: activeRun } : { name: libraryId ? "compose" : "library" },
  );
  const { connection, health } = useConnection();
  const [scale, setScale] = useUiScale();

  const refreshLibrary = useCallback(async () => {
    if (!libraryId) return;
    try {
      setLibrary(await api.library(libraryId));
      setLibraryError(null);
    } catch (failure) {
      setLibraryError(failure instanceof ApiError ? failure.message : "No pude cargar tu biblioteca.");
    }
  }, [libraryId]);

  useEffect(() => {
    refreshLibrary();
  }, [refreshLibrary, connection === "ok"]);

  useEffect(() => {
    document.querySelector<HTMLElement>("[data-screen-title]")?.focus({ preventScroll: true });
  }, [view]);

  const navigate = (section: Section) =>
    setView(section === "compose" && activeRun ? { name: "run", jobId: activeRun } : ({ name: section } as View));

  const finishOnboarding = (target: View) => {
    setOnboarded(true);
    setView(target);
  };

  return (
    <Shell
      active={SECTION_OF[view.name]}
      onNavigate={navigate}
      onHelp={() => setView({ name: "onboarding" })}
      connection={connection}
      services={health?.services ?? []}
      library={library}
      scale={scale}
      onScale={setScale}
    >
      {connection === "offline" && (
        <div className="mx-10 mt-6">
          <Banner kind="error" title="No me puedo comunicar con el asistente">
            Si acabas de abrir la app, espera unos segundos. Si persiste, ciérrala y vuelve a abrirla.
          </Banner>
        </div>
      )}
      {libraryError && connection === "ok" && view.name !== "onboarding" && (
        <div className="mx-10 mt-6">
          <Banner kind="warning" title={libraryError} />
        </div>
      )}
      {view.name === "onboarding" && (
        <Onboarding onStart={() => finishOnboarding({ name: "library" })} onSkip={() => finishOnboarding({ name: libraryId ? "compose" : "library" })} />
      )}
      {view.name === "library" && (
        <LibraryScreen
          key={ingestJobId ?? "idle"}
          library={library}
          ingestJobId={ingestJobId}
          onOpened={(summary, jobId) => {
            setLibraryId(summary.library_id);
            setLibrary(summary);
            setIngestJobId(jobId);
          }}
          onReset={() => {
            setLibraryId(null);
            setLibrary(null);
            setIngestJobId(null);
          }}
          onIngestJob={setIngestJobId}
          onRefresh={refreshLibrary}
          onCompose={() => setView({ name: "compose" })}
        />
      )}
      {view.name === "compose" && (
        <ComposeScreen
          library={library}
          onOpenLibrary={() => setView({ name: "library" })}
          onStarted={(jobId, prompt) => {
            setRunPrompt(prompt);
            setActiveRun(jobId);
            setView({ name: "run", jobId });
          }}
        />
      )}
      {view.name === "run" && (
        <RunScreen
          key={view.jobId}
          jobId={view.jobId}
          prompt={runPrompt}
          onReview={(draftId) => {
            setActiveRun(null);
            setView({ name: "review", draftId });
          }}
          onAdjust={() => {
            setActiveRun(null);
            setView({ name: "compose" });
          }}
        />
      )}
      {view.name === "review" && <ReviewScreen key={view.draftId} draftId={view.draftId} />}
      {view.name === "drafts" && (
        <DraftsScreen onOpen={(draftId) => setView({ name: "review", draftId })} onCompose={() => setView({ name: "compose" })} />
      )}
    </Shell>
  );
}
