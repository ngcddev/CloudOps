# Escribe los diagramas Mermaid del informe final (uno por figura). Cada elemento sale de HECHOS.md (§12–§15), es decir, del código y de la corrida de evidencias.
from pathlib import Path

AQUI = Path(__file__).resolve().parent
D = {}

D["01-c4-contexto"] = """flowchart LR
  tec([Técnico de la agencia]):::persona
  cli([Cliente pyme]):::persona
  vis([Visitante del sitio]):::persona
  hub[CloudOps Client Hub<br/>consola, portal, incidentes, GitOps, asistente]:::sistema
  sitios[Sitios de los clientes<br/>restaurante, ferretería, consultorio]:::externo
  gh[GitHub<br/>código y CI]:::externo
  oll[Ollama en el equipo anfitrión<br/>LLM y embeddings locales]:::externo
  tec -- gestiona cambios, incidentes y reportes --> hub
  cli -- pide cambios y ve su disponibilidad --> hub
  vis -- usa --> sitios
  hub -- publica por GitOps y vigila --> sitios
  hub -- pregunta y recibe texto --> oll
  gh -. código fuente .-> hub
  classDef persona fill:#ffffff,stroke:#111,stroke-width:1px
  classDef sistema fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
  classDef externo fill:#f5f5f5,stroke:#555,stroke-dasharray:4 3
"""

D["02-c4-contenedores"] = """flowchart TB
  subgraph k3d[Clúster k3d]
    direction TB
    subgraph hubns[namespace hub]
      web[web · React/Vite<br/>consola y portal]
      api[api · FastAPI<br/>15 routers, 61 endpoints]
      voz[voz · faster-whisper + Piper]
      pg[(PostgreSQL 16)]
      bs[Backstage]
    end
    subgraph plat[Plataforma]
      gitea[Gitea + Actions + registro<br/>hub-gitops]
      argo[Argo CD 2.13<br/>9 Applications + ApplicationSet]
      mlf[MLflow 3.18 · ns mlops]
    end
    subgraph mon[namespace monitoring]
      prom[Prometheus] --> am[Alertmanager]
      bb[Blackbox] --> prom
      loki[Loki]
      tempo[Tempo]
      graf[Grafana]
    end
    subgraph cli[namespaces cliente-*]
      s1[restaurante]
      s2[ferreteria · staging]
      s3[consultorio web + api]
    end
  end
  oll[Ollama · equipo anfitrión]
  hubns ~~~ plat
  plat ~~~ mon
  mon ~~~ cli
  web --> api
  api --> pg
  api --> voz
  api -- commits de versión --> gitea
  api -- estado de sincronía --> argo
  api -- métricas --> prom
  api -- trazas OTLP --> tempo
  api -- chat y embeddings --> oll
  argo -- sincroniza --> cli
  argo -- lee --> gitea
  bb -- sondea cada 5 s --> cli
  am -- webhook --> api
  graf --> prom
  graf --> loki
"""

D["03-c4-componentes"] = """flowchart LR
  subgraph api[API del Hub · FastAPI]
    direction TB
    r1[auth · clients · catalog]
    r2[tickets · change_requests · services]
    r3[security · pipeline]
    r4[incidents · alerts]
    r5[dashboard · reports · audit_logs]
    r6[assistant · ai_drafts]
    s1[ticket_flow · change_flow · sla · priority]
    s2[gitops_publish · deploy_watch · rollback · provisioning]
    s3[security_gate]
    s4[incident_flow · incident_alerts · aiops]
    s5[kpi · reports · report_pdf · audit]
    s6[assistant_gate · assistant_context · knowledge · redaccion · ai_drafts]
    i[integrations: gitea · argocd · prometheus · loki · ollama · voz]
  end
  r1 --> s1
  r2 --> s1
  r2 --> s2
  r3 --> s3
  r4 --> s4
  r5 --> s5
  r6 --> s6
  s2 --> i
  s4 --> i
  s5 --> i
  s6 --> i
"""

D["04-despliegue"] = """flowchart TB
  subgraph laptop[Laptop del equipo · Windows 11 · RTX 4060 8 GB]
    subgraph dd[Docker Desktop]
      subgraph nodo[k3d-hub-server-0 · k3s v1.32.9]
        traefik[Traefik · Ingress *.hub.local]
        pods[Pods: hub, argocd, gitea, monitoring, mlops, cliente-*]
      end
      lb[k3d-hub-serverlb · puertos 80/443]
      runner[runner de Gitea Actions]
      compose[docker compose · entorno de desarrollo]
    end
    ollama[Ollama · GPU<br/>qwen2.5:7b · nomic-embed-text]
  end
  navegador([Navegador]) -- https://hub.local --> lb --> traefik --> pods
  pods -- host.docker.internal:11434 --> ollama
  runner -- puerta de seguridad --> pods
"""

D["05-flujo-datos"] = """flowchart LR
  c([Cliente]) -- solicitud de cambio --> hub[Hub API]
  t([Técnico 2]) -- aprueba --> hub
  hub -- ¿versión con puerta OK? --> sec[(security_runs)]
  hub -- commit newTag --> git[(Gitea · hub-gitops)]
  git --> argo[Argo CD] --> sitio[Sitio del cliente]
  bb[Blackbox] -- probe_success --> prom[Prometheus] --> am[Alertmanager]
  sitio -.sondeo.-> bb
  am -- webhook --> hub
  hub -- incidente P1 + plan de rollback --> db[(PostgreSQL)]
  hub -- git revert --> git
  q([Pregunta]) --> red[redacción de secretos] --> gate[compuerta] --> rag[RAG: kb_chunks] --> oll[Ollama] --> hub
  hub -- spans sin texto --> tempo[Tempo]
"""

D["06-modelo-er"] = """erDiagram
  agencies ||--o{ clients : tiene
  clients ||--o{ projects : tiene
  clients ||--o{ users : "usuarios del portal"
  clients ||--o{ reports : recibe
  projects ||--o{ services : contiene
  plans ||--o{ services : rige
  services ||--o{ tickets : recibe
  services ||--o{ change_requests : cambia
  services ||--o{ deployments : registra
  services ||--o{ incidents : sufre
  services ||--o{ security_runs : verifica
  security_runs ||--o{ security_checks : incluye
  tickets ||--o{ ticket_events : historial
  tickets ||--o{ work_logs : horas
  tickets ||--o| change_requests : origina
  incidents ||--o{ incident_events : historial
  incidents ||--o{ ai_drafts : borradores
  users ||--o{ audit_logs : "actúa en"
  users ||--o{ ai_queries : pregunta
  kb_documents ||--o{ kb_chunks : trozos
"""

D["07-seq-rag"] = """sequenceDiagram
  actor T as Técnico
  participant API as Hub API
  participant R as Redacción
  participant G as Compuerta (Naive Bayes)
  participant K as RAG (kb_chunks)
  participant O as Ollama
  T->>API: POST /api/assistant/ask
  API->>R: tapar secretos de la pregunta
  API->>G: ¿trata del Hub?
  alt fuera de tema
    G-->>API: no despertar al LLM
    API-->>T: respuesta fija (sin LLM)
  else del tema
    API->>O: embedding de la pregunta (nomic-embed-text)
    API->>K: top-4 por coseno (umbral 0,60)
    API->>O: prompt v3 + contexto cerrado (qwen2.5:7b)
    O-->>API: respuesta
    API-->>T: respuesta en texto plano + registro en ai_queries
  end
"""

D["08-seq-borradores"] = """sequenceDiagram
  actor T as Técnico
  participant API as Hub API
  participant O as Ollama
  actor C as Cliente
  T->>API: POST /api/incidents/{id}/ai-drafts
  API->>API: hechos cerrados del incidente (redactados)
  API->>O: borrador de resumen y de mensaje al cliente
  O-->>API: textos
  API->>API: verificar términos prohibidos y horas
  alt no pasa
    API-->>T: texto base determinista para editar
  else pasa
    API-->>T: borradores para revisar
  end
  T->>API: aprobar (queda en la bitácora)
  API-->>C: mensaje aprobado en el portal
"""

D["09-seq-voz"] = """sequenceDiagram
  actor T as Técnico (navegador)
  participant W as Hub web
  participant API as Hub API
  participant V as Servicio de voz
  participant O as Ollama
  T->>W: pulsa «Hablar» (micrófono)
  W->>API: POST /api/assistant/voice/transcribe (audio ≤ 30 s)
  API->>V: faster-whisper small
  V-->>API: texto
  API-->>W: transcripción redactada (el usuario la corrige)
  W->>API: POST /api/assistant/ask
  API->>O: respuesta
  API-->>W: texto
  W->>API: POST /api/assistant/voice/speak
  API->>V: Piper es_MX
  V-->>W: audio WAV
"""

D["10-seq-cicd"] = """sequenceDiagram
  actor Dev as Equipo
  participant G as Gitea (repo del sitio)
  participant P as Puerta (Gitea Actions)
  participant H as Hub
  actor T1 as Técnico que pide
  actor T2 as Técnico que aprueba
  participant HG as hub-gitops
  participant A as Argo CD
  Dev->>G: push de etiqueta vX
  G->>P: dispara la puerta
  P->>H: abre la corrida
  P->>P: Gitleaks, pruebas y build, Trivy, Syft, Cosign, verify
  P->>H: cierra la corrida (ok / falla)
  T1->>H: solicitud de cambio a vX
  T2->>H: aprueba (no puede ser T1)
  H->>HG: commit newTag: vX
  A->>HG: detecta el cambio
  A->>A: sincroniza el namespace del cliente
  H->>A: vigila hasta Synced/Healthy (desplegada o fallida)
"""

D["11-seq-recuperacion"] = """sequenceDiagram
  participant S as Sitio (v2 rota)
  participant B as Blackbox/Prometheus
  participant AM as Alertmanager
  participant H as Hub
  actor T as Técnico
  participant HG as hub-gitops
  participant A as Argo CD
  S-->>B: probe_success = 0
  B->>AM: SitioCaido (for 30 s)
  AM->>H: webhook
  H->>H: incidente P1 + plan de rollback (48–49 s desde el corte)
  T->>H: rollback
  H->>HG: git revert
  A->>HG: sincroniza v1
  B->>AM: el sondeo vuelve a 1
  AM->>H: resuelta
  H->>H: incidente mitigado, MTTR calculado
"""

D["12-casos-de-uso"] = """flowchart LR
  tec([Técnico]):::a
  cli([Cliente]):::a
  ia([IA local · Ollama]):::s
  alm([Almacenamiento · PostgreSQL y Gitea]):::s
  obs([Observabilidad · Prometheus y Alertmanager]):::s
  subgraph hub[CloudOps Client Hub]
    u1((Pedir un cambio))
    u2((Aprobar un cambio))
    u3((Ver disponibilidad y SLA))
    u4((Atender un incidente))
    u5((Hacer rollback))
    u6((Preguntar al asistente, también por voz))
    u7((Generar borradores y reportes))
    u8((Consultar la bitácora))
  end
  cli --- u1
  cli --- u3
  tec --- u2
  tec --- u4
  tec --- u5
  tec --- u6
  tec --- u7
  tec --- u8
  u6 --- ia
  u7 --- ia
  u2 --- alm
  u5 --- alm
  obs --- u4
  classDef a fill:#fff,stroke:#111
  classDef s fill:#f5f5f5,stroke:#555,stroke-dasharray:4 3
"""

for nombre, texto in D.items():
    (AQUI / f"{nombre}.mmd").write_text(texto, encoding="utf-8", newline="\n")
print(len(D), "diagramas escritos")
