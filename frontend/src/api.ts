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
}

export interface TicketTransitionInput {
  new_status: Exclude<TicketStatus, "abierto">;
}

export interface WorkLogInput {
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

// Se decide una sola vez: si /api/plans no contesta con JSON, se trabaja con datos de prueba.
// Sin sesión la API responde 401 con JSON (spec 007): también cuenta como API real.
function detectMode(): Promise<"api" | "mock"> {
  modePromise ??= fetch("/api/plans", { headers: { Accept: "application/json" } })
    .then((res) =>
      (res.ok || res.status === 401) && res.headers.get("content-type")?.includes("application/json")
        ? "api"
        : "mock",
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

// ---------- Sesión (spec 007) ----------

export interface SessionUser {
  id: number;
  name: string;
  email: string;
  role: "agencia" | "cliente";
  client_id: number | null;
}

let authToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

// El contexto de sesión (auth.tsx) entrega aquí el token y qué hacer cuando la API responde 401
export function setAuthToken(token: string | null) {
  authToken = token;
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "application/json" };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  const res = await fetch(`/api${path}`, { ...init, headers });
  if (res.status === 401 && authToken && path !== "/auth/login") onUnauthorized?.();
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
  return res.json() as Promise<T>;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  user: SessionUser;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  return request<LoginResult>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export async function getMe(): Promise<SessionUser> {
  return request<SessionUser>("/auth/me");
}

// Con datos de prueba no hay API que firme nada: las acciones salen a nombre de la técnica de ejemplo
const MOCK_USER_ID = 1;
const MOCK_USER_NAME = "Sofía Ramírez";

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
  params?: { client_id?: number; status?: TicketStatus; priority?: TicketPriority },
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

  const query = new URLSearchParams(queryEntries);
  return request<Ticket[]>(`/tickets${query.size ? `?${query.toString()}` : ""}`);
}

export async function getTicket(id: number): Promise<TicketDetail> {
  if ((await detectMode()) === "mock") return findMockTicket(id);
  return request<TicketDetail>(`/tickets/${id}`);
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
      created_by_id: MOCK_USER_ID,
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
      actor_id: MOCK_USER_ID,
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
      actor_id: MOCK_USER_ID,
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
      actor_id: MOCK_USER_ID,
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
      user_id: MOCK_USER_ID,
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

// ---------- Cambios por GitOps (spec 005) ----------

export type ChangeStatus = "pendiente" | "aprobada" | "en_validacion" | "desplegada" | "rechazada" | "fallida";

export interface ChangeRequest {
  id: number;
  ticket_id: number;
  ticket_title: string | null;
  service_id: number;
  from_version: string;
  to_version: string;
  status: ChangeStatus;
  requested_by_id: number | null;
  requested_by_name: string | null;
  approved_by_id: number | null;
  approved_by_name: string | null;
  gitops_commit_sha: string | null;
  rejection_reason: string | null;
  created_at: string;
  approved_at: string | null;
  deployed_at: string | null;
}

export interface ChangeRequestInput {
  ticket_id: number;
  to_version: string;
}

// Una fila de la consola de servicios: versión activa, sincronización y salud que informa Argo CD
export interface ServiceVersionStatus {
  service_id: number;
  client_id: number;
  client_name: string;
  service_name: string;
  host: string;
  namespace: string;
  current_version: string;
  stable_version: string;
  sync_status: string;
  health_status: string;
  last_author: string | null;
  last_change_at: string | null;
  open_change_id: number | null;
  open_change_status: ChangeStatus | null;
  open_change_to_version: string | null;
  // Puerta de seguridad de la versión activa (spec 006)
  security_status: GateStatus;
  security_failed_step: SecurityStep | "pipeline" | null;
  // Monitoreo (spec 008): caido mientras tenga un incidente de alerta abierto
  service_status: ServiceStatus;
}

export interface Deployment {
  id: number;
  service_id: number;
  version: string;
  commit_sha: string | null;
  author: string;
  source: "cambio" | "rollback";
  created_at: string;
}

const OPEN_CHANGE_STATUSES: ChangeStatus[] = ["pendiente", "aprobada", "en_validacion"];

// Estado de los cambios y las versiones en datos de prueba (la API real no usa nada de esto)
const changeMock = {
  changes: [] as ChangeRequest[],
  versions: new Map<number, { current: string; author: string | null; at: string | null }>(),
  nextId: 1,
};

function mockServices() {
  return mock.clients.flatMap((client) =>
    client.projects.flatMap((project) => project.services.map((service) => ({ client, service }))),
  );
}

function mockVersion(serviceId: number) {
  let entry = changeMock.versions.get(serviceId);
  if (!entry) {
    entry = { current: "v1", author: null, at: null };
    changeMock.versions.set(serviceId, entry);
  }
  return entry;
}

function findMockChange(id: number): ChangeRequest {
  const change = changeMock.changes.find((item) => item.id === id);
  if (!change) throw new ApiError("La solicitud de cambio no existe.", 404);
  return change;
}

export async function listChangeRequests(params?: { ticket_id?: number }): Promise<ChangeRequest[]> {
  if ((await detectMode()) === "mock") {
    const changes = changeMock.changes.filter((c) => params?.ticket_id === undefined || c.ticket_id === params.ticket_id);
    return changes.sort((a, b) => b.id - a.id);
  }
  const query = params?.ticket_id !== undefined ? `?ticket_id=${params.ticket_id}` : "";
  return request<ChangeRequest[]>(`/change-requests${query}`);
}

export async function createChangeRequest(input: ChangeRequestInput): Promise<ChangeRequest> {
  if ((await detectMode()) === "mock") {
    const ticket = findMockTicket(input.ticket_id);
    if (ticket.kind !== "cambio") throw new ApiError("La solicitud debe ser de tipo cambio.", 422);
    requireText(input.to_version, "La versión destino es obligatoria.");
    const version = mockVersion(ticket.service_id);
    if (input.to_version.trim() === version.current) {
      throw new ApiError(`El sitio ya está en la versión ${version.current}.`, 422);
    }
    if (changeMock.changes.some((c) => c.service_id === ticket.service_id && OPEN_CHANGE_STATUSES.includes(c.status))) {
      throw new ApiError("Ya hay un cambio en curso para este sitio.", 409);
    }
    const change: ChangeRequest = {
      id: changeMock.nextId++,
      ticket_id: ticket.id,
      ticket_title: ticket.title,
      service_id: ticket.service_id,
      from_version: version.current,
      to_version: input.to_version.trim(),
      status: "pendiente",
      requested_by_id: MOCK_USER_ID,
      requested_by_name: MOCK_USER_NAME,
      approved_by_id: null,
      approved_by_name: null,
      gitops_commit_sha: null,
      rejection_reason: null,
      created_at: new Date().toISOString(),
      approved_at: null,
      deployed_at: null,
    };
    changeMock.changes.push(change);
    return change;
  }
  return request<ChangeRequest>("/change-requests", { method: "POST", body: JSON.stringify(input) });
}

export async function approveChangeRequest(id: number): Promise<ChangeRequest> {
  if ((await detectMode()) === "mock") {
    const change = findMockChange(id);
    if (change.status !== "pendiente") {
      throw new ApiError(`No se permite pasar de «${change.status}» a «aprobada».`, 409);
    }
    change.status = "en_validacion";
    change.approved_by_id = MOCK_USER_ID;
    change.approved_by_name = MOCK_USER_NAME;
    change.approved_at = new Date().toISOString();
    change.gitops_commit_sha = Math.random().toString(16).slice(2).padEnd(40, "0").slice(0, 40);
    // Argo CD tarda unos segundos en sincronizar: se simula para que la bandeja muestre el paso
    setTimeout(() => {
      change.status = "desplegada";
      change.deployed_at = new Date().toISOString();
      const version = mockVersion(change.service_id);
      version.current = change.to_version;
      version.author = MOCK_USER_NAME;
      version.at = change.deployed_at;
    }, 4000);
    return change;
  }
  return request<ChangeRequest>(`/change-requests/${id}/approve`, { method: "POST" });
}

export async function rejectChangeRequest(id: number, reason: string): Promise<ChangeRequest> {
  if ((await detectMode()) === "mock") {
    const change = findMockChange(id);
    requireText(reason, "Debe indicar el motivo del rechazo.");
    if (change.status !== "pendiente") {
      throw new ApiError(`No se permite pasar de «${change.status}» a «rechazada».`, 409);
    }
    change.status = "rechazada";
    change.rejection_reason = reason.trim();
    return change;
  }
  return request<ChangeRequest>(`/change-requests/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// En datos de prueba, igual que la API: caído si tiene un incidente de alerta abierto (spec 008)
function mockServiceStatus(serviceId: number): ServiceStatus {
  ensureMockIncidents();
  return incidentMock.incidents.some((i) => i.service_id === serviceId && i.source === "alerta" && i.status === "abierto")
    ? "caido"
    : "operativo";
}

export async function listServicesStatus(): Promise<ServiceVersionStatus[]> {
  if ((await detectMode()) === "mock") {
    return mockServices().map(({ client, service }) => {
      const version = mockVersion(service.id);
      const open = changeMock.changes.find(
        (c) => c.service_id === service.id && OPEN_CHANGE_STATUSES.includes(c.status),
      );
      return {
        service_id: service.id,
        client_id: client.id,
        client_name: client.name,
        service_name: service.name,
        host: service.host,
        namespace: service.namespace,
        current_version: version.current,
        stable_version: version.current,
        sync_status: open?.status === "en_validacion" ? "OutOfSync" : "Synced",
        health_status: "Healthy",
        last_author: version.author,
        last_change_at: version.at,
        open_change_id: open?.id ?? null,
        open_change_status: open?.status ?? null,
        open_change_to_version: open?.to_version ?? null,
        security_status: "ok" as GateStatus,
        security_failed_step: null,
        service_status: mockServiceStatus(service.id),
      };
    });
  }
  return request<ServiceVersionStatus[]>("/services/status");
}

export async function listDeployments(serviceId: number): Promise<Deployment[]> {
  if ((await detectMode()) === "mock") {
    return changeMock.changes
      .filter((c) => c.service_id === serviceId && c.status === "desplegada")
      .map((c) => ({
        id: c.id,
        service_id: serviceId,
        version: c.to_version,
        commit_sha: c.gitops_commit_sha,
        author: c.approved_by_name ?? "Hub",
        source: "cambio" as const,
        created_at: c.deployed_at ?? c.created_at,
      }))
      .reverse();
  }
  return request<Deployment[]>(`/services/${serviceId}/deployments`);
}


// ---------- Bitácora (spec 007) ----------

export interface AuditLog {
  id: number;
  user_id: number | null;
  // "Sistema" cuando la acción la hizo el Hub solo
  user_name: string;
  action: string;
  entity: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  ip: string | null;
  created_at: string;
}

export interface AuditLogFilters {
  user_id?: number;
  entity?: string;
  action?: string;
  from?: string;
  to?: string;
}

export async function listAuditLogs(filters: AuditLogFilters = {}): Promise<AuditLog[]> {
  if ((await detectMode()) === "mock") {
    const now = Date.now();
    const hoursAgo = (hours: number) => new Date(now - hours * 60 * 60 * 1000).toISOString();
    const sample: AuditLog[] = [
      { id: 3, user_id: null, user_name: "Sistema", action: "desplegar", entity: "change_request", entity_id: 1, details: { a: "v1.1", commit: "3fa9c21" }, ip: null, created_at: hoursAgo(1) },
      { id: 2, user_id: MOCK_USER_ID, user_name: MOCK_USER_NAME, action: "aprobar", entity: "change_request", entity_id: 1, details: { a: "v1.1", commit: "3fa9c21" }, ip: "127.0.0.1", created_at: hoursAgo(2) },
      { id: 1, user_id: MOCK_USER_ID, user_name: MOCK_USER_NAME, action: "cambiar_prioridad", entity: "ticket", entity_id: 1001, details: { a: "P2" }, ip: "127.0.0.1", created_at: hoursAgo(3) },
    ];
    return sample.filter(
      (log) =>
        (filters.user_id === undefined || log.user_id === filters.user_id) &&
        (!filters.entity || log.entity === filters.entity) &&
        (!filters.action || log.action === filters.action),
    );
  }
  const query = new URLSearchParams();
  if (filters.user_id !== undefined) query.set("user_id", String(filters.user_id));
  if (filters.entity) query.set("entity", filters.entity);
  if (filters.action) query.set("action", filters.action);
  if (filters.from) query.set("from", filters.from);
  if (filters.to) query.set("to", filters.to);
  return request<AuditLog[]>(`/audit-logs${query.size ? `?${query.toString()}` : ""}`);
}


// ---------- Puerta de seguridad (spec 006) ----------

export type GateStatus = "sin_corrida" | "en_curso" | "ok" | "fallo";
export type SecurityStep = "secretos" | "construccion" | "vulnerabilidades" | "sbom" | "firma" | "verificacion";

export interface SecurityCheck {
  id: number;
  step: SecurityStep;
  // Imagen a la que aplica; null en los controles de toda la versión (secretos)
  image: string | null;
  status: "ok" | "fallo";
  summary: string;
  // true si el control guardó un reporte descargable como evidencia
  has_report: boolean;
  created_at: string;
}

export interface SecurityRun {
  id: number;
  service_id: number;
  version: string;
  commit_sha: string | null;
  images: string[];
  status: GateStatus;
  failed_step: SecurityStep | "pipeline" | null;
  image_digests: Record<string, string> | null;
  started_at: string;
  finished_at: string | null;
  checks: SecurityCheck[];
}

// Estado de la puerta para la versión destino de un cambio, con su última corrida
export interface Gate {
  version: string;
  status: GateStatus;
  failed_step: SecurityRun["failed_step"];
  run: SecurityRun | null;
}

const MOCK_STEPS: SecurityStep[] = ["secretos", "construccion", "vulnerabilidades", "sbom", "firma", "verificacion"];

export async function getChangeGate(changeId: number): Promise<Gate> {
  if ((await detectMode()) === "mock") {
    const change = findMockChange(changeId);
    const startedAt = change.created_at;
    return {
      version: change.to_version,
      status: "ok",
      failed_step: null,
      run: {
        id: changeId,
        service_id: change.service_id,
        version: change.to_version,
        commit_sha: null,
        images: ["ferreteria"],
        status: "ok",
        failed_step: null,
        image_digests: null,
        started_at: startedAt,
        finished_at: startedAt,
        checks: MOCK_STEPS.map((step, index) => ({
          id: changeId * 10 + index,
          step,
          image: step === "secretos" ? null : "ferreteria",
          status: "ok" as const,
          summary: "Datos de prueba",
          has_report: false,
          created_at: startedAt,
        })),
      },
    };
  }
  return request<Gate>(`/change-requests/${changeId}/checks`);
}

// Descarga el reporte de un control (la evidencia). Va por fetch para enviar la sesión en la cabecera.
export async function downloadCheckReport(checkId: number): Promise<void> {
  if ((await detectMode()) === "mock") throw new ApiError("Con datos de prueba no hay reportes guardados.", 404);
  const headers: Record<string, string> = {};
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  const res = await fetch(`/api/security-checks/${checkId}/report`, { headers });
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
  const name = /filename="([^"]+)"/.exec(res.headers.get("content-disposition") ?? "")?.[1] ?? `reporte-${checkId}.json`;
  const url = URL.createObjectURL(await res.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  // Se revoca después: en algunos navegadores revocar de inmediato cancela la descarga
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

// ---------- Incidentes (spec 008) ----------

export type IncidentStatus = "abierto" | "mitigado" | "cerrado";
export type IncidentSource = "alerta" | "manual";
export type IncidentEventType = "detectado" | "tomado" | "nota" | "recuperado" | "cerrado";
// Estado de un reloj del SLA (spec 008, CA-4)
export type ClockState = "a_tiempo" | "en_riesgo" | "vencido" | "cumplido";

export interface Incident {
  id: number;
  service_id: number;
  client_id: number;
  client_name: string;
  service_name: string;
  namespace: string;
  priority: TicketPriority;
  status: IncidentStatus;
  source: IncidentSource;
  title: string;
  started_at: string;
  acknowledged_at: string | null;
  mitigated_at: string | null;
  closed_at: string | null;
  response_due_at: string;
  resolution_due_at: string;
  assignee_id: number | null;
  assignee_name: string | null;
  root_cause: string | null;
  response_state: ClockState;
  resolution_state: ClockState;
  created_at: string;
}

export interface IncidentEvent {
  id: number;
  type: IncidentEventType;
  message: string | null;
  // Nombre del técnico o «Sistema» si lo registró el monitoreo
  actor_name: string;
  created_at: string;
}

// Última publicación del servicio, para revisar si la falla vino de ahí
export interface IncidentLastChange {
  version: string;
  author: string;
  source: "cambio" | "rollback";
  deployed_at: string;
  change_request_id: number | null;
  commit_sha: string | null;
  commit_url: string | null;
}

export interface IncidentDetail extends Incident {
  events: IncidentEvent[];
  logs_url: string | null;
  last_change: IncidentLastChange | null;
}

export interface IncidentInput {
  service_id: number;
  priority: TicketPriority;
  title: string;
}

export interface IncidentFilters {
  status?: IncidentStatus;
  client_id?: number;
  priority?: TicketPriority;
}

// Minutos de respuesta y solución por prioridad. En datos de prueba se cuentan 24/7; la API real usa el
// horario del plan para P2–P4 (spec 004).
const MOCK_SLA_MINUTES: Record<TicketPriority, [number, number]> = {
  P1: [15, 240],
  P2: [60, 480],
  P3: [240, 1440],
  P4: [480, 4320],
};

// Igual que clock_state del backend: en_riesgo desde el 80 % del plazo; con done el reloj está detenido
export function clockState(start: string, due: string, done: string | null, now: number = Date.now()): ClockState {
  const startMs = Date.parse(start);
  const dueMs = Date.parse(due);
  if (done) return Date.parse(done) <= dueMs ? "cumplido" : "vencido";
  if (now >= dueMs) return "vencido";
  return (now - startMs) * 5 >= (dueMs - startMs) * 4 ? "en_riesgo" : "a_tiempo";
}

// Igual que la API: la respuesta se detiene en lo primero que pase entre tomar y mitigar el incidente
export function responseStoppedAt(incident: Pick<Incident, "acknowledged_at" | "mitigated_at">): string | null {
  const stops = [incident.acknowledged_at, incident.mitigated_at].filter((t): t is string => t !== null);
  if (stops.length === 0) return null;
  return stops.reduce((first, t) => (Date.parse(t) < Date.parse(first) ? t : first));
}

// Incidentes de prueba en memoria: uno de alerta de La Sazón que empezó hace 3 minutos
const incidentMock = (() => {
  const incidents: IncidentDetail[] = [];
  let nextId = 1;
  return {
    incidents,
    newId: () => nextId++,
  };
})();

function addMockMinutes(iso: string, minutes: number): string {
  return new Date(Date.parse(iso) + minutes * 60_000).toISOString();
}

function newMockIncident(serviceId: number, priority: TicketPriority, title: string, source: IncidentSource, startedAt: string): IncidentDetail {
  const found = mockServices().find(({ service }) => service.id === serviceId);
  if (!found) throw new ApiError("El servicio no existe.", 404);
  const [response, resolution] = MOCK_SLA_MINUTES[priority];
  const incident: IncidentDetail = {
    id: incidentMock.newId(),
    service_id: serviceId,
    client_id: found.client.id,
    client_name: found.client.name,
    service_name: found.service.name,
    namespace: found.service.namespace,
    priority,
    status: "abierto",
    source,
    title,
    started_at: startedAt,
    acknowledged_at: null,
    mitigated_at: null,
    closed_at: null,
    response_due_at: addMockMinutes(startedAt, response),
    resolution_due_at: addMockMinutes(startedAt, resolution),
    assignee_id: null,
    assignee_name: null,
    root_cause: null,
    response_state: "a_tiempo",
    resolution_state: "a_tiempo",
    created_at: startedAt,
    events: [],
    logs_url: null,
    last_change: null,
  };
  incident.events.push({
    id: incidentMock.newId(),
    type: "detectado",
    message: source === "alerta" ? "El monitoreo detectó que el sitio no responde." : `Abierto a mano por ${MOCK_USER_NAME}.`,
    actor_name: source === "alerta" ? "Sistema" : MOCK_USER_NAME,
    created_at: startedAt,
  });
  incidentMock.incidents.unshift(incident);
  return incident;
}

function ensureMockIncidents() {
  if (incidentMock.incidents.length > 0) return;
  const restaurante = mockServices().find(({ service }) => service.namespace === "cliente-restaurante");
  if (restaurante) {
    newMockIncident(restaurante.service.id, "P1", "El sitio de restaurante no responde", "alerta", addMockMinutes(new Date().toISOString(), -3));
  }
}

// Devuelve una copia con los relojes calculados a la hora actual, como lo hace la API
function withClocks(incident: IncidentDetail): IncidentDetail {
  return {
    ...incident,
    events: [...incident.events],
    response_state: clockState(incident.started_at, incident.response_due_at, responseStoppedAt(incident)),
    resolution_state: clockState(incident.started_at, incident.resolution_due_at, incident.mitigated_at),
  };
}

function findMockIncident(id: number): IncidentDetail {
  ensureMockIncidents();
  const incident = incidentMock.incidents.find((item) => item.id === id);
  if (!incident) throw new ApiError("El incidente no existe.", 404);
  return incident;
}

function addMockIncidentEvent(incident: IncidentDetail, type: IncidentEventType, message: string) {
  incident.events.push({ id: incidentMock.newId(), type, message, actor_name: MOCK_USER_NAME, created_at: new Date().toISOString() });
}

export async function listIncidents(filters: IncidentFilters = {}): Promise<Incident[]> {
  if ((await detectMode()) === "mock") {
    ensureMockIncidents();
    return incidentMock.incidents
      .filter((i) => !filters.status || i.status === filters.status)
      .filter((i) => !filters.client_id || i.client_id === filters.client_id)
      .filter((i) => !filters.priority || i.priority === filters.priority)
      .map(withClocks);
  }
  const query = new URLSearchParams();
  if (filters.status) query.set("status", filters.status);
  if (filters.client_id) query.set("client_id", String(filters.client_id));
  if (filters.priority) query.set("priority", filters.priority);
  return request<Incident[]>(`/incidents${query.size ? `?${query.toString()}` : ""}`);
}

export async function getIncident(id: number): Promise<IncidentDetail> {
  if ((await detectMode()) === "mock") return withClocks(findMockIncident(id));
  return request<IncidentDetail>(`/incidents/${id}`);
}

export async function createIncident(input: IncidentInput): Promise<Incident> {
  if ((await detectMode()) === "mock") {
    ensureMockIncidents();
    requireText(input.title, "El título es obligatorio.");
    return withClocks(newMockIncident(input.service_id, input.priority, input.title.trim(), "manual", new Date().toISOString()));
  }
  return request<Incident>("/incidents", { method: "POST", body: JSON.stringify(input) });
}

export async function acknowledgeIncident(id: number): Promise<IncidentDetail> {
  if ((await detectMode()) === "mock") {
    const incident = findMockIncident(id);
    if (incident.acknowledged_at) throw new ApiError("El incidente ya fue tomado.", 409);
    if (incident.status === "cerrado") throw new ApiError("El incidente ya está cerrado.", 409);
    incident.acknowledged_at = new Date().toISOString();
    incident.assignee_id = MOCK_USER_ID;
    incident.assignee_name = MOCK_USER_NAME;
    addMockIncidentEvent(incident, "tomado", `Tomado por ${MOCK_USER_NAME}.`);
    return withClocks(incident);
  }
  return request<IncidentDetail>(`/incidents/${id}/acknowledge`, { method: "POST" });
}

export async function addIncidentNote(id: number, message: string): Promise<IncidentDetail> {
  if ((await detectMode()) === "mock") {
    const incident = findMockIncident(id);
    requireText(message, "La nota no puede estar vacía.");
    if (incident.status === "cerrado") throw new ApiError("El incidente ya está cerrado.", 409);
    addMockIncidentEvent(incident, "nota", message.trim());
    return withClocks(incident);
  }
  return request<IncidentDetail>(`/incidents/${id}/notes`, { method: "POST", body: JSON.stringify({ message }) });
}

export async function mitigateIncident(id: number): Promise<IncidentDetail> {
  if ((await detectMode()) === "mock") {
    const incident = findMockIncident(id);
    if (incident.source !== "manual") {
      throw new ApiError("Un incidente de alerta se mitiga solo cuando el monitoreo ve el sitio sano.", 409);
    }
    if (incident.status !== "abierto") throw new ApiError(`No se permite pasar de «${incident.status}» a «mitigado».`, 409);
    incident.status = "mitigado";
    incident.mitigated_at = new Date().toISOString();
    addMockIncidentEvent(incident, "recuperado", `Mitigado a mano por ${MOCK_USER_NAME}.`);
    return withClocks(incident);
  }
  return request<IncidentDetail>(`/incidents/${id}/mitigate`, { method: "POST" });
}

export async function closeIncident(id: number, rootCause: string): Promise<IncidentDetail> {
  if ((await detectMode()) === "mock") {
    const incident = findMockIncident(id);
    requireText(rootCause, "Para cerrar el incidente hay que escribir la causa raíz.");
    if (incident.status !== "mitigado") throw new ApiError(`No se permite pasar de «${incident.status}» a «cerrado».`, 409);
    incident.status = "cerrado";
    incident.root_cause = rootCause.trim();
    incident.closed_at = new Date().toISOString();
    addMockIncidentEvent(incident, "cerrado", `Cerrado por ${MOCK_USER_NAME}. Causa raíz: ${incident.root_cause}`);
    return withClocks(incident);
  }
  return request<IncidentDetail>(`/incidents/${id}/close`, { method: "POST", body: JSON.stringify({ root_cause: rootCause }) });
}

// ---------- Dashboards y metricas (spec 010) ----------

export interface ClientKpi {
  client_id: number;
  client_name: string;
  service_name: string | null;
  service_status: ServiceStatus;
  // null = sin datos (Prometheus caido o sin serie); nunca se inventa un 100 %
  availability: number | null;
  cumple_objetivo: boolean | null;
  latency_p95: number | null;
  sla_compliance: number | null;
  mttr: number | null;
  open_tickets: number;
  closed_tickets: number;
  hours: number;
  cost: number;
}

// El portal no recibe costo, horas ni nombres de tecnicos (CA-7)
export interface ClientDashboardKpi {
  client_id: number;
  client_name: string;
  service_name: string | null;
  service_status: ServiceStatus;
  availability: number | null;
  cumple_objetivo: boolean | null;
  slo_availability: number | null;
  latency_p95: number | null;
  sla_compliance: number | null;
  mttr: number | null;
  open_tickets: number;
  closed_tickets: number;
}

// Falla del mes en el portal: sin tecnicos, SLA ni causa interna (CA-4, CA-7)
export interface ClientIncident {
  id: number;
  title: string;
  status: IncidentStatus;
  started_at: string;
}

export interface TechnicianLoad {
  user_id: number;
  name: string;
  hours: number;
  load: number;
}

export interface AgencyDashboard {
  month: string;
  clients: ClientKpi[];
  technicians: TechnicianLoad[];
}

export interface SeriesPoint {
  timestamp: string;
  value: number;
}

export interface ClientSeries {
  client_id: number;
  month: string;
  slo_availability: number | null;
  availability: SeriesPoint[];
  latency_p95: SeriesPoint[];
}

// Mes actual en America/Bogota, con el formato YYYY-MM que recibe la API
function mesActual(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
  })
    .format(new Date())
    .slice(0, 7);
}

function mockMainService(clientId: number) {
  const client = findMockClient(clientId);
  return client.projects.flatMap((project) => project.services)[0] ?? null;
}

// Horas registradas en el mes de prueba (los datos de prueba viven en octubre de 2026)
function mockClientHours(clientId: number): number {
  const client = findMockClient(clientId);
  const serviceIds = new Set(client.projects.flatMap((project) => project.services.map((service) => service.id)));
  return mock.tickets
    .filter((ticket) => serviceIds.has(ticket.service_id))
    .flatMap((ticket) => ticket.work_logs)
    .reduce((total, log) => total + log.hours, 0);
}

function mockClientKpi(clientId: number): ClientKpi {
  const client = findMockClient(clientId);
  const service = mockMainService(clientId);
  const hours = mockClientHours(clientId);
  // El tercer cliente queda sin serie para mostrar �sin datos� (CA-8)
  const availability = clientId === 3 ? null : clientId === 1 ? 99.4 : 98.6;
  const slo = service?.plan.slo_availability ?? null;
  return {
    client_id: client.id,
    client_name: client.name,
    service_name: service?.name ?? null,
    service_status: service?.status ?? "operativo",
    availability,
    cumple_objetivo: availability === null || slo === null ? null : availability >= slo,
    latency_p95: clientId === 3 ? null : clientId === 1 ? 0.24 : 0.41,
    sla_compliance: clientId === 3 ? null : 80,
    mttr: clientId === 1 ? 8 : null,
    open_tickets: 1,
    closed_tickets: 2,
    hours,
    cost: hours * 25000,
  };
}

export async function getAgencyDashboard(month?: string): Promise<AgencyDashboard> {
  const mes = month ?? mesActual();
  if ((await detectMode()) === "mock") {
    return {
      month: mes,
      clients: mock.clients.map((client) => mockClientKpi(client.id)),
      technicians: [
        { user_id: 1, name: MOCK_USER_NAME, hours: 30, load: 30 / 120 },
        { user_id: 2, name: "Camilo Torres", hours: 96, load: 96 / 120 },
      ],
    };
  }
  return request<AgencyDashboard>(`/dashboard/agency?month=${encodeURIComponent(mes)}`);
}

export async function getClientDashboard(clientId: number, month?: string): Promise<ClientDashboardKpi> {
  const mes = month ?? mesActual();
  if ((await detectMode()) === "mock") {
    const { hours: _hours, cost: _cost, ...client } = mockClientKpi(clientId);
    return {
      ...client,
      slo_availability: mockMainService(clientId)?.plan.slo_availability ?? null,
    };
  }
  return request<ClientDashboardKpi>(
    `/dashboard/client/${clientId}?month=${encodeURIComponent(mes)}`,
  );
}

// Fallas del mes para el portal: la API filtra por cliente y por mes; el mock lo hace en memoria
export async function listClientIncidents(
  clientId: number,
  month?: string,
): Promise<ClientIncident[]> {
  const mes = month ?? mesActual();
  if ((await detectMode()) === "mock") {
    ensureMockIncidents();
    return incidentMock.incidents
      .filter((incident) => incident.client_id === clientId)
      .map(({ id, title, status, started_at }) => ({ id, title, status, started_at }));
  }
  return request<ClientIncident[]>(
    `/dashboard/client/${clientId}/incidents?month=${encodeURIComponent(mes)}`,
  );
}

// Serie de prueba: un punto cada 5 min durante un dia, con el hueco de la caida de la demo (CA-6)
function mockSeries(clientId: number, month: string): ClientSeries {
  const service = mockMainService(clientId);
  const slo = service?.plan.slo_availability ?? null;
  const dia = `${month}-05`;
  const availability: SeriesPoint[] = [];
  const latency: SeriesPoint[] = [];
  for (let minuto = 0; minuto < 24 * 60; minuto += 5) {
    // Hueco de 10:00 a 10:30: el sitio dejo de responder (la grafica queda cortada)
    if (minuto >= 10 * 60 && minuto < 10 * 60 + 30) continue;
    const hora = String(Math.floor(minuto / 60)).padStart(2, "0");
    const mins = String(minuto % 60).padStart(2, "0");
    const timestamp = new Date(`${dia}T${hora}:${mins}:00-05:00`).toISOString();
    availability.push({ timestamp, value: 100 });
    latency.push({ timestamp, value: minuto === 10 * 60 + 30 ? 1.8 : 0.24 });
  }
  return { client_id: clientId, month, slo_availability: slo, availability, latency_p95: latency };
}

export async function getClientSeries(clientId: number, month?: string): Promise<ClientSeries> {
  const mes = month ?? mesActual();
  if ((await detectMode()) === "mock") return mockSeries(clientId, mes);
  return request<ClientSeries>(`/dashboard/client/${clientId}/series?month=${encodeURIComponent(mes)}`);
}
