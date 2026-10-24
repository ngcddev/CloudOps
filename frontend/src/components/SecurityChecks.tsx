// Controles de la puerta de seguridad de una versión: ✓ / ✕ / … por control, resumen y descarga del reporte (spec 006).
import { useState } from "react";

import { downloadCheckReport, type Gate, type GateStatus, type SecurityCheck, type SecurityStep } from "../api";

// Nombre de cada control para la agencia (el cliente nunca ve esta pantalla)
export const STEP_LABELS: Record<SecurityStep | "pipeline", string> = {
  secretos: "Secretos en el código",
  construccion: "Construcción de la imagen",
  vulnerabilidades: "Vulnerabilidades críticas",
  sbom: "Inventario de componentes (SBOM)",
  firma: "Firma de la imagen",
  verificacion: "Verificación de la firma",
  pipeline: "Ejecución del pipeline",
};

// Orden en que corren los controles; sirve para mostrar también los que aún no han llegado
const STEP_ORDER: SecurityStep[] = ["secretos", "construccion", "vulnerabilidades", "sbom", "firma", "verificacion"];

// El estado se comunica con texto e ícono, nunca con color
export const GATE_TEXT: Record<GateStatus, { icon: string; text: string }> = {
  sin_corrida: { icon: "—", text: "Sin revisar" },
  en_curso: { icon: "…", text: "Revisando" },
  ok: { icon: "✓", text: "Controles aprobados" },
  fallo: { icon: "✕", text: "No pasó los controles" },
};

export function gateSummary(status: GateStatus, failedStep: string | null): string {
  const base = `${GATE_TEXT[status].icon} ${GATE_TEXT[status].text}`;
  if (status !== "fallo" || !failedStep) return base;
  return `${base}: ${(STEP_LABELS[failedStep as SecurityStep | "pipeline"] ?? failedStep).toLowerCase()}`;
}

function checkFor(checks: SecurityCheck[], step: SecurityStep): SecurityCheck[] {
  return checks.filter((check) => check.step === step);
}

export default function SecurityChecks({ gate }: { gate: Gate }) {
  const [error, setError] = useState<string | null>(null);
  const checks = gate.run?.checks ?? [];

  async function handleReport(check: SecurityCheck) {
    try {
      setError(null);
      await downloadCheckReport(check.id);
    } catch (reportError) {
      setError((reportError as Error).message);
    }
  }

  return (
    <details className="security-checks">
      <summary>{gateSummary(gate.status, gate.failed_step)}</summary>
      {gate.status === "sin_corrida" && (
        <p className="muted">La versión {gate.version} aún no pasó por la puerta: súbela al repositorio del sitio.</p>
      )}
      {gate.run && (
        <ul className="plain-list">
          {STEP_ORDER.map((step) => {
            const done = checkFor(checks, step);
            if (done.length === 0) {
              return (
                <li key={step}>
                  <span aria-hidden="true">{gate.status === "en_curso" ? "…" : "—"}</span> {STEP_LABELS[step]}
                  <span className="muted"> · {gate.status === "en_curso" ? "pendiente" : "no corrió"}</span>
                </li>
              );
            }
            return done.map((check) => (
              <li key={check.id}>
                <span aria-hidden="true">{check.status === "ok" ? "✓" : "✕"}</span> {STEP_LABELS[step]}
                {check.image && <span className="muted"> ({check.image})</span>}
                {check.summary && <div className="muted">{check.summary}</div>}
                {check.has_report && (
                  <button type="button" className="link-button" onClick={() => void handleReport(check)}>
                    Ver reporte
                  </button>
                )}
              </li>
            ));
          })}
        </ul>
      )}
      {error && (
        <p className="error" role="alert">
          ✕ {error}
        </p>
      )}
    </details>
  );
}
