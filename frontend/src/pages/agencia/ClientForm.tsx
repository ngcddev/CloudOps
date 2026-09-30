// Pantalla "Registrar cliente": crea el cliente con su primer proyecto y servicio con plan.
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { listPlans, registerClient, type Plan, type Template } from "../../api";

// Valores del formulario; todos son texto porque vienen de los campos
const emptyForm = {
  name: "",
  contact_name: "",
  email: "",
  phone: "",
  project_name: "",
  project_description: "",
  service_name: "Sitio web",
  host: "",
  template: "landing" as Template,
  namespace: "",
  plan_id: "",
};

type FormValues = typeof emptyForm;
type FieldErrors = Partial<Record<keyof FormValues, string>>;

// Reglas mínimas antes de enviar (CA-5); la API repite las mismas validaciones
function validate(values: FormValues): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.name.trim()) errors.name = "El nombre del cliente es obligatorio.";
  if (values.email && !/^\S+@\S+\.\S+$/.test(values.email)) errors.email = "El correo no es válido.";
  if (!values.project_name.trim()) errors.project_name = "El nombre del proyecto es obligatorio.";
  if (!values.service_name.trim()) errors.service_name = "El nombre del servicio es obligatorio.";
  if (!values.host.trim()) errors.host = "La dirección del sitio es obligatoria.";
  if (!values.namespace.trim()) errors.namespace = "El espacio en el clúster es obligatorio.";
  if (!values.plan_id) errors.plan_id = "Elija un plan: un servicio no puede quedar sin plan.";
  return errors;
}

export default function ClientForm() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [values, setValues] = useState<FormValues>(emptyForm);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listPlans()
      .then(setPlans)
      .catch((e: Error) => setSubmitError(`No se pudieron cargar los planes: ${e.message}`));
  }, []);

  function update(field: keyof FormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    try {
      const client = await registerClient(
        {
          name: values.name.trim(),
          contact_name: values.contact_name.trim(),
          email: values.email.trim(),
          phone: values.phone.trim(),
        },
        { name: values.project_name.trim(), description: values.project_description.trim() },
        {
          name: values.service_name.trim(),
          host: values.host.trim(),
          template: values.template,
          namespace: values.namespace.trim(),
          plan_id: Number(values.plan_id),
        },
      );
      navigate("/agencia/clientes", { state: { created: client.name } });
    } catch (e) {
      setSubmitError((e as Error).message);
      setSaving(false);
    }
  }

  // Campo de texto con su etiqueta y su mensaje de error
  function field(name: keyof FormValues, label: string, props: { type?: string; placeholder?: string; required?: boolean } = {}) {
    const { required, ...inputProps } = props;
    return (
      <div className="field">
        <label htmlFor={name}>
          {label}
          {required && <span aria-hidden="true"> *</span>}
        </label>
        <input
          id={name}
          value={values[name]}
          onChange={(e) => update(name, e.target.value)}
          aria-invalid={Boolean(errors[name])}
          aria-describedby={errors[name] ? `${name}-error` : undefined}
          {...inputProps}
        />
        {errors[name] && (
          <span id={`${name}-error`} className="field-error">
            ✕ {errors[name]}
          </span>
        )}
      </div>
    );
  }

  return (
    <>
      <p>
        <Link to="/agencia/clientes">← Volver a clientes</Link>
      </p>
      <h1>Registrar cliente</h1>
      <p className="muted">Los campos con * son obligatorios.</p>

      {submitError && (
        <p className="error" role="alert">
          ✕ No se pudo registrar el cliente: {submitError}
        </p>
      )}

      <form className="form" onSubmit={handleSubmit} noValidate>
        <fieldset>
          <legend>Cliente</legend>
          {field("name", "Nombre", { required: true, placeholder: "Ej. Panadería El Trigal" })}
          {field("contact_name", "Persona de contacto")}
          {field("email", "Correo", { type: "email", placeholder: "contacto@empresa.test" })}
          {field("phone", "Teléfono", { type: "tel", placeholder: "+57 300 000 0000" })}
        </fieldset>

        <fieldset>
          <legend>Proyecto</legend>
          {field("project_name", "Nombre del proyecto", { required: true, placeholder: "Ej. Sitio web El Trigal" })}
          <div className="field">
            <label htmlFor="project_description">Descripción</label>
            <textarea
              id="project_description"
              rows={3}
              value={values.project_description}
              onChange={(e) => update("project_description", e.target.value)}
            />
          </div>
        </fieldset>

        <fieldset>
          <legend>Servicio y plan</legend>
          {field("service_name", "Nombre del servicio", { required: true })}
          {field("host", "Dirección (host)", { required: true, placeholder: "panaderia.hub.local" })}
          <div className="field">
            <label htmlFor="template">Plantilla</label>
            <select id="template" value={values.template} onChange={(e) => update("template", e.target.value)}>
              <option value="landing">Landing estática</option>
              <option value="landing_form">Landing + formulario</option>
            </select>
          </div>
          {field("namespace", "Espacio en el clúster (namespace)", { required: true, placeholder: "cliente-panaderia" })}
          <div className="field">
            <label htmlFor="plan_id">
              Plan<span aria-hidden="true"> *</span>
            </label>
            <select
              id="plan_id"
              value={values.plan_id}
              onChange={(e) => update("plan_id", e.target.value)}
              aria-invalid={Boolean(errors.plan_id)}
              aria-describedby={errors.plan_id ? "plan_id-error" : undefined}
            >
              <option value="">Elija un plan…</option>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} · SLO {plan.slo_availability.toLocaleString("es-CO", { minimumFractionDigits: 1 })} %
                </option>
              ))}
            </select>
            {errors.plan_id && (
              <span id="plan_id-error" className="field-error">
                ✕ {errors.plan_id}
              </span>
            )}
          </div>
        </fieldset>

        <div className="form-actions">
          <button type="submit" className="button" disabled={saving}>
            {saving ? "Registrando…" : "Registrar cliente"}
          </button>
          <Link to="/agencia/clientes" className="button button-secondary">
            Cancelar
          </Link>
        </div>
      </form>
    </>
  );
}
