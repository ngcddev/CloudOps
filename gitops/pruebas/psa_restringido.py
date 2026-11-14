# Verifica sin clúster que los manifiestos renderizados cumplen el perfil Pod Security `restricted` de Kubernetes
# (https://kubernetes.io/docs/concepts/security/pod-security-standards/): lo que Pod Security Admission rechazaría en un namespace
# con `pod-security.kubernetes.io/enforce: restricted`. Revisa Pods, Deployments, StatefulSets, DaemonSets, Jobs y CronJobs.
# Uso:  kubectl kustomize gitops/hub | python gitops/pruebas/psa_restringido.py [etiqueta]
# Sale con código 1 y lista cada incumplimiento si encuentra alguno. Necesita PyYAML (ya lo usa el backend para sus pruebas).
import sys

import yaml

VOLUMENES_PERMITIDOS = {"configMap", "csi", "downwardAPI", "emptyDir", "ephemeral", "persistentVolumeClaim", "projected", "secret"}
CAPACIDADES_AGREGABLES = {"NET_BIND_SERVICE"}


def plantilla_de_pod(recurso: dict) -> dict | None:
    """La especificación del Pod que crea el recurso, o None si el recurso no crea Pods."""
    tipo, spec = recurso.get("kind"), recurso.get("spec") or {}
    if tipo == "Pod":
        return {"metadata": recurso.get("metadata", {}), "spec": spec}
    if tipo in ("Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job"):
        return spec.get("template")
    if tipo == "CronJob":
        return ((spec.get("jobTemplate") or {}).get("spec") or {}).get("template")
    return None


def revisar(recurso: dict) -> list[str]:
    plantilla = plantilla_de_pod(recurso)
    if not plantilla:
        return []
    nombre = f"{recurso['kind']}/{recurso['metadata']['name']}"
    pod = plantilla.get("spec") or {}
    seguridad_pod = pod.get("securityContext") or {}
    problemas: list[str] = []

    for campo in ("hostNetwork", "hostPID", "hostIPC"):
        if pod.get(campo):
            problemas.append(f"{nombre}: usa {campo}")
    for volumen in pod.get("volumes") or []:
        tipos = set(volumen) - {"name"}
        if not tipos <= VOLUMENES_PERMITIDOS:
            problemas.append(f"{nombre}: volumen {volumen['name']} de un tipo no permitido ({', '.join(sorted(tipos - VOLUMENES_PERMITIDOS))})")
    if (seguridad_pod.get("seccompProfile") or {}).get("type") not in ("RuntimeDefault", "Localhost") and not all(
        ((c.get("securityContext") or {}).get("seccompProfile") or {}).get("type") in ("RuntimeDefault", "Localhost")
        for c in (pod.get("containers") or [])
    ):
        problemas.append(f"{nombre}: falta seccompProfile RuntimeDefault")

    for contenedor in (pod.get("initContainers") or []) + (pod.get("containers") or []):
        etiqueta = f"{nombre} (contenedor {contenedor['name']})"
        ctx = contenedor.get("securityContext") or {}
        if ctx.get("privileged"):
            problemas.append(f"{etiqueta}: es privilegiado")
        if ctx.get("allowPrivilegeEscalation") is not False:
            problemas.append(f"{etiqueta}: allowPrivilegeEscalation debe ser false")
        no_root = ctx.get("runAsNonRoot", seguridad_pod.get("runAsNonRoot"))
        if no_root is not True:
            problemas.append(f"{etiqueta}: runAsNonRoot debe ser true")
        if ctx.get("runAsUser", seguridad_pod.get("runAsUser")) == 0:
            problemas.append(f"{etiqueta}: corre como UID 0")
        capacidades = ctx.get("capabilities") or {}
        if "ALL" not in (capacidades.get("drop") or []):
            problemas.append(f"{etiqueta}: debe quitar todas las capacidades (drop: [ALL])")
        sobrantes = set(capacidades.get("add") or []) - CAPACIDADES_AGREGABLES
        if sobrantes:
            problemas.append(f"{etiqueta}: agrega capacidades no permitidas ({', '.join(sorted(sobrantes))})")
        for puerto in contenedor.get("ports") or []:
            if puerto.get("hostPort"):
                problemas.append(f"{etiqueta}: usa hostPort")
    return problemas


def main() -> int:
    etiqueta = sys.argv[1] if len(sys.argv) > 1 else "manifiestos"
    documentos = [d for d in yaml.safe_load_all(sys.stdin) if d]
    revisados = [d for d in documentos if plantilla_de_pod(d)]
    problemas = [p for d in revisados for p in revisar(d)]
    if problemas:
        print(f"✗ {etiqueta}: {len(problemas)} incumplimiento(s) del perfil restricted:")
        for p in problemas:
            print(f"   - {p}")
        return 1
    print(f"✓ {etiqueta}: {len(revisados)} cargas de trabajo cumplen el perfil restricted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
