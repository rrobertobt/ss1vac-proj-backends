from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.db.models import Specialty
from app.api.routes.specialties_schemas import SpecialtyCreate, SpecialtyUpdate
from typing import List, Optional


class SpecialtiesRepository:
    @staticmethod
    async def create(db: AsyncSession, specialty_data: SpecialtyCreate) -> Specialty:
        """Crear una nueva especialidad"""
        specialty = Specialty(
            name=specialty_data.name, description=specialty_data.description
        )
        db.add(specialty)
        try:
            await db.commit()
            await db.refresh(specialty)
            return specialty
        except IntegrityError:
            await db.rollback()
            raise ValueError("Ya existe una especialidad con ese nombre")

    @staticmethod
    async def get_all(db: AsyncSession) -> List[Specialty]:
        """Obtener todas las especialidades"""
        result = await db.execute(select(Specialty).order_by(Specialty.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, specialty_id: int) -> Optional[Specialty]:
        """Obtener una especialidad por ID"""
        result = await db.execute(
            select(Specialty).where(Specialty.id == specialty_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Specialty]:
        """Obtener una especialidad por nombre (case-insensitive)"""
        result = await db.execute(select(Specialty).where(Specialty.name.ilike(name)))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, specialty_id: int, specialty_data: SpecialtyUpdate
    ) -> Optional[Specialty]:
        """Actualizar una especialidad"""
        specialty = await SpecialtiesRepository.get_by_id(db, specialty_id)
        if not specialty:
            return None

        if specialty_data.name is not None:
            specialty.name = specialty_data.name
        if specialty_data.description is not None:
            specialty.description = specialty_data.description

        try:
            await db.commit()
            await db.refresh(specialty)
            return specialty
        except IntegrityError:
            await db.rollback()
            raise ValueError("Ya existe una especialidad con ese nombre")

    @staticmethod
    async def delete(db: AsyncSession, specialty_id: int) -> bool:
        """
        Eliminar una especialidad.
        Verifica que no haya empleados asociados.
        """
        specialty = await SpecialtiesRepository.get_by_id(db, specialty_id)
        if not specialty:
            return False

        # Verificar si hay empleados asociados a través de employee_specialties
        from app.db.models import employee_specialties
        employees_result = await db.execute(
            select(func.count())
            .select_from(employee_specialties)
            .where(employee_specialties.c.specialty_id == specialty_id)
        )
        employees_count = employees_result.scalar()

        if employees_count > 0:
            raise ValueError(
                f"No se puede eliminar la especialidad porque tiene {employees_count} empleado(s) asociado(s)"
            )

        await db.delete(specialty)
        await db.commit()
        return True
