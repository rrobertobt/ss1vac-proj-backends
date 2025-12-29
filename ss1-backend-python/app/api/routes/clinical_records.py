from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.db.models import ClinicalRecord, Patient, Employee
from app.api.routes.clinical_records_schemas import (
    ClinicalRecordCreate,
    ClinicalRecordUpdate,
    ClinicalRecordResponse,
    ClinicalRecordListResponse,
)

router = APIRouter(prefix="/clinical-records", tags=["clinical-records"])


@router.post("", response_model=ClinicalRecordResponse, status_code=201)
async def create_clinical_record(
    record_data: ClinicalRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.CREATE_PATIENT_CLINICAL_RECORDS)),
):
    """
    Crear una nueva historia clínica (apertura).
    Requiere permiso: CREATE_PATIENT_CLINICAL_RECORDS
    Roles: PSYCHOLOGIST, PSYCHIATRIST, ADMIN
    """
    
    # Verificar que el paciente existe
    result = await db.execute(select(Patient).where(Patient.id == record_data.patient_id))
    patient = result.unique().scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Paciente con ID {record_data.patient_id} no encontrado"
        )
    
    # Verificar que el paciente esté activo
    if patient.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="No se puede crear historia clínica para un paciente inactivo"
        )
    
    # Verificar empleado responsable si se proporciona
    if record_data.responsible_employee_id:
        result = await db.execute(
            select(Employee).where(Employee.id == record_data.responsible_employee_id)
        )
        employee = result.unique().scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=404,
                detail=f"Empleado con ID {record_data.responsible_employee_id} no encontrado"
            )
        
        if employee.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar un empleado inactivo como responsable"
            )
    
    # Verificar si ya existe un número de historia clínica
    if record_data.record_number:
        result = await db.execute(
            select(ClinicalRecord).where(
                ClinicalRecord.record_number == record_data.record_number
            )
        )
        existing_record = result.unique().scalar_one_or_none()
        
        if existing_record:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una historia clínica con el número {record_data.record_number}"
            )
    
    # Crear la historia clínica
    new_record = ClinicalRecord(
        patient_id=record_data.patient_id,
        record_number=record_data.record_number,
        institution_name=record_data.institution_name,
        service=record_data.service,
        opening_date=record_data.opening_date,
        responsible_employee_id=record_data.responsible_employee_id,
        responsible_license=record_data.responsible_license,
        referral_source=record_data.referral_source,
        chief_complaint=record_data.chief_complaint,
        status="ACTIVE",
    )
    
    db.add(new_record)
    await db.commit()
    await db.refresh(new_record)
    
    return new_record


@router.get("", response_model=ClinicalRecordListResponse)
async def list_clinical_records(
    patient_id: Optional[int] = Query(None, alias="patientId", description="Filtrar por ID de paciente"),
    professional_id: Optional[int] = Query(None, alias="professionalId", description="Filtrar por ID de profesional responsable"),
    status: Optional[str] = Query(None, description="Filtrar por estado (ACTIVE, CLOSED)"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Elementos por página"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_PATIENT_CLINICAL_RECORDS)),
):
    """
    Listar historias clínicas con filtros.
    Requiere permiso: VIEW_PATIENT_CLINICAL_RECORDS
    Roles: PSYCHOLOGIST, PSYCHIATRIST, ADMIN
    """
    
    # Construir query base
    query = select(ClinicalRecord).order_by(ClinicalRecord.created_at.desc())
    
    # Aplicar filtros
    if patient_id:
        query = query.where(ClinicalRecord.patient_id == patient_id)
    
    if professional_id:
        query = query.where(ClinicalRecord.responsible_employee_id == professional_id)
    
    if status:
        if status not in ["ACTIVE", "CLOSED"]:
            raise HTTPException(status_code=400, detail="Estado inválido. Use ACTIVE o CLOSED")
        query = query.where(ClinicalRecord.status == status)
    
    # TODO: Implementar lógica para que el profesional solo vea sus propias historias
    # if current_user.role.name == "PSYCHOLOGIST":
    #     query = query.where(ClinicalRecord.responsible_employee_id == current_user.employee.id)
    
    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Aplicar paginación
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Ejecutar query
    result = await db.execute(query)
    records = result.unique().scalars().all()
    
    return {
        "data": records,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit if total > 0 else 0,
        },
    }


@router.get("/me", response_model=list[ClinicalRecordResponse])
async def get_my_clinical_records(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_db),  # Solo requiere estar autenticado
):
    """
    Obtener historias clínicas del paciente actual.
    Solo requiere autenticación (para pacientes).
    """
    
    # Verificar que el usuario tiene un patient_id
    patient_id = current_user.patient.id if (hasattr(current_user, 'patient') and current_user.patient) else None
    
    if not patient_id:
        raise HTTPException(
            status_code=400,
            detail="El usuario actual no tiene un paciente asociado"
        )
    
    # Obtener historias clínicas del paciente
    result = await db.execute(
        select(ClinicalRecord)
        .where(ClinicalRecord.patient_id == patient_id)
        .order_by(ClinicalRecord.created_at.desc())
    )
    records = result.unique().scalars().all()
    
    return records


@router.get("/{record_id}", response_model=ClinicalRecordResponse)
async def get_clinical_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_PATIENT_CLINICAL_RECORDS)),
):
    """
    Obtener detalle de una historia clínica.
    Requiere permiso: VIEW_PATIENT_CLINICAL_RECORDS
    Roles: PSYCHOLOGIST, PSYCHIATRIST, ADMIN
    """
    
    result = await db.execute(
        select(ClinicalRecord).where(ClinicalRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Historia clínica con ID {id} no encontrada"
        )
    
    # TODO: Verificar permisos - profesional solo puede ver sus propias historias
    # if current_user.role.name == "PSYCHOLOGIST":
    #     if record.responsible_employee_id != current_user.employee.id:
    #         raise HTTPException(
    #             status_code=403,
    #             detail="No tiene permiso para ver esta historia clínica"
    #         )
    
    return record


@router.patch("/{record_id}", response_model=ClinicalRecordResponse)
async def update_clinical_record(
    record_id: int,
    record_data: ClinicalRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.EDIT_PATIENT_CLINICAL_RECORDS)),
):
    """
    Actualizar una historia clínica (secciones: antecedentes, plan, diagnósticos).
    Requiere permiso: EDIT_PATIENT_CLINICAL_RECORDS
    Roles: PSYCHOLOGIST, PSYCHIATRIST, ADMIN
    """
    
    # Buscar el registro
    result = await db.execute(
        select(ClinicalRecord).where(ClinicalRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Historia clínica con ID {record_id} no encontrada"
        )
    
    # TODO: Verificar permisos - profesional solo puede editar sus propias historias
    # if current_user.role.name == "PSYCHOLOGIST":
    #     if record.responsible_employee_id != current_user.employee.id:
    #         raise HTTPException(
    #             status_code=403,
    #             detail="No tiene permiso para editar esta historia clínica"
    #         )
    
    # Verificar empleado responsable si se cambia
    if record_data.responsible_employee_id and record_data.responsible_employee_id != record.responsible_employee_id:
        emp_result = await db.execute(
            select(Employee).where(Employee.id == record_data.responsible_employee_id)
        )
        employee = emp_result.unique().scalar_one_or_none()
        
        if not employee:
            raise HTTPException(
                status_code=404,
                detail=f"Empleado con ID {record_data.responsible_employee_id} no encontrado"
            )
        
        if employee.status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar un empleado inactivo como responsable"
            )
    
    # Verificar número de historia clínica si se cambia
    if record_data.record_number and record_data.record_number != record.record_number:
        num_result = await db.execute(
            select(ClinicalRecord).where(
                ClinicalRecord.record_number == record_data.record_number,
                ClinicalRecord.id != record_id
            )
        )
        existing_record = num_result.unique().scalar_one_or_none()
        
        if existing_record:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una historia clínica con el número {record_data.record_number}"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = record_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    await db.commit()
    await db.refresh(record)
    
    return record
