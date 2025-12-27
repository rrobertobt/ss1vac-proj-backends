from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Employee


class EmployeesRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, employee_data: dict):
        employee = Employee(**employee_data)
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def find_by_id(self, employee_id: int):
        result = await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()
