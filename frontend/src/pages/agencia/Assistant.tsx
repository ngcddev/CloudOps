// Asistente de ayuda de la consola (spec 012): se pregunta cómo usar el Hub; una compuerta de ML decide si hace
// falta despertar al LLM local. Cada respuesta dice quién la dio, y la persona puede corregir la decisión
// («era / no era del Hub»); el panel mide cuánto LLM se evitó y cuántas decisiones se corrigieron.
import { useCallback, useEffect, useRef, useState } from "react";

import {
  askAssistant,
  getAssistantDrift,
  getAssistantStats,
  getVoiceStatus,
  sendAssistantFeedback,
  speakText,
  type AssistantAnswer,
  type AssistantDrift,
  type AssistantStats,
  type GateLabel,
} from "../../api";
import VoiceInput from "../../components/VoiceInput";

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
  const [drift, setDrift] = useState<AssistantDrift | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    try {
      // Independientes: en paralelo, no una detrás de otra (auditoría FE-07)
      const [estadisticas, deriva] = await Promise.all([getAssistantStats(), getAssistantDrift()]);
      setStats(estadisticas);
      setDrift(deriva);
    } catch (statsError) {
      setError((statsError as Error).message);
    }
  }, []);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  // Voz (spec 021): si el servicio responde se puede dictar y escuchar la respuesta; la preferencia de leer en voz alta se recuerda en este navegador
  const [vozDisponible, setVozDisponible] = useState(false);
  const [leerRespuestas, setLeerRespuestas] = useState(() => {
    try {
      return window.localStorage.getItem("asistente.leerRespuestas") !== "no";
    } catch {
      return true;
    }
  });
  const [habla, setHabla] = useState<"callado" | "preparando" | "hablando">("callado");
  const audio = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    getVoiceStatus()
      .then((estado) => setVozDisponible(estado.disponible))
      .catch(() => setVozDisponible(false));
  }, []);

  const callar = useCallback(() => {
    if (audio.current) {
      audio.current.pause();
      audio.current = null;
    }
    setHabla("callado");
  }, []);

  useEffect(() => callar, [callar]);

  function cambiarLeer(valor: boolean) {
    setLeerRespuestas(valor);
    if (!valor) callar();
    try {
      window.localStorage.setItem("asistente.leerRespuestas", valor ? "si" : "no");
    } catch {
      // sin almacenamiento del navegador solo se pierde la preferencia
    }
  }

  async function leerEnVoz(texto: string) {
    callar();
    setHabla("preparando");
    try {
      const url = URL.createObjectURL(await speakText(texto));
      const reproductor = new Audio(url);
      audio.current = reproductor;
      const terminar = () => {
        URL.revokeObjectURL(url);
        if (audio.current === reproductor) {
          audio.current = null;
          setHabla("callado");
        }
      };
      reproductor.onended = terminar;
      reproductor.onerror = terminar;
      setHabla("hablando");
      await reproductor.play();
    } catch (e) {
      setHabla("callado");
      // Sin voz la respuesta ya está en pantalla: solo se avisa
      setError(`No se pudo leer la respuesta en voz alta: ${(e as Error).message}`);
    }
  }

  async function enviar(texto: string) {
    const text = texto.trim();
    if (text.length < 3 || busy) return;
    setBusy(true);
    setError(null);
    try {
      const answer = await askAssistant(text);
      setTurns((current) => [{ question: text, answer, feedback: null }, ...current]);
      setQuestion("");
      void loadStats();   // las estadísticas no retrasan la respuesta hablada (auditoría FE-07)
      if (vozDisponible && leerRespuestas) void leerEnVoz(answer.answer);
    } catch (askError) {
      setError((askError as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await enviar(question);
  }

  // Lo dictado queda en el cuadro para corregirlo; con «enviar sin revisar» se manda de una vez
  const alTranscribir = useCallback(
    (texto: string, mandar: boolean) => {
      setQuestion(texto);
      if (mandar) void enviar(texto);
    },
    [busy, vozDisponible, leerRespuestas],
  );

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
        <VoiceInput onTranscript={alTranscribir} onStart={callar} disabled={busy} />
        {vozDisponible && (
          <div className="voice-output">
            <label className="muted voice-option">
              <input type="checkbox" checked={leerRespuestas} onChange={(event) => cambiarLeer(event.target.checked)} /> Leer las respuestas en voz alta
            </label>
            <p className="muted" role="status" aria-live="polite">
              {busy ? "Pensando la respuesta…" : habla === "preparando" ? "Preparando la voz…" : habla === "hablando" ? "Hablando…" : ""}
              {habla === "hablando" && (
                <>
                  {" "}
                  <button type="button" className="button button-secondary" onClick={callar}>
                    Callar
                  </button>
                </>
              )}
            </p>
          </div>
        )}
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
        {stats === null && !error && <p className="muted" role="status">Cargando…</p>}
        {drift !== null && drift.avisos.length > 0 && (
          <div role="note" aria-label="Deriva del asistente">
            <h3>Deriva en los últimos {drift.ventana_dias} días</h3>
            <ul>
              {drift.avisos.map((aviso) => (
                <li key={aviso.codigo}>⚠ {aviso.mensaje}</li>
              ))}
            </ul>
          </div>
        )}
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
