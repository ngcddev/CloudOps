// Asistente de ayuda de la consola (spec 012): se pregunta cómo usar el Hub; una compuerta de ML decide si hace
// falta despertar al LLM local. Cada respuesta dice quién la dio, y la persona puede corregir la decisión
// («era / no era del Hub»); el panel mide cuánto LLM se evitó y cuántas decisiones se corrigieron.
import { useCallback, useEffect, useState } from "react";

import {
  askAssistant,
  getAssistantStats,
  sendAssistantFeedback,
  type AssistantAnswer,
  type AssistantStats,
  type GateLabel,
} from "../../api";

interface Turn {
  question: string;
  answer: AssistantAnswer;
  // Lo que la persona marcó; nulo = sin opinar
  feedback: GateLabel | null;
}

const pct = (value: number | null) => (value === null ? "—" : `${value.toLocaleString("es-CO")} %`);

export default function Assistant() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [stats, setStats] = useState<AssistantStats | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    try {
      setStats(await getAssistantStats());
    } catch (statsError) {
      setError((statsError as Error).message);
    }
  }, []);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (text.length < 3 || busy) return;
    setBusy(true);
    setError(null);
    try {
      const answer = await askAssistant(text);
      setTurns((current) => [{ question: text, answer, feedback: null }, ...current]);
      setQuestion("");
      await loadStats();
    } catch (askError) {
      setError((askError as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function opine(id: number, label: GateLabel) {
    try {
      await sendAssistantFeedback(id, label);
      setTurns((current) => current.map((turn) => (turn.answer.id === id ? { ...turn, feedback: label } : turn)));
      await loadStats();
    } catch (feedbackError) {
      setError((feedbackError as Error).message);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>Asistente</h1>
        <p className="muted">
          Pregunta cómo usar el Hub. Una compuerta decide si la pregunta trata del Hub antes de despertar a la IA
          local; si no, responde ella sola. El asistente solo informa: no aprueba, publica ni hace rollback.
        </p>
      </div>

      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}

      <section className="card">
        <form className="assistant-form" onSubmit={submit}>
          <label className="field" style={{ flex: "1 1 280px" }}>
            <span>Tu pregunta</span>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              maxLength={500}
              placeholder="Por ejemplo: ¿Cómo abro un incidente manual?"
            />
          </label>
          <button className="button button-primary" type="submit" disabled={busy || question.trim().length < 3}>
            {busy ? "Consultando…" : "Preguntar"}
          </button>
        </form>
      </section>

      {turns.length > 0 && (
        <section className="card" aria-live="polite">
          {turns.map(({ question: asked, answer, feedback }) => (
            <article className="assistant-turn" key={answer.id}>
              <p className="assistant-question">{asked}</p>
              <p className="assistant-answer">{answer.answer}</p>
              <div className="assistant-meta">
                <span className="assistant-by">
                  {answer.answered_by === "llm"
                    ? answer.llm_ok === false
                      ? "! IA sin respuesta"
                      : "✓ Respondió la IA local"
                    : answer.answered_by === "ayuda"
                      ? "Sin información en la ayuda · IA dormida"
                      : "Respondió la compuerta · IA dormida"}
                </span>
                <span className="muted">
                  Probabilidad de que sea ajena al Hub: {Math.round(answer.p_fuera_de_tema * 100)} %
                  {answer.latency_ms !== null && ` · ${answer.latency_ms} ms`}
                  {answer.model && ` · ${answer.model}`}
                </span>
                {answer.answered_by === "llm" && answer.llm_ok !== false && answer.context_sections.length > 0 && (
                  <span className="muted">
                    Basada en la ayuda del Hub
                    {(answer.context_mode ? answer.context_mode === "completo" : answer.context_sections.length > 3)
                      ? " (completa)"
                      : `: ${answer.context_sections.join(" · ")}`}
                    {answer.context_mode === "rag" && answer.retrieval_score != null &&
                      ` · similitud ${answer.retrieval_score.toLocaleString("es-CO", { maximumFractionDigits: 2 })}`}
                  </span>
                )}
                {feedback === null ? (
                  <span>
                    <button className="button button-secondary" type="button" onClick={() => opine(answer.id, "en_tema")}>
                      Era del Hub
                    </button>{" "}
                    <button className="button button-secondary" type="button" onClick={() => opine(answer.id, "fuera_de_tema")}>
                      No era del Hub
                    </button>
                  </span>
                ) : (
                  <span className="muted">
                    ✓ Marcaste: {feedback === "en_tema" ? "era del Hub" : "no era del Hub"}
                    {feedback !== answer.gate_label && " (corrige a la compuerta)"}
                  </span>
                )}
              </div>
            </article>
          ))}
        </section>
      )}

      <section className="card">
        <div className="card-header">
          <h3>Qué tanto trabaja la IA</h3>
          <span className="muted">Se calcula con todas las preguntas de la agencia</span>
        </div>
        {stats === null && !error && <p className="muted">Cargando…</p>}
        {stats !== null && stats.total === 0 && <p>Todavía no hay preguntas. Haz la primera arriba.</p>}
        {stats !== null && stats.total > 0 && (
          <dl className="assistant-stats">
            <div>
              <dt>Preguntas</dt>
              <dd>{stats.total}</dd>
            </div>
            <div>
              <dt>IA local evitada</dt>
              <dd>{pct(stats.llm_evitado_pct)}</dd>
            </div>
            <div>
              <dt>Veces que despertó la IA</dt>
              <dd>{stats.llm_despertado}</dd>
            </div>
            <div>
              <dt>IA sin respuesta</dt>
              <dd>{stats.llm_sin_respuesta}</dd>
            </div>
            <div>
              <dt>Tiempo medio de la IA</dt>
              <dd>{stats.latencia_llm_ms === null ? "—" : `${stats.latencia_llm_ms} ms`}</dd>
            </div>
            <div>
              <dt>Decisiones corregidas</dt>
              <dd>{pct(stats.decisiones_corregidas_pct)}</dd>
            </div>
          </dl>
        )}
      </section>
    </>
  );
}
