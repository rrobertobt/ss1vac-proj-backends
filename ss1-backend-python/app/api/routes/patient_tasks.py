from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.db.models import PatientTask, Patient, ClinicalRecord
from app.api.routes.patient_tasks_schemas import (
    PatientTaskCreate,
    PatientTaskUpdate,
    PatientTaskResponse,
)

router = APIRouter(prefix="/patients", tags=["patient-tasks"])


@router.post("/{patient_id}/tasks", response_model=PatientTaskResponse, status_code=201)
async def create_patient_task(
    patient_id: int,
    task_data: PatientTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.ASSIGN_PATIENT_TASKS)),
):
    """
    Crear una tarea para un paciente (desde clínico).
    Requiere permiso: ASSIGN_PATIENT_TASKS
    Roles: PSYCHOLOGIST, PSYCHIATRIST
    """
    
    # Verificar que el paciente existe
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.unique().scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Paciente con ID {patient_id} no encontrado"
        )
    
    # Verificar que el paciente esté activo
    if patient.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="No se puede asignar tarea a un paciente inactivo"
        )
    
    # Verificar historia clínica si se proporciona
    if task_data.clinical_record_id:
        result = await db.execute(
            select(ClinicalRecord).where(ClinicalRecord.id == task_data.clinical_record_id)
        )
        clinical_record = result.unique().scalar_one_or_none()
        
        if not clinical_record:
            raise HTTPException(
                status_code=404,
                detail=f"Historia clínica con ID {task_data.clinical_record_id} no encontrada"
            )
        
        # Verificar que la historia clínica pertenece al paciente
        if clinical_record.patient_id != patient_id:
            raise HTTPException(
                status_code=400,
                detail="La historia clínica no pertenece al paciente"
            )
    
    # Obtener employee_id del usuario actual (si está disponible)
    assigned_by_employee_id = getattr(current_user, 'employee_id', None) if hasattr(current_user, 'employee_id') else None
    
    # Crear la tarea
    new_task = PatientTask(
        patient_id=patient_id,
        clinical_record_id=task_data.clinical_record_id,
        assigned_by_employee_id=assigned_by_employee_id,
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        status="PENDING",
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    return new_task


@router.get("/{patient_id}/tasks", response_model=list[PatientTaskResponse])
async def list_patient_tasks(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.VIEW_PATIENTS)),
):
    """
    Listar tareas de un paciente.
    Requiere permiso: VIEW_PATIENTS
    """
    
    # Verificar que el paciente existe
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.unique().scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Paciente con ID {patient_id} no encontrado"
        )
    
    # Obtener tareas
    result = await db.execute(
        select(PatientTask)
        .where(PatientTask.patient_id == patient_id)
        .order_by(PatientTask.created_at.desc())
    )
    tasks = result.unique().scalars().all()
    
    return tasks


@router.get("/me/tasks", response_model=list[PatientTaskResponse])
async def list_my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_db),  # Solo requiere estar autenticado
):
    """
    Listar tareas del paciente actual.
    Solo requiere autenticación (para pacientes).
    """
    
    # Verificar que el usuario tiene un patient_id
    patient_id = getattr(current_user, 'patient_id', None) if hasattr(current_user, 'patient_id') else None
    
    if not patient_id:
        raise HTTPException(
            status_code=400,
            detail="El usuario actual no tiene un paciente asociado"
        )
    
    # Obtener tareas del paciente
    result = await db.execute(
        select(PatientTask)
        .where(PatientTask.patient_id == patient_id)
        .order_by(PatientTask.created_at.desc())
    )
    tasks = result.unique().scalars().all()
    
    return tasks


@router.patch("/tasks/{task_id}", response_model=PatientTaskResponse)
async def update_patient_task(
    task_id: int,
    task_data: PatientTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permissions(Permission.ASSIGN_PATIENT_TASKS)),
):
    """
    Actualizar una tarea de paciente.
    Requiere permiso: ASSIGN_PATIENT_TASKS
    Roles: PSYCHOLOGIST, PSYCHIATRIST
    """
    
    # Buscar la tarea
    result = await db.execute(
        select(PatientTask).where(PatientTask.id == task_id)
    )
    task = result.unique().scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Tarea con ID {task_id} no encontrada"
        )
    
    # Validar estado si se proporciona
    if task_data.status and task_data.status not in ["PENDING", "COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido. Use PENDING, COMPLETED o CANCELLED"
        )
    
    # Actualizar solo los campos proporcionados
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    return task
