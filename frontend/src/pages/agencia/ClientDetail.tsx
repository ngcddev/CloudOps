// Pantalla "Detalle del cliente": datos de contacto, proyectos, servicios con su plan y tabla de SLA.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getClient, type ClientDetail as ClientDetailData, type Service } from "../../api";
import StatusBadge from "../../components/StatusBadge";
import {
  formatMinutes,
  formatPercent,
  formatPrice,
  formatSlaClock,
  formatSupportHours,
  formatTemplate,
} from "../../format";

// Significado de cada prioridad (constitución, "Prioridades y SLA base")
const priorityMeaning: Record<string, string> = {
  P1: "Crítica: el sitio no funciona o se pierden ventas",
  P2: "Alta: una función importante falla",
  P3: "Media: falla menor con alternativa",
  P4: "Baja: consulta o mejora",
};

// Tarjeta de un servicio con los datos de su plan
function ServiceCard({ service }: { service: Service }) {
  const { plan } = service;
  return (
    <section className="card">
      <div className="card-header">
        <h3>{service.name}</h3>
        <StatusBadge status={service.status} />
      </div>
      <dl className="data">
        <dt>Dirección</dt>
        <dd>{service.host}</dd>
        <dt>Plantilla</dt>
        <dd>{formatTemplate(service.template)}</dd>
        <dt>Namespace</dt>
        <dd>
          <code>{service.namespace}</code>
        </dd>
      </dl>

      <h4>
        Plan <span className="plan-name">{plan.name}</span>
      </h4>
      <dl className="data">
        <dt>SLO de disponibilidad mensual</dt>
        <dd>{formatPercent(plan.slo_availability)}</dd>
        <dt>Horario de atención</dt>
        <dd>{formatSupportHours(plan.support_hours)}</dd>
        <dt>Cuota CPU / RAM</dt>
        <dd>
          {plan.cpu_quota} / {plan.memory_quota}
        </dd>
        <dt>Precio mensual</dt>
        <dd>{formatPrice(plan.monthly_price)}</dd>
        <dt>Horas incluidas</dt>
        <dd>{plan.included_hours ?? "Por definir"}</dd>
      </dl>
    </section>
  );
}

export default function ClientDetail() {
  const { id } = useParams();
  const [client, setClient] = useState<ClientDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setClient(null);
    setError(null);
    getClient(Number(id))
      .then(setClient)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  return (
    <>
      <p>
        <Link to="/agencia/clientes">← Volver a clientes</Link>
      </p>

      {error && (
        <p className="error" role="alert">
          ✕ No se pudo cargar el cliente: {error}
        </p>
      )}
      {!client && !error && <p>Cargando cliente…</p>}

      {client && (
        <>
          <h1>{client.name}</h1>

          <section>
            <h2>Contacto</h2>
            <dl className="data">
              <dt>Persona de contacto</dt>
              <dd>{client.contact_name || "—"}</dd>
              <dt>Correo</dt>
              <dd>{client.email ? <a href={`mailto:${client.email}`}>{client.email}</a> : "—"}</dd>
              <dt>Teléfono</dt>
              <dd>{client.phone || "—"}</dd>
            </dl>
          </section>

          <section>
            <h2>Proyectos y servicios</h2>
            {client.projects.length === 0 && <p>Este cliente todavía no tiene proyectos.</p>}
            {client.projects.map((project) => (
              <article key={project.id} className="project">
                <h3>{project.name}</h3>
                {project.description && <p>{project.description}</p>}
                {project.services.length === 0 && <p>Este proyecto todavía no tiene servicios.</p>}
                {project.services.map((service) => (
                  <ServiceCard key={service.id} service={service} />
                ))}
              </article>
            ))}
          </section>

          <section>
            <h2>SLA por prioridad</h2>
            <p className="muted">
              Tiempos máximos desde que se abre el caso. P2–P4 corren solo en el horario de atención del plan.
            </p>
            <table className="table">
              <thead>
                <tr>
                  <th>Prioridad</th>
                  <th>Significado</th>
                  <th>Respuesta</th>
                  <th>Solución</th>
                  <th>Reloj</th>
                </tr>
              </thead>
              <tbody>
                {client.sla_policies.map((sla) => (
                  <tr key={sla.id}>
                    <td>
                      <strong>{sla.priority}</strong>
                    </td>
                    <td>{priorityMeaning[sla.priority] ?? "—"}</td>
                    <td>{formatMinutes(sla.response_minutes)}</td>
                    <td>{formatMinutes(sla.resolution_minutes)}</td>
                    <td>{formatSlaClock(sla.clock)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </>
  );
}
