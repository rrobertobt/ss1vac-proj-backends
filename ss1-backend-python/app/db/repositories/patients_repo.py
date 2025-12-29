from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.models import Patient
from typing import Optional


class PatientsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, patient_data: dict):
        patient = Patient(**patient_data)
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def find_by_id(self, patient_id: int):
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        return result.scalar_one_or_none()

    async def find_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ):
        query = select(Patient).order_by(Patient.created_at.desc())

        # Filtro de búsqueda
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.email.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                )
            )

        # Filtro de estado
        if status:
            query = query.where(Patient.status == status)

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginación
        offset = (page - 1) * limit
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        patients = result.scalars().all()

        return patients, total

    async def update(self, patient_id: int, patient_data: dict):
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            return None

        for key, value in patient_data.items():
            if value is not None:
                setattr(patient, key, value)

        await self.db.commit()
        await self.db.refresh(patient)
        return patient

