from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Patient


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
