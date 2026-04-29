"""Issued certifications management — approve/reject/revoke certification requests."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from src.core.audit import AuditAction, log_action
from src.core.permissions import require_admin
from src.db.models.learning_platform import (
    CertificationRequestStatus,
    Course,
    CourseCertification,
    User,
    UserCertification,
)
from src.db.session import get_db
from src.schemas.admin_panel import (
    CertificationApproveRequest,
    CertificationRejectRequest,
    CertificationStats,
    UserCertificationAdminList,
    UserCertificationAdminRead,
)


router = APIRouter(prefix="/certifications-issued")


def _to_read(uc: UserCertification, user: User, cc: CourseCertification, course: Course) -> UserCertificationAdminRead:
    return UserCertificationAdminRead(
        id=uc.id,
        user_id=user.id,
        user_full_name=f"{user.first_name} {user.last_name}",
        user_email=user.email,
        course_certification_id=cc.id,
        certification_title=cc.title,
        course_id=course.id,
        course_title=course.title,
        status=uc.status.value,
        requested_at=uc.requested_at,
        approved_at=uc.approved_at,
        issued_at=uc.issued_at,
        rejected_at=uc.rejected_at,
        rejection_reason=uc.rejection_reason,
        expiration_date=uc.expiration_date,
        certificate_code=uc.certificate_code,
        certificate_url=uc.certificate_url,
    )


def _generate_certificate_code() -> str:
    """Short random identifier for the certificate."""
    return f"CERT-{secrets.token_hex(8).upper()}"


@router.get("", response_model=UserCertificationAdminList)
def list_user_certifications(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="requested | approved | issued | rejected"),
    course_id: str | None = Query(None),
    user_id: str | None = Query(None),
    search: str | None = Query(None, description="Search by user name/email"),
):
    """Paginated list of user certification requests."""
    q = (
        db.query(UserCertification, User, CourseCertification, Course)
        .join(User, User.id == UserCertification.user_id)
        .join(CourseCertification, CourseCertification.id == UserCertification.course_certification_id)
        .join(Course, Course.id == CourseCertification.course_id)
    )

    if status:
        try:
            q = q.filter(UserCertification.status == CertificationRequestStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
    if course_id:
        q = q.filter(Course.id == course_id)
    if user_id:
        q = q.filter(UserCertification.user_id == user_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like)))

    total = q.count()
    rows = (
        q.order_by(desc(UserCertification.requested_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_to_read(uc, u, cc, c) for uc, u, cc, c in rows]
    return UserCertificationAdminList(total=total, page=page, page_size=page_size, items=items)


@router.get("/{user_certification_id}", response_model=UserCertificationAdminRead)
def get_user_certification(
    user_certification_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UserCertification, User, CourseCertification, Course)
        .join(User, User.id == UserCertification.user_id)
        .join(CourseCertification, CourseCertification.id == UserCertification.course_certification_id)
        .join(Course, Course.id == CourseCertification.course_id)
        .filter(UserCertification.id == user_certification_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Certificación no encontrada")
    uc, u, cc, c = row
    return _to_read(uc, u, cc, c)


@router.post("/{user_certification_id}/approve", response_model=UserCertificationAdminRead)
def approve_certification(
    user_certification_id: str,
    body: CertificationApproveRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve a pending certification. If `issue_now` is True, also issues it."""
    uc = db.query(UserCertification).filter(UserCertification.id == user_certification_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Certificación no encontrada")

    if uc.status not in (CertificationRequestStatus.REQUESTED, CertificationRequestStatus.APPROVED):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede aprobar una certificación en estado '{uc.status.value}'",
        )

    now = datetime.utcnow()
    uc.status = (
        CertificationRequestStatus.ISSUED if body.issue_now else CertificationRequestStatus.APPROVED
    )
    uc.approved_at = now
    if body.issue_now:
        uc.issued_at = now
        if not uc.certificate_code:
            uc.certificate_code = _generate_certificate_code()
        if body.certificate_url:
            uc.certificate_url = body.certificate_url

    if body.expiration_date:
        uc.expiration_date = body.expiration_date
    elif body.issue_now and not uc.expiration_date:
        # Auto-compute expiration from CourseCertification.validity_days
        cc = db.query(CourseCertification).filter(CourseCertification.id == uc.course_certification_id).first()
        if cc and cc.validity_days:
            uc.expiration_date = now + timedelta(days=cc.validity_days)

    db.commit()

    action = AuditAction.CERT_ISSUED if body.issue_now else AuditAction.CERT_APPROVED
    log_action(
        db,
        action,
        user_id=current_user.id,
        resource_type="user_certification",
        resource_id=uc.id,
        description=(
            f"Certificación {'emitida' if body.issue_now else 'aprobada'} para usuario {uc.user_id}"
        ),
        extra_data={
            "target_user_id": uc.user_id,
            "course_certification_id": uc.course_certification_id,
            "certificate_code": uc.certificate_code,
        },
        request=request,
    )

    return get_user_certification(user_certification_id=user_certification_id, _=current_user, db=db)


@router.post("/{user_certification_id}/reject", response_model=UserCertificationAdminRead)
def reject_certification(
    user_certification_id: str,
    body: CertificationRejectRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    uc = db.query(UserCertification).filter(UserCertification.id == user_certification_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Certificación no encontrada")

    if uc.status == CertificationRequestStatus.ISSUED:
        raise HTTPException(
            status_code=400,
            detail="No se puede rechazar una certificación ya emitida — usa revocar",
        )

    uc.status = CertificationRequestStatus.REJECTED
    uc.rejected_at = datetime.utcnow()
    uc.rejection_reason = body.reason
    db.commit()

    log_action(
        db,
        AuditAction.CERT_REJECTED,
        user_id=current_user.id,
        resource_type="user_certification",
        resource_id=uc.id,
        description=f"Certificación rechazada: {body.reason}",
        extra_data={"target_user_id": uc.user_id, "reason": body.reason},
        request=request,
    )

    return get_user_certification(user_certification_id=user_certification_id, _=current_user, db=db)


@router.post("/{user_certification_id}/revoke", response_model=UserCertificationAdminRead)
def revoke_certification(
    user_certification_id: str,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Revoke an already-issued certification. Sets status back to rejected."""
    uc = db.query(UserCertification).filter(UserCertification.id == user_certification_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Certificación no encontrada")

    if uc.status != CertificationRequestStatus.ISSUED:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden revocar certificaciones emitidas",
        )

    uc.status = CertificationRequestStatus.REJECTED
    uc.rejected_at = datetime.utcnow()
    uc.rejection_reason = "Revocada por administración"
    db.commit()

    log_action(
        db,
        AuditAction.CERT_REVOKED,
        user_id=current_user.id,
        resource_type="user_certification",
        resource_id=uc.id,
        description=f"Certificación revocada del usuario {uc.user_id}",
        extra_data={"target_user_id": uc.user_id, "certificate_code": uc.certificate_code},
        request=request,
    )

    return get_user_certification(user_certification_id=user_certification_id, _=current_user, db=db)


@router.get("/stats/summary", response_model=CertificationStats)
def certification_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Aggregate stats over user certifications."""
    counts = dict(
        db.query(UserCertification.status, func.count(UserCertification.id))
        .group_by(UserCertification.status)
        .all()
    )

    requested = int(counts.get(CertificationRequestStatus.REQUESTED, 0))
    approved = int(counts.get(CertificationRequestStatus.APPROVED, 0))
    issued = int(counts.get(CertificationRequestStatus.ISSUED, 0))
    rejected = int(counts.get(CertificationRequestStatus.REJECTED, 0))

    # Avg approval time (only on those approved or issued)
    rows = (
        db.query(UserCertification.requested_at, UserCertification.approved_at)
        .filter(UserCertification.approved_at.isnot(None))
        .all()
    )
    avg_hours: float | None = None
    if rows:
        deltas = [
            (a - r).total_seconds() / 3600.0
            for r, a in rows
            if r and a and a > r
        ]
        if deltas:
            avg_hours = round(sum(deltas) / len(deltas), 2)

    return CertificationStats(
        total_requested=requested,
        total_approved=approved,
        total_issued=issued,
        total_rejected=rejected,
        avg_approval_time_hours=avg_hours,
    )
