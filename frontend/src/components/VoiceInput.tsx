// Entrada por voz del asistente (spec 021): pulsar para hablar, ver lo que entendió y, si se quiere, enviarlo de una vez. Graba con el micrófono del navegador
// (webm/opus), manda el audio a la API del Hub (no se guarda) y devuelve el texto. El micrófono solo se ofrece si el servicio de voz responde y el navegador lo
// permite: necesita HTTPS o localhost. Una charla por turnos: no hay escucha permanente.
import { useCallback, useEffect, useRef, useState } from "react";

import { getVoiceStatus, transcribeAudio, type VoiceStatus } from "../api";

const MAX_SECONDS = 30;

type Phase = "inicio" | "grabando" | "transcribiendo";

interface Props {
  // Lo que se entendió; `enviar` es true si la persona pidió mandarlo sin revisar
  onTranscript: (text: string, enviar: boolean) => void;
  // Se llama al empezar a grabar (para callar la respuesta que se esté leyendo)
  onStart?: () => void;
  disabled?: boolean;
}

export default function VoiceInput({ onTranscript, onStart, disabled = false }: Props) {
  const [estado, setEstado] = useState<VoiceStatus | null>(null);
  const [fase, setFase] = useState<Phase>("inicio");
  const [segundos, setSegundos] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [enviarSinRevisar, setEnviarSinRevisar] = useState(false);
  const grabadora = useRef<MediaRecorder | null>(null);
  const trozos = useRef<Blob[]>([]);
  const temporizador = useRef<number | null>(null);
  const flujo = useRef<MediaStream | null>(null);
  const enviarRef = useRef(false);
  // La grabación termina más tarde que el render que la empezó: siempre se llama a la versión vigente
  const alTranscribirRef = useRef(onTranscript);
  alTranscribirRef.current = onTranscript;

  useEffect(() => {
    getVoiceStatus()
      .then(setEstado)
      .catch(() => setEstado({ habilitada: false, disponible: false }));
  }, []);

  const soportaMicrofono = typeof window !== "undefined" && window.isSecureContext && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";

  const liberar = useCallback(() => {
    if (temporizador.current !== null) window.clearInterval(temporizador.current);
    temporizador.current = null;
    flujo.current?.getTracks().forEach((pista) => pista.stop());
    flujo.current = null;
  }, []);

  useEffect(() => liberar, [liberar]);

  const transcribir = useCallback(
    async (audio: Blob) => {
      setFase("transcribiendo");
      try {
        const resultado = await transcribeAudio(audio);
        if (!resultado.text.trim()) {
          setError("No se entendió nada. Habla más cerca del micrófono e inténtalo de nuevo.");
        } else {
          if (resultado.secrets_redacted.length > 0) setError("Se taparon claves o contraseñas que dijiste: no las dictes en voz alta.");
          alTranscribirRef.current(resultado.text, enviarRef.current);
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setFase("inicio");
      }
    },
    [],
  );

  async function empezar() {
    setError(null);
    onStart?.();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      flujo.current = stream;
      const tipo = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/webm"].find((t) => MediaRecorder.isTypeSupported(t));
      const g = new MediaRecorder(stream, { ...(tipo ? { mimeType: tipo } : {}), audioBitsPerSecond: 32000 });
      trozos.current = [];
      g.ondataavailable = (evento) => {
        if (evento.data.size > 0) trozos.current.push(evento.data);
      };
      g.onstop = () => {
        liberar();
        const audio = new Blob(trozos.current, { type: g.mimeType || "audio/webm" });
        void transcribir(audio);
      };
      grabadora.current = g;
      g.start();
      setSegundos(0);
      setFase("grabando");
      const inicio = Date.now();
      temporizador.current = window.setInterval(() => {
        const transcurridos = Math.floor((Date.now() - inicio) / 1000);
        setSegundos(transcurridos);
        if (transcurridos >= MAX_SECONDS && g.state === "recording") g.stop();
      }, 500);
    } catch (e) {
      liberar();
      setFase("inicio");
      const nombre = (e as DOMException).name;
      setError(
        nombre === "NotAllowedError"
          ? "El navegador no dio permiso al micrófono. Habilítalo en el candado de la barra de direcciones."
          : nombre === "NotFoundError"
            ? "No se encontró ningún micrófono."
            : `No se pudo abrir el micrófono: ${(e as Error).message}`,
      );
    }
  }

  function detener() {
    if (grabadora.current?.state === "recording") grabadora.current.stop();
  }

  if (estado === null || !estado.habilitada) return null;
  if (!estado.disponible) {
    return <p className="muted">La voz no está disponible: el servicio de voz está apagado. El asistente sigue funcionando por texto.</p>;
  }
  if (!soportaMicrofono) {
    return (
      <p className="muted">
        El micrófono necesita una conexión segura: abre el Hub con HTTPS o desde localhost. Mientras tanto, escribe tu pregunta.
      </p>
    );
  }

  return (
    <div className="voice-input" role="group" aria-label="Entrada por voz">
      {fase === "grabando" ? (
        <button type="button" className="button button-primary" onClick={detener}>
          ● Escuchando… {segundos} s · Detener
        </button>
      ) : (
        <button type="button" className="button button-secondary" onClick={() => void empezar()} disabled={disabled || fase === "transcribiendo"}>
          {fase === "transcribiendo" ? "Transcribiendo…" : "Hablar"}
        </button>
      )}
      <label className="muted voice-option">
        <input type="checkbox" checked={enviarSinRevisar} onChange={(evento) => { enviarRef.current = evento.target.checked; setEnviarSinRevisar(evento.target.checked); }} /> Enviar al terminar de hablar, sin revisar
      </label>
      <p className="muted" role="status" aria-live="polite">
        {fase === "grabando" ? `Habla; se detiene sola a los ${MAX_SECONDS} s.` : fase === "transcribiendo" ? "Convirtiendo tu voz en texto…" : ""}
      </p>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
    </div>
  );
}
