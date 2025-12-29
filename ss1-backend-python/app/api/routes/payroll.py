from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, noload
from typing import List

from app.api.deps import get_db, require_permissions
from app.core.permissions import Permission
from app.db.models import PayrollPeriod, PayrollRecord, Employee, Appointment, User
from .payroll_schemas import (
    CreatePayrollPeriodSchema,
    UpdatePayrollRecordSchema,
    PayrollPeriodResponseSchema,
    PayrollRecordResponseSchema,
    PayrollPeriodRecordsResponseSchema,
)

router = APIRouter(prefix="/payroll", tags=["payroll"])


# GET /payroll/periods
@router.get("/periods", response_model=List[PayrollPeriodResponseSchema])
async def get_periods(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)),
):
    """
    Obtener todos los períodos de nómina
    """
    result = await db.execute(
        select(PayrollPeriod)
        .options(noload(PayrollPeriod.records))
        .order_by(PayrollPeriod.period_start.desc())
    )
    periods = result.unique().scalars().all()
    return periods


# POST /payroll/periods
@router.post("/periods", response_model=PayrollPeriodResponseSchema)
async def create_period(
    data: CreatePayrollPeriodSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.MANAGE_PAYROLL)),
):
    """
    Crear un nuevo período de nómina
    """
    period = PayrollPeriod(
        period_start=data.period_start,
        period_end=data.period_end,
        status="OPEN",
    )
    db.add(period)
    await db.commit()
    await db.refresh(period, attribute_names=['id', 'period_start', 'period_end', 'status', 'created_at', 'updated_at'])
    return period


# POST /payroll/periods/:id/calculate
@router.post("/periods/{period_id}/calculate")
async def calculate_payroll(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.MANAGE_PAYROLL)),
):
    """
    Calcular la nómina para todos los empleados activos en el período
    """
    # Verificar que el período exista
    result = await db.execute(
        select(PayrollPeriod)
        .options(noload(PayrollPeriod.records))
        .where(PayrollPeriod.id == period_id)
    )
    period = result.unique().scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Period with ID {period_id} not found",
        )

    if period.status != "OPEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period status must be OPEN to calculate",
        )

    # Obtener todos los empleados activos
    result = await db.execute(select(Employee).where(Employee.status == "ACTIVE"))
    employees = result.unique().scalars().all()

    employees_processed = 0

    for employee in employees:
        # A) Base salary
        base_salary_amount = float(employee.base_salary or 0)

        # B) Contar sesiones completadas en el período
        sessions_result = await db.execute(
            select(func.count(Appointment.id))
            .where(Appointment.professional_id == employee.id)
            .where(Appointment.status == "COMPLETED")
            .where(Appointment.start_datetime >= period.period_start)
            .where(Appointment.start_datetime <= period.period_end)
        )
        sessions_count = sessions_result.scalar() or 0

        # C) Calcular pago por sesiones
        session_rate = float(employee.session_rate or 0)
        sessions_amount = sessions_count * session_rate

        # Obtener el registro existente si hay uno
        existing_record_result = await db.execute(
            select(PayrollRecord)
            .where(PayrollRecord.employee_id == employee.id)
            .where(PayrollRecord.period_id == period_id)
        )
        existing_record = existing_record_result.scalar_one_or_none()

        # Mantener bonuses y other_deductions si ya existen
        bonuses_amount = float(existing_record.bonuses_amount) if existing_record else 0
        other_deductions = float(existing_record.other_deductions) if existing_record else 0

        # D) Calcular IGSS
        igss_percentage = float(employee.igss_percentage or 0)
        igss_deduction = (
            (base_salary_amount + sessions_amount + bonuses_amount) * (igss_percentage / 100)
        )

        # E) Calcular total
        total_pay = (
            base_salary_amount
            + sessions_amount
            + bonuses_amount
            - igss_deduction
            - other_deductions
        )

        # F) UPSERT
        if existing_record:
            # UPDATE
            existing_record.base_salary_amount = base_salary_amount
            existing_record.sessions_count = sessions_count
            existing_record.sessions_amount = sessions_amount
            existing_record.igss_deduction = igss_deduction
            existing_record.total_pay = total_pay
            # No modificamos bonuses_amount ni other_deductions (ajustes manuales)
        else:
            # INSERT
            new_record = PayrollRecord(
                employee_id=employee.id,
                period_id=period_id,
                base_salary_amount=base_salary_amount,
                sessions_count=sessions_count,
                sessions_amount=sessions_amount,
                bonuses_amount=bonuses_amount,
                igss_deduction=igss_deduction,
                other_deductions=other_deductions,
                total_pay=total_pay,
            )
            db.add(new_record)

        employees_processed += 1

    await db.commit()

    return {
        "message": "Payroll calculated successfully",
        "employees_processed": employees_processed,
    }


# GET /payroll/periods/:id/records
@router.get("/periods/{period_id}/records", response_model=PayrollPeriodRecordsResponseSchema)
async def get_period_records(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)),
):
    """
    Obtener todos los registros de nómina de un período
    """
    # Verificar que el período exista
    result = await db.execute(
        select(PayrollPeriod)
        .options(noload(PayrollPeriod.records))
        .where(PayrollPeriod.id == period_id)
    )
    period = result.unique().scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Period with ID {period_id} not found",
        )

    # Obtener los registros con información del empleado
    result = await db.execute(
        select(PayrollRecord)
        .options(
            selectinload(PayrollRecord.employee).options(
                selectinload(Employee.user),
                noload(Employee.payroll_records)
            ),
            noload(PayrollRecord.period)
        )
        .join(Employee, PayrollRecord.employee_id == Employee.id)
        .where(PayrollRecord.period_id == period_id)
        .order_by(Employee.last_name, Employee.first_name)
    )
    records = result.unique().scalars().all()

    return {
        "period": period,
        "records": records,
    }


# GET /payroll/records/:id
@router.get("/records/{record_id}", response_model=PayrollRecordResponseSchema)
async def get_payroll_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)),
):
    """
    Obtener el detalle de un registro de nómina específico
    """
    result = await db.execute(
        select(PayrollRecord)
        .options(
            noload(PayrollRecord.employee),
            noload(PayrollRecord.period),
        )
        .where(PayrollRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll record with ID {record_id} not found",
        )

    return record


# PATCH /payroll/records/:id
@router.patch("/records/{record_id}", response_model=PayrollRecordResponseSchema)
async def update_payroll_record(
    record_id: int,
    data: UpdatePayrollRecordSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.MANAGE_PAYROLL)),
):
    """
    Actualizar bonos o deducciones de un registro de nómina
    """
    # Obtener el registro
    result = await db.execute(
        select(PayrollRecord)
        .options(
            selectinload(PayrollRecord.period).options(noload(PayrollPeriod.records)),
            noload(PayrollRecord.employee)
        )
        .where(PayrollRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll record with ID {record_id} not found",
        )

    # Verificar que el período aún esté OPEN
    if record.period.status != "OPEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update records for a closed or paid period",
        )

    # Obtener employee para recalcular IGSS
    result = await db.execute(select(Employee).where(Employee.id == record.employee_id))
    employee = result.scalar_one_or_none()

    # Actualizar bonos o deducciones
    if data.bonuses_amount is not None:
        record.bonuses_amount = data.bonuses_amount
    if data.other_deductions is not None:
        record.other_deductions = data.other_deductions

    # Recalcular IGSS con los nuevos valores
    igss_percentage = float(employee.igss_percentage or 0)
    record.igss_deduction = (
        (float(record.base_salary_amount) + float(record.sessions_amount) + float(record.bonuses_amount))
        * (igss_percentage / 100)
    )

    # Recalcular total
    record.total_pay = (
        float(record.base_salary_amount)
        + float(record.sessions_amount)
        + float(record.bonuses_amount)
        - float(record.igss_deduction)
        - float(record.other_deductions)
    )

    await db.commit()
    await db.refresh(record, attribute_names=['id', 'employee_id', 'period_id', 'base_salary_amount', 'sessions_count', 'sessions_amount', 'bonuses_amount', 'igss_deduction', 'other_deductions', 'total_pay', 'paid_at', 'created_at', 'updated_at'])

    return record


# POST /payroll/periods/:id/close
@router.post("/periods/{period_id}/close", response_model=PayrollPeriodResponseSchema)
async def close_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.MANAGE_PAYROLL)),
):
    """
    Cerrar un período de nómina (cambiar status a CLOSED)
    """
    result = await db.execute(
        select(PayrollPeriod)
        .options(noload(PayrollPeriod.records))
        .where(PayrollPeriod.id == period_id)
    )
    period = result.unique().scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Period with ID {period_id} not found",
        )

    if period.status != "OPEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period is already closed or paid",
        )

    period.status = "CLOSED"
    await db.commit()
    await db.refresh(period, attribute_names=['id', 'period_start', 'period_end', 'status', 'created_at', 'updated_at'])

    return period


# POST /payroll/periods/:id/pay
@router.post("/periods/{period_id}/pay", response_model=PayrollPeriodResponseSchema)
async def pay_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.MANAGE_PAYROLL)),
):
    """
    Marcar un período como pagado (cambiar status a PAID)
    """
    result = await db.execute(
        select(PayrollPeriod)
        .options(noload(PayrollPeriod.records))
        .where(PayrollPeriod.id == period_id)
    )
    period = result.unique().scalar_one_or_none()

    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Period with ID {period_id} not found",
        )

    if period.status != "CLOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be CLOSED before paying",
        )

    # Actualizar el período a PAID
    period.status = "PAID"

    # Marcar todos los records como pagados
    result = await db.execute(
        select(PayrollRecord)
        .where(PayrollRecord.period_id == period_id)
        .where(PayrollRecord.paid_at.is_(None))
    )
    records = result.unique().scalars().all()

    from datetime import datetime

    now = datetime.now()
    for record in records:
        record.paid_at = now

    await db.commit()
    await db.refresh(period, attribute_names=['id', 'period_start', 'period_end', 'status', 'created_at', 'updated_at'])

    return period


# GET /payroll/employees/:employeeId/history
@router.get("/employees/{employee_id}/history")
async def get_employee_payroll_history(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Permission.VIEW_PAYROLL, Permission.MANAGE_PAYROLL)),
):
    """
    Obtener el historial de nómina de un empleado
    """
    # Verificar que el empleado exista
    result = await db.execute(
        select(Employee)
        .options(
            selectinload(Employee.user),
            noload(Employee.payroll_records)
        )
        .where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )

    # Obtener los registros con información del período
    result = await db.execute(
        select(PayrollRecord)
        .options(
            selectinload(PayrollRecord.period).options(noload(PayrollPeriod.records)),
            noload(PayrollRecord.employee)
        )
        .where(PayrollRecord.employee_id == employee_id)
        .order_by(PayrollRecord.id.desc())
    )
    records = result.unique().scalars().all()

    return {
        "employee": employee,
        "records": records,
    }
