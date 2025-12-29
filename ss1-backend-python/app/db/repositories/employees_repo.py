from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import joinedload
from app.db.models import Employee, User
import math


class EmployeesRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, employee_data: dict):
        employee = Employee(**employee_data)
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def get_all(
        self,
        page: int = 1,
        limit: int = 10,
        area_id: int | None = None,
        status: str | None = None,
        role_id: int | None = None,
        search: str | None = None,
    ):
        offset = (page - 1) * limit

        # Base query
        query = (
            select(Employee)
            .options(joinedload(Employee.user).joinedload(User.role))
            .order_by(Employee.created_at.desc())
        )

        # Join con users si necesitamos filtrar por role_id
        if role_id is not None:
            query = query.join(Employee.user).where(User.role_id == role_id)

        # Aplicar filtros
        if area_id is not None:
            query = query.where(Employee.area_id == area_id)

        if status is not None:
            query = query.where(Employee.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Employee.first_name.ilike(search_pattern),
                    Employee.last_name.ilike(search_pattern),
                    Employee.license_number.ilike(search_pattern),
                )
            )

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Aplicar paginación
        query = query.limit(limit).offset(offset)

        # Ejecutar query
        result = await self.db.execute(query)
        employees = list(result.scalars().unique().all())

        return {
            "data": employees,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": math.ceil(total / limit) if total > 0 else 0,
            },
        }

    async def find_by_id(self, employee_id: int):
        result = await self.db.execute(
            select(Employee)
            .options(
                joinedload(Employee.user).joinedload(User.role),
                joinedload(Employee.area),
                joinedload(Employee.specialties),
                joinedload(Employee.availability)
            )
            .where(Employee.id == employee_id)
        )
        return result.scalars().unique().one_or_none()

    async def update(self, employee_id: int, employee_data: dict):
        result = await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if not employee:
            return None

        for key, value in employee_data.items():
            setattr(employee, key, value)

        await self.db.commit()
        await self.db.refresh(employee)
        return employee
