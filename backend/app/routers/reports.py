# Reportes mensuales (spec 013): generar el operativo (agencia) y el ejecutivo (por cliente), verlos y descargarlos en PDF. El cliente solo ve y
# descarga sus propios reportes ejecutivos; el operativo es interno. Los datos del mes quedan congelados al generar el reporte.
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, defer, selectinload

from app.db import get_db
from app.deps import current_user, require_agency
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportIn, ReportOut, ReportSummary
from app.services import audit, kpi, report_pdf, reports
from app.paginacion import Pagina, pagina

router = APIRouter(prefix="/api/reports", tags=["reportes"])


def _nombre_seguro(texto: str) -> str:
    """«Restaurante La Sazón» → «restaurante-la-sazon»: los encabezados HTTP no admiten tildes."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _resumen(r: Report) -> dict:
    return {
        "id": r.id, "kind": r.kind, "client_id": r.client_id, "client_name": r.client.name if r.client is not None else None, "month": r.month,
        "month_label": reports.etiqueta_mes(r.month), "generated_by": r.generated_by.name if r.generated_by is not None else None, "created_at": r.created_at,
    }


def _visible(db: Session, user: User, report_id: int) -> Report:
    """El reporte si el usuario puede verlo; 404 si no existe o es de otro cliente (no se revela que existe)."""
    r = db.scalar(select(Report).options(selectinload(Report.client), selectinload(Report.generated_by)).where(Report.id == report_id))
    if r is None or (user.role != "agencia" and (r.kind != "ejecutivo" or r.client_id != user.client_id)):
        raise HTTPException(status_code=404, detail="El reporte no existe.")
    return r


@router.post("", response_model=ReportOut, status_code=201)
def generate(body: ReportIn, request: Request, db: Session = Depends(get_db), user: User = Depends(require_agency)):
    """Genera y guarda el reporte del mes (por omisión el actual) con los datos de ese momento."""
    month = body.month or kpi.mes_actual()
    if body.kind == "ejecutivo":
        if body.client_id is None:
            raise HTTPException(status_code=422, detail="El reporte ejecutivo necesita el cliente.")
        try:
            data = reports.ejecutivo(db, body.client_id, month)
        except LookupError:
            raise HTTPException(status_code=404, detail="El cliente no existe.") from None
        client_id = body.client_id
    else:
        data, client_id = reports.operativo(db, month), None
    r = Report(kind=body.kind, client_id=client_id, month=month, data=data, generated_by_id=user.id)
    db.add(r)
    db.flush()
    audit.record(db, user, "report.generar", "report", r.id, {"tipo": r.kind, "cliente": client_id, "mes": month}, audit.request_ip(request))
    db.commit()
    return {**_resumen(_visible(db, user, r.id)), "data": r.data}


@router.get("", response_model=list[ReportSummary])
def list_reports(page: Pagina = Depends(pagina), db: Session = Depends(get_db), user: User = Depends(current_user)):
    """La agencia ve todos; un cliente, solo sus reportes ejecutivos."""
    # `data` (el JSON congelado del reporte) no se necesita para el resumen: no se trae de la base (auditoría BE-04)
    consulta = select(Report).options(defer(Report.data), selectinload(Report.client), selectinload(Report.generated_by)).order_by(Report.id.desc()).limit(page.limit).offset(page.offset)
    if user.role != "agencia":
        consulta = consulta.where(Report.kind == "ejecutivo", Report.client_id == user.client_id)
    return [_resumen(r) for r in db.scalars(consulta).all()]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = _visible(db, user, report_id)
    return {**_resumen(r), "data": r.data}


@router.get("/{report_id}/pdf")
def download_pdf(report_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """El PDF sale siempre de los datos congelados: el mismo reporte da el mismo documento."""
    r = _visible(db, user, report_id)
    contenido = report_pdf.ejecutivo_pdf(r.data) if r.kind == "ejecutivo" else report_pdf.operativo_pdf(r.data)
    nombre = "-".join(p for p in ("reporte", r.kind, r.month, _nombre_seguro(r.client.name) if r.client is not None else "") if p) + ".pdf"
    return Response(content=contenido, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{nombre}"'})
