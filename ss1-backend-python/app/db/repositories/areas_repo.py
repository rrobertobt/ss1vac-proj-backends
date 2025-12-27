from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.db.models import Area, Employee
from app.api.routes.areas_schemas import AreaCreate, AreaUpdate
from typing import List, Optional


class AreasRepository:
    @staticmethod
    async def create(db: AsyncSession, area_data: AreaCreate) -> Area:
        """Crear una nueva área"""
        area = Area(name=area_data.name, description=area_data.description)
        db.add(area)
        try:
            await db.commit()
            await db.refresh(area)
            return area
        except IntegrityError:
            await db.rollback()
            raise ValueError("Ya existe un área con ese nombre")

    @staticmethod
    async def get_all(db: AsyncSession) -> List[Area]:
        """Obtener todas las áreas"""
        result = await db.execute(select(Area).order_by(Area.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, area_id: int) -> Optional[Area]:
        """Obtener un área por ID"""
        result = await db.execute(select(Area).where(Area.id == area_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Area]:
        """Obtener un área por nombre (case-insensitive)"""
        result = await db.execute(
            select(Area).where(Area.name.ilike(name))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, area_id: int, area_data: AreaUpdate
    ) -> Optional[Area]:
        """Actualizar un área"""
        area = await AreasRepository.get_by_id(db, area_id)
        if not area:
            return None

        if area_data.name is not None:
            area.name = area_data.name
        if area_data.description is not None:
            area.description = area_data.description

        try:
            await db.commit()
            await db.refresh(area)
            return area
        except IntegrityError:
            await db.rollback()
            raise ValueError("Ya existe un área con ese nombre")

    @staticmethod
    async def delete(db: AsyncSession, area_id: int) -> bool:
        """
        Eliminar un área.
        Verifica que no haya empleados ni servicios asociados.
        """
        area = await AreasRepository.get_by_id(db, area_id)
        if not area:
            return False

        # Verificar si hay empleados asociados
        employees_result = await db.execute(
            select(func.count()).select_from(Employee).where(Employee.area_id == area_id)
        )
        employees_count = employees_result.scalar()

        if employees_count > 0:
            raise ValueError(
                f"No se puede eliminar el área porque tiene {employees_count} empleado(s) asociado(s)"
            )

        # Verificar si hay servicios asociados
        from app.db.models import Service
        services_result = await db.execute(
            select(func.count()).select_from(Service).where(Service.area_id == area_id)
        )
        services_count = services_result.scalar()

        if services_count > 0:
            raise ValueError(
                f"No se puede eliminar el área porque tiene {services_count} servicio(s) asociado(s)"
            )

        await db.delete(area)
        await db.commit()
        return True
