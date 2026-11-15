// Bloque «Borradores de IA» del detalle de un incidente mitigado: el asistente local redacta el resumen técnico y el mensaje al
// cliente, la persona los edita y los aprueba o los descarta (spec 012, principio 6). Si la IA no respondió, muestra el texto base
// con el motivo. Solo el mensaje aprobado llega al portal del cliente.
import { useCallback, useEffect, useState } from "react";

import { approveAiDraft, discardAiDraft, generateAiDrafts, listAiDrafts, type AiDraft, type AiDraftKind } from "../api";
import { formatDateTime } from "../format";

const KIND_LABELS: Record<AiDraftKind, string> = {
  resumen: "Resumen técnico (solo agencia)",
  mensaje_cliente: "Mensaje al cliente (llega al portal al aprobarlo)",
  diagnostico: "Diagnóstico con IA (solo agencia)",
};
const STATUS_LABELS = { borrador_ia: "Borrador", aprobado: "Aprobado", descartado: "Descartado" } as const;

interface Props {
  incidentId: number;
}

export default function AiDraftsPanel({ incidentId }: Props) {
  const [drafts, setDrafts] = useState<AiDraft[]>([]);
  const [texts, setTexts] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listAiDrafts(incidentId)
      .then((data) => {
        setDrafts(data);
        // Un borrador pendiente se edita sobre su texto generado; el que ya se resolvió no se toca
        setTexts((current) => {
          const next = { ...current };
          for (const draft of data) if (next[draft.id] === undefined) next[draft.id] = draft.final_text ?? draft.generated_text;
          return next;
        });
      })
      .catch((e: Error) => setError(e.message));
  }, [incidentId]);

  useEffect(load, [load]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // El último borrador de cada tipo es el vigente; los anteriores quedan en el historial
  const vigentes = (["resumen", "mensaje_cliente"] as AiDraftKind[])
    .map((kind) => drafts.find((draft) => draft.kind === kind))
    .filter((draft): draft is AiDraft => draft !== undefined);

  return (
    <section className="card" aria-label="Borradores de IA">
      <h2>Borradores de IA</h2>
      <p className="muted">
        El asistente local redacta; tú revisas, editas y apruebas. Nada llega al cliente sin tu aprobación, y la aprobación queda en la bitácora.
      </p>
      <button type="button" className="button" disabled={busy} onClick={() => run(() => generateAiDrafts(incidentId))}>
        {busy ? "Generando…" : vigentes.length ? "Generar de nuevo" : "Generar borradores"}
      </button>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {vigentes.map((draft) => (
        <div key={draft.id} className="stacked-form" aria-label={KIND_LABELS[draft.kind]}>
          <h3>{KIND_LABELS[draft.kind]}</h3>
          <p className="muted">
            <strong>{STATUS_LABELS[draft.status]}</strong>
            {" · "}
            {draft.source === "llm" ? `Redactado por ${draft.model ?? "la IA"}${draft.latency_ms ? ` en ${draft.latency_ms} ms` : ""}` : "Texto base (no lo redactó la IA)"}
            {draft.approved_by && ` · Aprobado por ${draft.approved_by} el ${formatDateTime(draft.approved_at as string)}`}
          </p>
          {draft.notice && <p role="note">⚠ {draft.notice}</p>}
          <textarea
            aria-label={`Texto del borrador: ${KIND_LABELS[draft.kind]}`}
            rows={draft.kind === "resumen" ? 5 : 3}
            maxLength={2000}
            value={texts[draft.id] ?? ""}
            readOnly={draft.status !== "borrador_ia"}
            onChange={(event) => setTexts({ ...texts, [draft.id]: event.target.value })}
          />
          {draft.status === "borrador_ia" && (
            <div className="button-row">
              <button type="button" className="button" disabled={busy} onClick={() => run(() => approveAiDraft(draft.id, texts[draft.id]))}>
                Aprobar
              </button>
              <button type="button" className="button button-secondary" disabled={busy} onClick={() => run(() => discardAiDraft(draft.id))}>
                Descartar
              </button>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}
