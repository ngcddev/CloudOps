// Bloque «Borradores» del detalle de un incidente mitigado: el asistente propone el resumen y el mensaje al
// cliente, el técnico los edita y los aprueba o descarta; si el asistente no responde, se escribe a mano (spec 012).
import { useCallback, useEffect, useState } from "react";

import {
  approveDraft,
  createManualDraft,
  discardDraft,
  generateDrafts,
  listDrafts,
  type AiDraft,
  type DraftKind,
  type IncidentDetail,
  type IncidentDrafts,
} from "../api";
import { formatDateTime } from "../format";

// Lo que el Hub espera al asistente (AI_TIMEOUT_SECONDS) más un margen para la red
const ASSISTANT_WAIT_MS = 62_000;

const KINDS: { kind: DraftKind; label: string; hint: string }[] = [
  { kind: "resumen", label: "Resumen técnico", hint: "Solo lo ve la agencia." },
  { kind: "mensaje_cliente", label: "Mensaje al cliente", hint: "Al aprobarlo, el cliente lo ve en su portal." },
];

// Texto de los estados del glosario; el estado se dice con ícono y texto, no con color
const STATUS_LABELS: Record<AiDraft["status"], string> = {
  borrador_ia: "● Borrador",
  aprobado: "✓ Aprobado",
  descartado: "○ Descartado",
};

class AssistantTimeout extends Error {}

interface Props {
  incident: IncidentDetail;
}

export default function DraftsPanel({ incident }: Props) {
  const [data, setData] = useState<IncidentDrafts | null>(null);
  // Texto editado de cada borrador pendiente, por id
  const [edits, setEdits] = useState<Record<number, string>>({});
  // Textos a mano por tipo; nulo = el editor a mano está cerrado
  const [manual, setManual] = useState<Record<DraftKind, string> | null>(null);
  const [problems, setProblems] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    listDrafts(incident.id)
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [incident.id]);

  useEffect(load, [load, incident.mitigated_at]);

  function openManual(templates = data?.manual_templates) {
    setManual({ resumen: templates?.resumen ?? "", mensaje_cliente: templates?.mensaje_cliente ?? "" });
  }

  async function generate() {
    setGenerating(true);
    setError(null);
    setProblems([]);
    let timer = 0;
    try {
      // Si la API no contesta a tiempo no se espera más: el técnico sigue a mano (CA-5)
      const timeout = new Promise<never>((_, reject) => {
        timer = window.setTimeout(() => reject(new AssistantTimeout()), ASSISTANT_WAIT_MS);
      });
      const result = await Promise.race([generateDrafts(incident.id), timeout]);
      setProblems(result.problems);
      load();
    } catch (err) {
      setError(
        err instanceof AssistantTimeout
          ? "El asistente no respondió en 60 segundos. Escribe el texto a mano: el borrador se prellena con los datos reales del incidente."
          : (err as Error).message,
      );
      openManual();
    } finally {
      window.clearTimeout(timer);
      setGenerating(false);
    }
  }

  // Corre una acción sobre un borrador y vuelve a pedir la lista
  async function act(action: () => Promise<unknown>, after?: () => void) {
    setBusy(true);
    setError(null);
    try {
      await action();
      after?.();
      load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function saveManual(kind: DraftKind) {
    const text = manual?.[kind] ?? "";
    act(
      () => createManualDraft(incident.id, kind, text),
      () => setManual((current) => (current ? { ...current, [kind]: "" } : current)),
    );
  }

  if (incident.mitigated_at === null) return null;

  const drafts = data?.drafts ?? [];

  return (
    <section className="card" aria-label="Borradores">
      <h2>Borradores</h2>
      <p className="muted">
        El asistente local propone el resumen y el mensaje con los datos reales del incidente. Nada llega al cliente
        hasta que alguien de la agencia lo aprueba.
      </p>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}
      {problems.map((problem) => (
        <p key={problem} className="notice" role="status">
          ⚠ No se guardó: {problem}
        </p>
      ))}

      <div className="button-row">
        <button type="button" className="button" disabled={generating || busy} onClick={generate}>
          {generating ? "Generando… (hasta 60 s)" : "Generar borradores"}
        </button>
        {manual === null && (
          <button type="button" className="button button-secondary" disabled={generating} onClick={() => openManual()}>
            Escribir a mano
          </button>
        )}
      </div>

      {KINDS.map(({ kind, label, hint }) => {
        const ofKind = drafts.filter((draft) => draft.kind === kind);
        const approved = ofKind.find((draft) => draft.status === "aprobado");
        const pending = ofKind.filter((draft) => draft.status === "borrador_ia");
        const discarded = ofKind.filter((draft) => draft.status === "descartado");
        return (
          <div key={kind} className="draft-group">
            <h3>{label}</h3>
            <p className="muted">{hint}</p>

            {approved && (
              <div className="draft">
                <p>
                  <span className="status-pill">{STATUS_LABELS.aprobado}</span> por {approved.approved_by_name} ·{" "}
                  {formatDateTime(approved.approved_at)}
                </p>
                <p className="draft-text">{approved.final_text}</p>
              </div>
            )}

            {pending.map((draft) => {
              const text = edits[draft.id] ?? draft.generated_text;
              return (
                <div key={draft.id} className="draft stacked-form">
                  <p>
                    <span className="status-pill">{STATUS_LABELS.borrador_ia}</span>{" "}
                    {draft.model === "manual"
                      ? `escrito a mano por ${draft.created_by_name}`
                      : `${draft.model} · instrucciones ${draft.prompt_version} · ${((draft.latency_ms ?? 0) / 1000).toLocaleString("es-CO", { maximumFractionDigits: 1 })} s`}
                  </p>
                  <label>
                    Texto (puedes editarlo antes de aprobar)
                    <textarea
                      value={text}
                      rows={4}
                      maxLength={4000}
                      onChange={(event) => setEdits((current) => ({ ...current, [draft.id]: event.target.value }))}
                    />
                  </label>
                  <div className="button-row">
                    <button
                      type="button"
                      className="button"
                      disabled={busy || !text.trim()}
                      onClick={() => act(() => approveDraft(draft.id, text))}
                    >
                      Aprobar
                    </button>
                    <button
                      type="button"
                      className="button button-secondary"
                      disabled={busy}
                      onClick={() => act(() => discardDraft(draft.id))}
                    >
                      Descartar
                    </button>
                  </div>
                </div>
              );
            })}

            {manual !== null && (
              <div className="draft stacked-form">
                <label>
                  Escribir a mano (prellenado con los datos reales)
                  <textarea
                    value={manual[kind]}
                    rows={4}
                    maxLength={4000}
                    onChange={(event) => setManual({ ...manual, [kind]: event.target.value })}
                  />
                </label>
                <div className="button-row">
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={busy || !manual[kind].trim()}
                    onClick={() => saveManual(kind)}
                  >
                    Guardar como borrador
                  </button>
                </div>
              </div>
            )}

            {!approved && pending.length === 0 && manual === null && (
              <p className="muted">Todavía no hay borradores.</p>
            )}

            {discarded.length > 0 && (
              <details>
                <summary className="muted">
                  {discarded.length === 1 ? "1 borrador descartado" : `${discarded.length} borradores descartados`}
                </summary>
                <ul className="history-list">
                  {discarded.map((draft) => (
                    <li key={draft.id}>
                      <span className="muted">
                        {STATUS_LABELS.descartado} · {draft.model === "manual" ? "a mano" : draft.model} ·{" "}
                        {formatDateTime(draft.created_at)}
                      </span>
                      <div>{draft.final_text ?? draft.generated_text}</div>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        );
      })}
    </section>
  );
}
