// Cliente de la API del Hub: todas las llamadas del frontend pasan por aquí.
// Contrato: plan 001 (specs/001-clientes-y-planes/plan.md#api).
// Si la API aún no responde (T04–T07 pendientes o contenedor caído), se usan datos de prueba
// construidos desde seed/ y la interfaz lo avisa. Al conectar la API real no cambia nada más.
import seedClients from "@seed/clients.json";
import seedPlans from "@seed/plans.json";
import seedSlaPolicies from "@seed/sla_policies.json";

// ---------- Tipos (mismos nombres de campo que la API, en snake_case) ----------

export type ServiceStatus = "operativo" | "degradado" | "caido";
export type Template = "landing" | "landing_form";

export interface Plan {
  id: number;
  code: string;
  name: string;
  slo_availability: number;
  support_hours: string;
  cpu_quota: string;
  memory_quota: string;
  monthly_price: number | null;
  included_hours: number | null;
}

export interface SlaPolicy {
  id: number;
  priority: string;
  response_minutes: number;
  resolution_minutes: number;
  clock: string;
}

export interface Service {
  id: number;
  name: string;
  host: string;
  template: Template;
  namespace: string;
  status: ServiceStatus;
  plan: Plan;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  services: Service[];
}

export interface Client {
  id: number;
  name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
}

// Fila de la lista: el cliente con su servicio principal y el plan de ese servicio
export interface ClientSummary extends Client {
  main_service: { id: number; name: string; host: string; status: ServiceStatus; plan: Plan } | null;
}

// Detalle: el cliente con sus proyectos, servicios, plan y los tiempos de SLA
export interface ClientDetail extends Client {
  projects: Project[];
  sla_policies: SlaPolicy[];
}

export type TicketStatus = "abierto" | "en_progreso" | "en_espera" | "resuelto" | "cerrado";
export type TicketPriority = "P1" | "P2" | "P3" | "P4";
export type TicketImpact = "alto" | "medio" | "bajo";
export type TicketUrgency = "alta" | "media" | "baja";
export type TicketKind = "solicitud" | "cambio";

export interface Ticket {
  id: number;
  service_id: number;
  created_by_id: number | null;
  assignee_id: number | null;
  title: string;
  description: string;
  impact: TicketImpact | null;
  urgency: TicketUrgency | null;
  priority: TicketPriority | null;
  status: TicketStatus;
  kind: TicketKind;
  response_due_at: string | null;
  resolution_due_at: string | null;
  first_response_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string;
}

export interface TicketEvent {
  id: number;
  actor_id: number | null;
  type: string;
  from_value: string | null;
  to_value: string | null;
  note: string | null;
  internal: boolean;
  created_at: string;
}

export interface WorkLog {
  id: number;
  user_id: number;
  hours: number;
  note: string | null;
  created_at: string;
}

export interface TicketDetail extends Ticket {
  events: TicketEvent[];
  work_logs: WorkLog[];
}

export interface ClientInput {
  name: string;
  contact_name: string;
  email: string;
  phone: string;
}

export interface TicketInput {
  service_id: number;
  created_by_id?: number | null;
  title: string;
  description: string;
  kind?: TicketKind;
}

export interface TicketClassifyInput {
  impact: TicketImpact;
  urgency: TicketUrgency;
  priority?: TicketPriority;
  correction_reason?: string | null;
}

export interface TicketAssignInput {
  assignee_id: number;
  actor_id?: number | null;
}

export interface TicketTransitionInput {
  new_status: Exclude<TicketStatus, "abierto">;
  actor_id?: number | null;
}

export interface WorkLogInput {
  user_id: number;
  hours: number;
  note?: string | null;
}

export interface ProjectInput {
  name: string;
  description: string;
}

export interface ServiceInput {
  name: string;
  host: string;
  template: Template;
  namespace: string;
  plan_id: number | null;
}

// Error con mensaje listo para mostrar en pantalla (en español)
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

// ---------- Modo de trabajo: API real o datos de prueba ----------

let modePromise: Promise<"api" | "mock"> | null = null;

// Se decide una sola vez: si /api/plans no contesta con JSON, se trabaja con datos de prueba
function detectMode(): Promise<"api" | "mock"> {
  modePromise ??= fetch("/api/plans", { headers: { Accept: "application/json" } })
    .then((res) =>
      res.ok && res.headers.get("content-type")?.includes("application/json") ? "api" : "mock",
    )
    .catch(() => "mock" as const);
  return modePromise;
}

// true cuando la interfaz muestra datos de prueba en lugar de la API
export async function isUsingMockData(): Promise<boolean> {
  return (await detectMode()) === "mock";
}

// ---------- Llamadas a la API real ----------

// Convierte la respuesta de error de FastAPI en un mensaje legible
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(". ");
    }
  } catch {
    // La respuesta no era JSON; se usa el mensaje genérico
  }
  if (res.status === 404) return "No se encontró el recurso solicitado.";
  return `La API respondió con un error (${res.status}).`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
  return res.json() as Promise<T>;
}

// ---------- Datos de prueba en memoria (se pierden al recargar la página) ----------

const mock = (() => {
  const plans: Plan[] = seedPlans.map((p, i) => ({ id: i + 1, ...p }));
  const slaPolicies: SlaPolicy[] = seedSlaPolicies.map((s, i) => ({ id: i + 1, ...s }));
  const clients: ClientDetail[] = [];
  let nextId = 1;

  for (const c of seedClients.clients) {
    clients.push({
      id: nextId++,
      name: c.name,
      contact_name: c.contact_name,
      email: c.email,
      phone: c.phone,
      sla_policies: slaPolicies,
      projects: c.projects.map((p) => ({
        id: nextId++,
        name: p.name,
        description: p.description,
        services: p.services.map((s) => ({
          id: nextId++,
          name: s.name,
          host: s.host,
          template: s.template as Template,
          namespace: s.namespace,
          status: "operativo" as ServiceStatus,
          plan: plans.find((pl) => pl.code === s.plan_code)!,
        })),
      })),
    });
  }

  const baseDate = new Date("2026-10-05T14:00:00Z").toISOString();
  const firstServiceId = clients[0]?.projects[0]?.services[0]?.id ?? 1;
  const tickets: TicketDetail[] = [
    {
      id: 1001,
      service_id: firstServiceId,
      created_by_id: 1,
      assignee_id: 2,
      title: "El menú del domingo no aparece",
      description: "La web de La Sazón no carga el menú del domingo desde la última actualización.",
      impact: "alto",
      urgency: "media",
      priority: "P2",
      status: "en_progreso",
      kind: "solicitud",
      response_due_at: new Date("2026-10-05T15:00:00Z").toISOString(),
      resolution_due_at: new Date("2026-10-05T22:00:00Z").toISOString(),
      first_response_at: new Date("2026-10-05T14:10:00Z").toISOString(),
      resolved_at: null,
      closed_at: null,
      created_at: baseDate,
      events: [
        {
          id: 1,
          actor_id: 1,
          type: "estado",
          from_value: "abierto",
          to_value: "en_progreso",
          note: null,
          internal: false,
          created_at: new Date("2026-10-05T14:10:00Z").toISOString(),
        },
      ],
      work_logs: [
        {
          id: 1,
          user_id: 2,
          hours: 1.5,
          note: "Revisión del menú y ajuste de render",
          created_at: new Date("2026-10-05T14:30:00Z").toISOString(),
        },
      ],
    },
    {
      id: 1002,
      service_id: firstServiceId,
      created_by_id: 1,
      assignee_id: null,
      title: "No llegan los mensajes del formulario",
      description: "El formulario del consultorio no envía la solicitud de cita.",
      impact: "medio",
      urgency: "alta",
      priority: "P2",
      status: "abierto",
      kind: "solicitud",
      response_due_at: new Date("2026-10-05T15:00:00Z").toISOString(),
      resolution_due_at: new Date("2026-10-05T22:00:00Z").toISOString(),
      first_response_at: null,
      resolved_at: null,
      closed_at: null,
      created_at: baseDate,
      events: [],
      work_logs: [],
    },
    {
      id: 1003,
      service_id: clients[0]?.projects[0]?.services[1]?.id ?? firstServiceId,
      created_by_id: 1,
      assignee_id: 3,
      title: "Cambio de banner del sitio",
      description: "Solicitan cambiar la imagen principal del home del cliente.",
      impact: "bajo",
      urgency: "baja",
      priority: "P4",
      status: "cerrado",
      kind: "cambio",
      response_due_at: new Date("2026-10-05T18:00:00Z").toISOString(),
      resolution_due_at: new Date("2026-10-06T06:00:00Z").toISOString(),
      first_response_at: new Date("2026-10-05T16:00:00Z").toISOString(),
      resolved_at: new Date("2026-10-05T17:00:00Z").toISOString(),
      closed_at: new Date("2026-10-05T17:15:00Z").toISOString(),
      created_at: baseDate,
      events: [
        {
          id: 2,
          actor_id: 3,
          type: "estado",
          from_value: "resuelto",
          to_value: "cerrado",
          note: null,
          internal: false,
          created_at: new Date("2026-10-05T17:15:00Z").toISOString(),
        },
      ],
      work_logs: [
        {
          id: 2,
          user_id: 3,
          hours: 1,
          note: "Ajuste visual y validación del publicador",
          created_at: new Date("2026-10-05T16:30:00Z").toISOString(),
        },
      ],
    },
  ];

  return { plans, slaPolicies, clients, tickets, newId: () => nextId++ };
})();

function findMockClient(id: number): ClientDetail {
  const client = mock.clients.find((c) => c.id === id);
  if (!client) throw new ApiError("El cliente no existe.", 404);
  return client;
}

function findMockTicket(id: number): TicketDetail {
  const ticket = mock.tickets.find((item) => item.id === id);
  if (!ticket) throw new ApiError("La solicitud no existe.", 404);
  return ticket;
}

function summarize(client: ClientDetail): ClientSummary {
  const { projects, sla_policies: _sla, ...data } = client;
  const service = projects.flatMap((p) => p.services)[0];
  return {
    ...data,
    main_service: service
      ? { id: service.id, name: service.name, host: service.host, status: service.status, plan: service.plan }
      : null,
  };
}

// Mismas validaciones que la API (CA-5)
function requireText(value: string, message: string) {
  if (!value.trim()) throw new ApiError(message, 422);
}

// ---------- Funciones públicas ----------

export async function listPlans(): Promise<Plan[]> {
  if ((await detectMode()) === "mock") return mock.plans;
  return request<Plan[]>("/plans");
}

export async function listClients(): Promise<ClientSummary[]> {
  if ((await detectMode()) === "mock") return mock.clients.map(summarize);
  return request<ClientSummary[]>("/clients");
}

export async function getClient(id: number): Promise<ClientDetail> {
  if ((await detectMode()) === "mock") return findMockClient(id);
  return request<ClientDetail>(`/clients/${id}`);
}

export async function createClient(input: ClientInput): Promise<Client> {
  if ((await detectMode()) === "mock") {
    requireText(input.name, "El nombre del cliente es obligatorio.");
    const client: ClientDetail = { id: mock.newId(), ...input, projects: [], sla_policies: mock.slaPolicies };
    mock.clients.push(client);
    return client;
  }
  return request<Client>("/clients", { method: "POST", body: JSON.stringify(input) });
}

export async function createProject(clientId: number, input: ProjectInput): Promise<Project> {
  if ((await detectMode()) === "mock") {
    requireText(input.name, "El nombre del proyecto es obligatorio.");
    const project: Project = { id: mock.newId(), ...input, services: [] };
    findMockClient(clientId).projects.push(project);
    return project;
  }
  return request<Project>(`/clients/${clientId}/projects`, { method: "POST", body: JSON.stringify(input) });
}

export async function createService(projectId: number, input: ServiceInput): Promise<Service> {
  if ((await detectMode()) === "mock") {
    requireText(input.name, "El nombre del servicio es obligatorio.");
    const plan = mock.plans.find((p) => p.id === input.plan_id);
    if (!plan) throw new ApiError("El servicio necesita un plan.", 422);
    const project = mock.clients.flatMap((c) => c.projects).find((p) => p.id === projectId);
    if (!project) throw new ApiError("El proyecto no existe.", 404);
    const { plan_id: _planId, ...data } = input;
    const service: Service = { id: mock.newId(), ...data, status: "operativo", plan };
    project.services.push(service);
    return service;
  }
  return request<Service>(`/projects/${projectId}/services`, { method: "POST", body: JSON.stringify(input) });
}

// Registro completo desde el formulario: cliente → proyecto → servicio con plan
export async function listTickets(
  params?: { client_id?: number; status?: TicketStatus; priority?: TicketPriority; viewer_role?: "agencia" | "cliente" },
): Promise<Ticket[]> {
  if ((await detectMode()) === "mock") {
    let tickets = [...mock.tickets];
    if (params?.client_id !== undefined) {
      const clientServiceIds = new Set(
        mock.clients
          .filter((client) => client.id === params.client_id)
          .flatMap((client) => client.projects.flatMap((project) => project.services.map((service) => service.id))),
      );
      tickets = tickets.filter((ticket) => clientServiceIds.has(ticket.service_id));
    }
    if (params?.status) tickets = tickets.filter((ticket) => ticket.status === params.status);
    if (params?.priority) tickets = tickets.filter((ticket) => ticket.priority === params.priority);
    return tickets;
  }

  const queryEntries: [string, string][] = [];
  if (params?.client_id !== undefined) queryEntries.push(["client_id", String(params.client_id)]);
  if (params?.status) queryEntries.push(["status", params.status]);
  if (params?.priority) queryEntries.push(["priority", params.priority]);
  queryEntries.push(["viewer_role", params?.viewer_role ?? "agencia"]);

  const query = new URLSearchParams(queryEntries);
  return request<Ticket[]>(`/tickets${query.size ? `?${query.toString()}` : ""}`);
}

export async function getTicket(
  id: number,
  viewer_role: "agencia" | "cliente" = "agencia",
  client_id?: number,
): Promise<TicketDetail> {
  if ((await detectMode()) === "mock") return findMockTicket(id);
  const query = new URLSearchParams({ viewer_role, ...(client_id !== undefined ? { client_id: client_id.toString() } : {}) });
  return request<TicketDetail>(`/tickets/${id}?${query.toString()}`);
}

export async function createTicket(input: TicketInput): Promise<Ticket> {
  if ((await detectMode()) === "mock") {
    requireText(input.title, "El título de la solicitud es obligatorio.");
    requireText(input.description, "La descripción de la solicitud es obligatoria.");
    const service = mock.clients.flatMap((client) => client.projects.flatMap((project) => project.services)).find((item) => item.id === input.service_id);
    if (!service) throw new ApiError("El servicio indicado no existe.", 404);
    const ticket: TicketDetail = {
      id: mock.newId(),
      service_id: input.service_id,
      created_by_id: input.created_by_id ?? null,
      assignee_id: null,
      title: input.title,
      description: input.description,
      impact: null,
      urgency: null,
      priority: null,
      status: "abierto",
      kind: input.kind ?? "solicitud",
      response_due_at: null,
      resolution_due_at: null,
      first_response_at: null,
      resolved_at: null,
      closed_at: null,
      created_at: new Date().toISOString(),
      events: [],
      work_logs: [],
    };
    mock.tickets.unshift(ticket);
    return ticket;
  }
  return request<Ticket>("/tickets", { method: "POST", body: JSON.stringify(input) });
}

export async function classifyTicket(id: number, input: TicketClassifyInput): Promise<Ticket> {
  if ((await detectMode()) === "mock") {
    const ticket = findMockTicket(id);
    const previousPriority = ticket.priority;
    ticket.impact = input.impact;
    ticket.urgency = input.urgency;
    ticket.priority = input.priority ?? "P2";
    ticket.response_due_at = new Date(Date.parse(ticket.created_at) + 60 * 60 * 1000).toISOString();
    ticket.resolution_due_at = new Date(Date.parse(ticket.created_at) + 8 * 60 * 60 * 1000).toISOString();
    ticket.events.unshift({
      id: Date.now(),
      actor_id: 1,
      type: "prioridad",
      from_value: previousPriority,
      to_value: ticket.priority,
      note: input.correction_reason ?? null,
      internal: false,
      created_at: new Date().toISOString(),
    });
    return ticket;
  }
  return request<Ticket>(`/tickets/${id}/classify`, { method: "POST", body: JSON.stringify(input) });
}

export async function assignTicket(id: number, input: TicketAssignInput): Promise<Ticket> {
  if ((await detectMode()) === "mock") {
    const ticket = findMockTicket(id);
    const previousAssignee = ticket.assignee_id;
    ticket.assignee_id = input.assignee_id;
    ticket.events.unshift({
      id: Date.now(),
      actor_id: input.actor_id ?? 1,
      type: "asignacion",
      from_value: previousAssignee === null ? null : String(previousAssignee),
      to_value: String(input.assignee_id),
      note: null,
      internal: false,
      created_at: new Date().toISOString(),
    });
    return ticket;
  }
  return request<Ticket>(`/tickets/${id}/assign`, { method: "POST", body: JSON.stringify(input) });
}

export async function transitionTicket(id: number, input: TicketTransitionInput): Promise<Ticket> {
  if ((await detectMode()) === "mock") {
    const ticket = findMockTicket(id);
    const previousStatus = ticket.status;
    ticket.status = input.new_status;
    if (input.new_status === "en_progreso" && !ticket.first_response_at) {
      ticket.first_response_at = new Date().toISOString();
    }
    if (input.new_status === "resuelto") ticket.resolved_at = new Date().toISOString();
    if (input.new_status === "cerrado") ticket.closed_at = new Date().toISOString();
    ticket.events.unshift({
      id: Date.now(),
      actor_id: input.actor_id ?? 1,
      type: "estado",
      from_value: previousStatus,
      to_value: input.new_status,
      note: null,
      internal: false,
      created_at: new Date().toISOString(),
    });
    return ticket;
  }
  return request<Ticket>(`/tickets/${id}/transition`, { method: "POST", body: JSON.stringify(input) });
}

export async function createWorkLog(id: number, input: WorkLogInput): Promise<WorkLog> {
  if ((await detectMode()) === "mock") {
    const ticket = findMockTicket(id);
    const workLog: WorkLog = {
      id: Date.now(),
      user_id: input.user_id,
      hours: input.hours,
      note: input.note ?? null,
      created_at: new Date().toISOString(),
    };
    ticket.work_logs.unshift(workLog);
    return workLog;
  }
  return request<WorkLog>(`/tickets/${id}/work-logs`, { method: "POST", body: JSON.stringify(input) });
}

export async function registerClient(
  client: ClientInput,
  project: ProjectInput,
  service: ServiceInput,
): Promise<Client> {
  const created = await createClient(client);
  const createdProject = await createProject(created.id, project);
  await createService(createdProject.id, service);
  return created;
}
