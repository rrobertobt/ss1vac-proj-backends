from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date
from typing import Optional
from app.api.deps import get_db
from app.db.models import (
    Invoice,
    InvoiceItem,
    Payment,
    PaymentMethod,
    PayrollRecord,
    PayrollPeriod,
    Appointment,
    Patient,
    Employee,
    Service,
    Product,
    Specialty,
    Area,
)
from collections import defaultdict

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/revenue")
async def get_revenue_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    currency: str = Query("GTQ"),
    db: AsyncSession = Depends(get_db),
):
    """
    Reporte de ingresos por período
    Obtiene el total de ingresos basados en facturas y pagos realizados
    """
    # Obtener facturas en el período
    invoices_result = await db.execute(
        select(Invoice)
        .filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.currency == currency,
            Invoice.status.in_(["ISSUED", "PAID"]),
        )
    )
    invoices = invoices_result.scalars().unique().all()

    # Obtener pagos realizados en el período
    payments_result = await db.execute(
        select(Payment)
        .join(Invoice)
        .filter(
            Payment.paid_at.between(start_date, end_date),
            Invoice.currency == currency,
        )
    )
    payments = payments_result.scalars().unique().all()

    # Calcular totales
    total_invoiced = sum(float(inv.total_amount) for inv in invoices)
    total_paid = sum(float(pay.amount) for pay in payments)

    # Agrupar por mes
    by_month = defaultdict(lambda: {"invoiced": 0, "paid": 0, "count": 0})

    for invoice in invoices:
        month = invoice.invoice_date.strftime("%Y-%m")
        by_month[month]["invoiced"] += float(invoice.total_amount)
        by_month[month]["count"] += 1

    for payment in payments:
        month = payment.paid_at.strftime("%Y-%m")
        if month in by_month:
            by_month[month]["paid"] += float(payment.amount)

    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "currency": currency,
        "summary": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "pending": total_invoiced - total_paid,
            "invoices_count": len(invoices),
            "payments_count": len(payments),
        },
        "by_month": [
            {"month": month, **data} for month, data in sorted(by_month.items())
        ],
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date,
                "patient": (
                    f"{inv.patient.first_name} {inv.patient.last_name}"
                    if inv.patient
                    else None
                ),
                "total_amount": float(inv.total_amount),
                "status": inv.status,
            }
            for inv in invoices
        ],
        "payments": [
            {
                "id": pay.id,
                "paid_at": pay.paid_at,
                "amount": float(pay.amount),
                "payment_method": pay.payment_method.name if pay.payment_method else None,
                "invoice_number": pay.invoice.invoice_number if pay.invoice else None,
                "patient": (
                    f"{pay.invoice.patient.first_name} {pay.invoice.patient.last_name}"
                    if pay.invoice and pay.invoice.patient
                    else None
                ),
            }
            for pay in payments
        ],
    }


@router.get("/payroll")
async def get_payroll_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    employee_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Reporte de pagos realizados a empleados
    Obtiene los pagos de nómina a empleados en un período
    """
    # Obtener registros de nómina en el período
    query = (
        select(PayrollRecord)
        .join(PayrollPeriod)
        .filter(
            or_(
                PayrollPeriod.period_start.between(start_date, end_date),
                PayrollPeriod.period_end.between(start_date, end_date),
            )
        )
    )

    if employee_id:
        query = query.filter(PayrollRecord.employee_id == employee_id)

    records_result = await db.execute(query)
    records = records_result.scalars().unique().all()

    # Calcular totales
    summary = {
        "total_base_salary": 0,
        "total_sessions_amount": 0,
        "total_bonuses": 0,
        "total_igss_deduction": 0,
        "total_other_deductions": 0,
        "total_paid": 0,
        "total_sessions": 0,
        "employees_count": len(set(r.employee_id for r in records)),
    }

    for record in records:
        summary["total_base_salary"] += float(record.base_salary_amount)
        summary["total_sessions_amount"] += float(record.sessions_amount)
        summary["total_bonuses"] += float(record.bonuses_amount)
        summary["total_igss_deduction"] += float(record.igss_deduction)
        summary["total_other_deductions"] += float(record.other_deductions)
        summary["total_paid"] += float(record.total_pay)
        summary["total_sessions"] += record.sessions_count

    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": summary,
        "records": [
            {
                "id": record.id,
                "employee": (
                    {
                        "id": record.employee.id,
                        "name": f"{record.employee.first_name} {record.employee.last_name}",
                        "area": record.employee.area.name if record.employee.area else None,
                    }
                    if record.employee
                    else None
                ),
                "period": {
                    "start": record.period.period_start,
                    "end": record.period.period_end,
                    "status": record.period.status,
                }
                if record.period
                else None,
                "base_salary_amount": float(record.base_salary_amount),
                "sessions_count": record.sessions_count,
                "sessions_amount": float(record.sessions_amount),
                "bonuses_amount": float(record.bonuses_amount),
                "igss_deduction": float(record.igss_deduction),
                "other_deductions": float(record.other_deductions),
                "total_pay": float(record.total_pay),
                "paid_at": record.paid_at,
            }
            for record in records
        ],
    }


@router.get("/sales")
async def get_sales_history(
    start_date: date = Query(...),
    end_date: date = Query(...),
    patient_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Historial de ventas
    Obtiene el detalle de todas las ventas (facturas con sus items)
    """
    # Obtener facturas en el período
    query = select(Invoice).filter(
        Invoice.invoice_date.between(start_date, end_date)
    )

    if patient_id:
        query = query.filter(Invoice.patient_id == patient_id)

    query = query.order_by(Invoice.invoice_date.desc())
    
    invoices_result = await db.execute(query)
    invoices = invoices_result.scalars().unique().all()

    # Calcular estadísticas
    total_sales = sum(float(inv.total_amount) for inv in invoices)

    items_stats = {
        "services_count": 0,
        "services_amount": 0,
        "products_count": 0,
        "products_amount": 0,
    }

    for invoice in invoices:
        if invoice.items:
            for item in invoice.items:
                if item.service_id:
                    items_stats["services_count"] += 1
                    items_stats["services_amount"] += float(item.total_amount)
                elif item.product_id:
                    items_stats["products_count"] += 1
                    items_stats["products_amount"] += float(item.total_amount)

    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_sales": total_sales,
            "invoices_count": len(invoices),
            **items_stats,
        },
        "sales": [
            {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "patient": (
                    {
                        "id": invoice.patient.id,
                        "name": f"{invoice.patient.first_name} {invoice.patient.last_name}",
                        "email": invoice.patient.email,
                    }
                    if invoice.patient
                    else None
                ),
                "created_by": (
                    f"{invoice.created_by.first_name} {invoice.created_by.last_name}"
                    if invoice.created_by
                    else None
                ),
                "status": invoice.status,
                "total_amount": float(invoice.total_amount),
                "currency": invoice.currency,
                "items": [
                    {
                        "id": item.id,
                        "type": "service" if item.service_id else "product",
                        "name": item.service.name if item.service else (item.product.name if item.product else None),
                        "description": item.description,
                        "quantity": float(item.quantity),
                        "unit_price": float(item.unit_price),
                        "total_amount": float(item.total_amount),
                    }
                    for item in invoice.items
                ]
                if invoice.items
                else [],
            }
            for invoice in invoices
        ],
    }


@router.get("/patients-per-specialty")
async def get_patients_per_specialty(
    start_date: date = Query(...),
    end_date: date = Query(...),
    specialty_id: Optional[int] = Query(None),
    area_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Pacientes atendidos por especialidad (área)
    Obtiene estadísticas de pacientes atendidos agrupados por especialidad y área
    """
    # Obtener citas completadas en el período
    query = select(Appointment).filter(
        Appointment.start_datetime.between(start_date, end_date),
        Appointment.status == "COMPLETED",
    )

    if specialty_id:
        query = query.filter(Appointment.specialty_id == specialty_id)

    appointments_result = await db.execute(query)
    appointments = appointments_result.scalars().unique().all()

    # Filtrar por área si se especifica
    if area_id:
        appointments = [
            app
            for app in appointments
            if app.professional and app.professional.area_id == area_id
        ]

    # Agrupar por especialidad
    by_specialty = defaultdict(
        lambda: {
            "specialty": "",
            "area": "",
            "appointments_count": 0,
            "unique_patients": set(),
        }
    )

    for appointment in appointments:
        specialty_name = (
            appointment.specialty.name if appointment.specialty else "Sin especialidad"
        )
        area_name = (
            appointment.professional.area.name
            if appointment.professional and appointment.professional.area
            else "Sin área"
        )

        by_specialty[specialty_name]["specialty"] = specialty_name
        by_specialty[specialty_name]["area"] = area_name
        by_specialty[specialty_name]["appointments_count"] += 1
        by_specialty[specialty_name]["unique_patients"].add(appointment.patient_id)

    # Convertir a lista y calcular promedios
    specialty_stats = []
    for stat in by_specialty.values():
        unique_count = len(stat["unique_patients"])
        specialty_stats.append(
            {
                "specialty": stat["specialty"],
                "area": stat["area"],
                "appointments_count": stat["appointments_count"],
                "unique_patients_count": unique_count,
                "avg_appointments_per_patient": (
                    round(stat["appointments_count"] / unique_count, 2)
                    if unique_count > 0
                    else 0
                ),
            }
        )

    # Ordenar por número de citas
    specialty_stats.sort(key=lambda x: x["appointments_count"], reverse=True)

    # Calcular total de pacientes únicos
    total_unique_patients = len(set(app.patient_id for app in appointments))

    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_appointments": len(appointments),
            "total_unique_patients": total_unique_patients,
            "specialties_count": len(specialty_stats),
        },
        "by_specialty": specialty_stats,
    }
