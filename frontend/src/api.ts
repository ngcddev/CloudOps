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

export interface ClientInput {
  name: string;
  contact_name: string;
  email: string;
  phone: string;
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

  return { plans, slaPolicies, clients, newId: () => nextId++ };
})();

function findMockClient(id: number): ClientDetail {
  const client = mock.clients.find((c) => c.id === id);
  if (!client) throw new ApiError("El cliente no existe.", 404);
  return client;
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
