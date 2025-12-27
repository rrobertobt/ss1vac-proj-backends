# Convenciones de Nomenclatura - Backend Python

## Regla General: snake_case en TODO

Para mantener consistencia con el backend de Node.js y la base de datos PostgreSQL, **SIEMPRE** usar `snake_case` en:

### 1. Modelos SQLAlchemy
```python
class User(Base):
    __tablename__ = "users"
    
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role_id: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean)
```

### 2. Schemas Pydantic
```python
class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role_id: int
    is_active: Optional[bool] = True
    
    class Config:
        from_attributes = True  # NO usar alias_generator
```

### 3. Request Bodies
```python
class LoginBody(BaseModel):
    email_or_username: str  # ❌ NO emailOrUsername
    password: str

class UpdateUserBody(BaseModel):
    first_name: Optional[str] = None  # ❌ NO firstName
    last_name: Optional[str] = None   # ❌ NO lastName
```

### 4. Response JSON
```python
@router.get("/users/{id}")
async def get_user(id: int):
    return {
        "id": user.id,
        "first_name": user.first_name,  # ❌ NO "firstName"
        "last_name": user.last_name,    # ❌ NO "lastName"
        "role_id": user.role_id,        # ❌ NO "roleId"
        "is_active": user.is_active,    # ❌ NO "isActive"
    }
```

### 5. Parámetros de Funciones
```python
async def create_user(
    first_name: str,     # ❌ NO firstName
    last_name: str,      # ❌ NO lastName
    email: str,
    role_id: int         # ❌ NO roleId
):
    pass
```

### 6. Variables y Nombres de Campos
```python
# Variables locales
user_email = user.email           # ❌ NO userEmail
role_name = user.role.name        # ❌ NO roleName
two_fa_enabled = user.two_fa_enabled  # ❌ NO twoFaEnabled

# Diccionarios
user_data = {
    "first_name": "John",         # ❌ NO "firstName"
    "email": "john@example.com",
    "is_active": True             # ❌ NO "isActive"
}
```

## Razón de esta Convención

1. **Consistencia con PostgreSQL**: La base de datos usa `snake_case`
2. **Compatibilidad con Node.js**: El backend Node también devuelve `snake_case`
3. **Estándar Python**: PEP 8 recomienda `snake_case` para variables y funciones
4. **Simplicidad**: Evita conversiones innecesarias entre camelCase y snake_case

## Checklist para Nuevas Implementaciones

- [ ] Modelos SQLAlchemy usan `snake_case`
- [ ] Schemas Pydantic usan `snake_case`
- [ ] Request bodies usan `snake_case`
- [ ] Response JSON usa `snake_case`
- [ ] Variables y parámetros usan `snake_case`
- [ ] NO hay `alias_generator` en Config de Pydantic
- [ ] NO hay conversiones manuales a camelCase en el código

## Ejemplo Completo Correcto

```python
# Schema
class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    employee_type: str
    license_number: Optional[str] = None
    
    class Config:
        from_attributes = True

# Endpoint
@router.post("/employees", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db)
):
    # Usar directamente sin conversión
    employee = await employees_repo.create(employee_data.model_dump())
    
    # Respuesta automática en snake_case
    return employee
```

## ❌ Anti-patrones a Evitar

```python
# MAL: Conversión manual a camelCase
return {
    "firstName": user.first_name,  # ❌
    "lastName": user.last_name,    # ❌
    "roleId": user.role_id         # ❌
}

# MAL: alias_generator
class UserSchema(BaseModel):
    first_name: str
    
    class Config:
        alias_generator = to_camel  # ❌ NUNCA hacer esto

# MAL: Field con alias
class UserSchema(BaseModel):
    first_name: str = Field(alias="firstName")  # ❌
```

## Herramientas de Verificación

Buscar patrones problemáticos:
```bash
# Buscar camelCase en responses
grep -r "firstName\|lastName\|roleId\|isActive" app/

# Buscar alias_generator
grep -r "alias_generator" app/
```
