from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text
from app.db.models import Appointment, EmployeeAvailability, Employee, Specialty
from datetime import datetime, date, time, timedelta, timezone
from typing import Optional
import math


class AppointmentsRepository:
    """Repositorio para operaciones de citas"""

    @staticmethod
    async def check_availability(
        db: AsyncSession,
        target_date: date,
        specialty_id: Optional[int] = None,
        professional_id: Optional[int] = None,
    ):
        """
        Verificar disponibilidad de citas en una fecha específica
        """
        # Obtener día de la semana (0=Domingo, 6=Sábado)
        day_of_week = target_date.weekday()
        # Python usa 0=Lunes, ajustar a 0=Domingo
        day_of_week = (day_of_week + 1) % 7

        # Query base para disponibilidades
        query = (
            select(EmployeeAvailability)
            .where(EmployeeAvailability.day_of_week == day_of_week)
            .where(EmployeeAvailability.is_active == True)
        )

        # Filtros opcionales
        if specialty_id:
            query = query.where(EmployeeAvailability.specialty_id == specialty_id)
        
        if professional_id:
            query = query.where(EmployeeAvailability.employee_id == professional_id)

        result = await db.execute(query)
        availabilities = result.unique().scalars().all()

        # Para cada disponibilidad, generar slots
        all_slots = []
        
        for avail in availabilities:
            # Obtener citas existentes del profesional en esa fecha
            start_of_day = datetime.combine(target_date, time.min)
            end_of_day = datetime.combine(target_date, time.max)
            
            existing_query = (
                select(Appointment)
                .where(Appointment.professional_id == avail.employee_id)
                .where(Appointment.start_datetime >= start_of_day)
                .where(Appointment.start_datetime <= end_of_day)
                .where(Appointment.status.in_(["SCHEDULED", "COMPLETED"]))
            )
            
            existing_result = await db.execute(existing_query)
            existing_appointments = existing_result.unique().scalars().all()
            
            # Generar slots disponibles
            slots = AppointmentsRepository._generate_time_slots(
                avail.start_time,
                avail.end_time,
                existing_appointments,
                target_date,
            )
            
            all_slots.append({
                "employee_id": avail.employee_id,
                "employee_name": f"{avail.employee.first_name} {avail.employee.last_name}" if avail.employee else "N/A",
                "specialty_id": avail.specialty_id,
                "specialty_name": avail.specialty.name if avail.specialty else None,
                "available_slots": slots,
            })

        return {
            "date": target_date.isoformat(),
            "day_of_week": day_of_week,
            "professionals": all_slots,
        }

    @staticmethod
    def _generate_time_slots(
        start_time: time,
        end_time: time,
        existing_appointments: list[Appointment],
        target_date: date,
    ) -> list[dict]:
        """Generar slots de 1 hora"""
        slots = []
        
        tzinfo = existing_appointments[0].start_datetime.tzinfo if existing_appointments else timezone.utc
        current_datetime = datetime.combine(target_date, start_time).replace(tzinfo=tzinfo)
        end_datetime = datetime.combine(target_date, end_time).replace(tzinfo=tzinfo)
        
        while current_datetime < end_datetime:
            slot_end = current_datetime + timedelta(hours=1)
            
            if slot_end > end_datetime:
                break
            
            # Verificar conflictos
            has_conflict = False
            for appt in existing_appointments:
                if (current_datetime < appt.end_datetime and 
                    slot_end > appt.start_datetime):
                    has_conflict = True
                    break
            
            if not has_conflict:
                slots.append({
                    "start": current_datetime.isoformat(),
                    "end": slot_end.isoformat(),
                    "available": True,
                })
            
            current_datetime = slot_end
        
        return slots

    @staticmethod
    async def create(db: AsyncSession, appointment_data: dict) -> Appointment:
        """Crear una nueva cita"""
        # Validar fechas
        start = datetime.fromisoformat(appointment_data["start_datetime"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(appointment_data["end_datetime"].replace('Z', '+00:00'))
        
        if end <= start:
            raise ValueError("end_datetime debe ser posterior a start_datetime")
        
        # Verificar conflictos si hay profesional asignado
        if appointment_data.get("professional_id"):
            conflicts_query = (
                select(Appointment)
                .where(Appointment.professional_id == appointment_data["professional_id"])
                .where(Appointment.start_datetime < end)
                .where(Appointment.end_datetime > start)
                .where(Appointment.status.in_(["SCHEDULED", "COMPLETED"]))
            )
            
            result = await db.execute(conflicts_query)
            conflicts = result.scalars().all()
            
            if conflicts:
                raise ValueError("El profesional ya tiene una cita agendada en ese horario")
        
        # Crear cita
        new_appointment = Appointment(
            patient_id=appointment_data["patient_id"],
            professional_id=appointment_data.get("professional_id"),
            specialty_id=appointment_data.get("specialty_id"),
            appointment_type=appointment_data.get("appointment_type"),
            start_datetime=start,
            end_datetime=end,
            status="SCHEDULED",
            notes=appointment_data.get("notes"),
        
        )
        
        db.add(new_appointment)
        await db.commit()
        await db.refresh(new_appointment)
        
        return new_appointment

    @staticmethod
    async def find_all(
        db: AsyncSession,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        professional_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ):
        """Listar citas con filtros y paginación"""
        query = select(Appointment)
        
        # Filtros
        if from_date:
            start_dt = datetime.fromisoformat(from_date)
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.where(Appointment.start_datetime >= start_dt)
        
        if to_date:
            end_dt = datetime.fromisoformat(to_date)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.where(Appointment.start_datetime <= end_dt)
        
        if professional_id:
            query = query.where(Appointment.professional_id == professional_id)
        
        if patient_id:
            query = query.where(Appointment.patient_id == patient_id)
        
        if status:
            query = query.where(Appointment.status == status)
        
        # Orden descendente
        query = query.order_by(Appointment.start_datetime.desc())
        
        # Total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Paginación
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        appointments = result.unique().scalars().all()
        
        return {
            "data": appointments,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": math.ceil(total / limit) if total > 0 else 0,
            },
        }

    @staticmethod
    async def find_by_patient_id(db: AsyncSession, patient_id: int):
        """Obtener citas de un paciente específico"""
        query = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.start_datetime.desc())
        )
        
        result = await db.execute(query)
        return result.unique().scalars().all()

    @staticmethod
    async def find_by_professional_id(db: AsyncSession, professional_id: int):
        """Obtener citas de un profesional específico"""
        query = (
            select(Appointment)
            .where(Appointment.professional_id == professional_id)
            .order_by(Appointment.start_datetime.desc())
        )
        
        result = await db.execute(query)
        return result.unique().scalars().all()

    @staticmethod
    async def find_by_id(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
        """Obtener una cita por ID"""
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, 
        appointment_id: int, 
        update_data: dict
    ) -> Appointment:
        """Actualizar una cita"""
        appointment = await AppointmentsRepository.find_by_id(db, appointment_id)
        
        if not appointment:
            raise ValueError(f"Cita con ID {appointment_id} no encontrada")
        
        # Validar fechas si se proporcionan
        if "start_datetime" in update_data or "end_datetime" in update_data:
            start = update_data.get("start_datetime")
            end = update_data.get("end_datetime")
            
            if start:
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                start = appointment.start_datetime
            
            if end:
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:
                end = appointment.end_datetime
            
            if end <= start:
                raise ValueError("end_datetime debe ser posterior a start_datetime")
            
            # Verificar conflictos
            professional_id = update_data.get("professional_id", appointment.professional_id)
            
            if professional_id:
                conflicts_query = (
                    select(Appointment)
                    .where(Appointment.professional_id == professional_id)
                    .where(Appointment.id != appointment_id)
                    .where(Appointment.start_datetime < end)
                    .where(Appointment.end_datetime > start)
                    .where(Appointment.status.in_(["SCHEDULED", "COMPLETED"]))
                )
                
                result = await db.execute(conflicts_query)
                conflicts = result.scalars().all()
                
                if conflicts:
                    raise ValueError("El profesional ya tiene una cita agendada en ese horario")
            
            update_data["start_datetime"] = start
            update_data["end_datetime"] = end
        
        # Actualizar campos
        for key, value in update_data.items():
            if value is not None and hasattr(appointment, key):
                setattr(appointment, key, value)
        
        await db.commit()
        await db.refresh(appointment)
        
        return appointment

    @staticmethod
    async def cancel(db: AsyncSession, appointment_id: int) -> Appointment:
        """Cancelar una cita"""
        appointment = await AppointmentsRepository.find_by_id(db, appointment_id)
        
        if not appointment:
            raise ValueError(f"Cita con ID {appointment_id} no encontrada")
        
        if appointment.status == "CANCELLED":
            raise ValueError("La cita ya está cancelada")
        
        if appointment.status == "COMPLETED":
            raise ValueError("No se puede cancelar una cita completada")
        
        appointment.status = "CANCELLED"
        
        await db.commit()
        await db.refresh(appointment)
        
        return appointment

    @staticmethod
    async def complete(db: AsyncSession, appointment_id: int) -> Appointment:
        """Marcar cita como completada"""
        appointment = await AppointmentsRepository.find_by_id(db, appointment_id)
        
        if not appointment:
            raise ValueError(f"Cita con ID {appointment_id} no encontrada")
        
        if appointment.status == "CANCELLED":
            raise ValueError("No se puede completar una cita cancelada")
        
        if appointment.status == "COMPLETED":
            raise ValueError("La cita ya está marcada como completada")
        
        appointment.status = "COMPLETED"
        
        await db.commit()
        await db.refresh(appointment)
        
        return appointment
