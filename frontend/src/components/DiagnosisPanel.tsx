// Bloque «Diagnóstico con IA» del detalle de un incidente (spec 019): la IA local propone hipótesis y un borrador de runbook a partir de la evidencia
// real del incidente (métricas, registros y lo que la persona aporte). Es un borrador: se edita y se aprueba o se descarta; la IA no ejecuta nada y
// el diagnóstico nunca llega al portal del cliente. Si la IA no respondió o su texto no pasó las verificaciones, muestra el texto base con el motivo.
import { useCallback, useEffect, useState } from "react";

import { approveAiDraft, discardAiDraft, listAiDrafts, requestAiDiagnosis, type AiDraft } from "../api";
import { formatDateTime } from "../format";

const STATUS_LABELS = { borrador_ia: "Borrador", aprobado: "Aprobado", descartado: "Descartado" } as const;

interface Props {
  incidentId: number;
}

export default function DiagnosisPanel({ incidentId }: Props) {
  const [draft, setDraft] = useState<AiDraft | null>(null);
  const [text, setText] = useState("");
  const [extra, setExtra] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listAiDrafts(incidentId)
      .then((data) => {
        // El último diagnóstico que no se descartó es el vigente
        const vigente = data.find((d) => d.kind === "diagnostico" && d.status !== "descartado") ?? null;
        setDraft(vigente);
        if (vigente) setText(vigente.final_text ?? vigente.generated_text);
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

  const aportada = extra
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 8);

  return (
    <section className="card" aria-label="Diagnóstico con IA">
      <h2>Diagnóstico con IA</h2>
      <p className="muted">
        La IA local propone hipótesis y un borrador de runbook con las métricas y los registros del incidente. Son hipótesis sin confirmar: tú las revisas, y nada
        se ejecuta ni llega al cliente.
      </p>
      <label>
        Evidencia adicional (opcional, una por línea)
        <textarea
          rows={3}
          maxLength={2400}
          value={extra}
          onChange={(event) => setExtra(event.target.value)}
          placeholder="Por ejemplo: registro: OOMKilled en el contenedor web"
        />
      </label>
      <button type="button" className="button" disabled={busy} onClick={() => run(() => requestAiDiagnosis(incidentId, aportada))}>
        {busy ? "Analizando…" : draft ? "Analizar de nuevo" : "Pedir hipótesis a la IA"}
      </button>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {draft && (
        <div className="stacked-form" aria-label="Borrador de diagnóstico">
          <p className="muted">
            <strong>{STATUS_LABELS[draft.status]}</strong>
            {" · "}
            {draft.source === "llm" ? `Redactado por ${draft.model ?? "la IA"}${draft.latency_ms ? ` en ${draft.latency_ms} ms` : ""}` : "Texto base (no lo redactó la IA)"}
            {draft.approved_by && ` · Aprobado por ${draft.approved_by} el ${formatDateTime(draft.approved_at as string)}`}
          </p>
          {draft.notice && <p role="note">⚠ {draft.notice}</p>}
          <textarea
            aria-label="Texto del diagnóstico"
            rows={10}
            maxLength={4000}
            value={text}
            readOnly={draft.status !== "borrador_ia"}
            onChange={(event) => setText(event.target.value)}
          />
          {draft.status === "borrador_ia" && (
            <div className="button-row">
              <button type="button" className="button" disabled={busy} onClick={() => run(() => approveAiDraft(draft.id, text))}>
                Aprobar
              </button>
              <button type="button" className="button button-secondary" disabled={busy} onClick={() => run(() => discardAiDraft(draft.id))}>
                Descartar
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
