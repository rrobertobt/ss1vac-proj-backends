# Configuración de Validaciones

Este documento explica cómo están configuradas las validaciones en ambos backends y el formato de respuesta de errores.

## Backend Node.js (NestJS)

### Configuración Global

En `src/main.ts`, se configura el `ValidationPipe` globalmente:

```typescript
import { ValidationPipe } from '@nestjs/common';

app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,              // Remueve propiedades no definidas en el DTO
    forbidNonWhitelisted: true,   // Lanza error si hay propiedades extra
    transform: true,              // Transforma los payloads a las instancias del DTO
    transformOptions: {
      enableImplicitConversion: true, // Convierte tipos automáticamente
    },
  }),
);
```

### Decoradores de Validación

Se utilizan decoradores de `class-validator` en los DTOs:

```typescript
import { IsEmail, IsNotEmpty, MinLength, MaxLength, Min, Max, IsIn } from 'class-validator';

export class CreateEmployeeDto {
  @IsEmail({}, { message: 'El email debe ser válido' })
  @IsNotEmpty({ message: 'El email es obligatorio' })
  email: string;

  @IsString({ message: 'El nombre debe ser un texto' })
  @MinLength(2, { message: 'El nombre debe tener al menos 2 caracteres' })
  @MaxLength(100, { message: 'El nombre no puede exceder 100 caracteres' })
  @IsNotEmpty({ message: 'El nombre es obligatorio' })
  first_name: string;

  @IsNumber({}, { message: 'El salario base debe ser un número' })
  @Min(0, { message: 'El salario base no puede ser negativo' })
  @Max(999999999.99, { message: 'El salario base excede el límite permitido' })
  @IsOptional()
  base_salary?: number;

  @IsString({ message: 'El tipo de empleado debe ser un texto' })
  @IsIn(['PSYCHOLOGIST', 'PSYCHIATRIST', 'TECHNICIAN', 'MAINTENANCE', 'ADMIN_STAFF'], {
    message: 'El tipo de empleado debe ser uno de: PSYCHOLOGIST, PSYCHIATRIST, TECHNICIAN, MAINTENANCE, ADMIN_STAFF',
  })
  @IsNotEmpty({ message: 'El tipo de empleado es obligatorio' })
  employee_type: string;
}
```

### Formato de Respuesta de Errores

Cuando hay errores de validación, NestJS devuelve:

```json
{
  "message": [
    "El email es obligatorio",
    "El email debe ser válido",
    "El nombre debe tener al menos 2 caracteres"
  ],
  "error": "Bad Request",
  "statusCode": 400
}
```

## Backend Python (FastAPI)

### Configuración de Exception Handlers

En `app/main.py`, se configura un exception handler personalizado para `RequestValidationError`:

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Construir mensajes individuales como en NestJS
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"][1:])
        msg = error["msg"]
        
        # Si hay un mensaje personalizado del validator, usarlo
        if "ctx" in error and "error" in error["ctx"]:
            msg = str(error["ctx"]["error"])
        
        # Formatear mensaje con el campo
        if field:
            error_messages.append(f"{msg}")
        else:
            error_messages.append(msg)
    
    return JSONResponse(
        status_code=400,
        content={
            "message": error_messages if error_messages else ["Error de validación"],
            "error": "Bad Request",
            "statusCode": 400,
        },
    )
```

### Validaciones con Pydantic

Se utilizan `Field()` y `field_validator` en los schemas:

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
import re

class EmployeeCreate(BaseModel):
    email: EmailStr = Field(..., description="Email del empleado")
    
    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Nombre de usuario"
    )
    
    role_id: int = Field(..., gt=0, description="ID del rol")
    
    first_name: str = Field(
        ..., min_length=2, max_length=100, description="Nombre del empleado"
    )
    
    base_salary: Optional[float] = Field(
        0, ge=0, le=999999999.99, description="Salario base"
    )
    
    igss_percentage: Optional[float] = Field(
        0, ge=0, le=100, description="Porcentaje IGSS (0-100)"
    )
    
    employee_type: Literal[
        "PSYCHOLOGIST", "PSYCHIATRIST", "TECHNICIAN", "MAINTENANCE", "ADMIN_STAFF"
    ] = Field(..., description="Tipo de empleado")
    
    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()
    
    @field_validator("phone", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        phone_pattern = r"^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$"
        if not re.match(phone_pattern, v):
            raise ValueError("El teléfono debe tener un formato válido")
        return v
```

### Formato de Respuesta de Errores

Después de la configuración, FastAPI devuelve el mismo formato que NestJS:

```json
{
  "message": [
    "Field required",
    "El email debe ser válido",
    "El nombre debe tener al menos 2 caracteres"
  ],
  "error": "Bad Request",
  "statusCode": 400
}
```

## Tipos de Validaciones Implementadas

### Ambos Backends

| Validación | Node.js (class-validator) | Python (Pydantic) | Descripción |
|-----------|---------------------------|-------------------|-------------|
| Email | `@IsEmail()` | `EmailStr` | Valida formato de email |
| Requerido | `@IsNotEmpty()` | `Field(...)` | Campo obligatorio |
| Longitud mínima | `@MinLength(n)` | `Field(min_length=n)` | Mínimo de caracteres |
| Longitud máxima | `@MaxLength(n)` | `Field(max_length=n)` | Máximo de caracteres |
| Valor mínimo | `@Min(n)` | `Field(ge=n)` o `Field(gt=n)` | Mayor o igual / Mayor que |
| Valor máximo | `@Max(n)` | `Field(le=n)` | Menor o igual que |
| Enums | `@IsIn([...])` | `Literal[...]` | Valores permitidos |
| Opcional | `@IsOptional()` | `Optional[T]` | Campo opcional |
| Regex | `@Matches(pattern)` | `field_validator` con `re.match()` | Patrón personalizado |
| Fechas | `@IsDateString()` | `date` type | Validación de fechas |

### Validaciones Personalizadas

**Node.js:**
```typescript
// No hay custom validators en los DTOs actuales, pero se pueden agregar con:
@Validate(CustomValidator)
```

**Python:**
```python
@field_validator("hired_at")
@classmethod
def validate_hired_date(cls, v: Optional[date]) -> Optional[date]:
    if v and v > date.today():
        raise ValueError("La fecha de contratación no puede ser futura")
    return v
```

## Mensajes de Error en Español

Todos los mensajes de validación están en español para mejor experiencia de usuario:

- ✅ "El email es obligatorio"
- ✅ "El nombre debe tener al menos 2 caracteres"
- ✅ "El salario base no puede ser negativo"
- ✅ "El porcentaje IGSS no puede exceder 100%"
- ✅ "El teléfono debe tener un formato válido"

## Beneficios de esta Configuración

1. **Validación Automática**: Los datos se validan antes de llegar a los servicios
2. **Respuestas Consistentes**: Mismo formato de error en ambos backends
3. **Mensajes Claros**: Errores descriptivos en español
4. **Type Safety**: TypeScript/Pydantic garantizan tipos correctos
5. **Seguridad**: `whitelist` y `forbidNonWhitelisted` previenen propiedades maliciosas
6. **Transformación**: Conversión automática de tipos (strings a números, etc.)

## Archivos Modificados

### Node.js
- `src/main.ts`: Configuración global del ValidationPipe
- `src/modules/employees/dto/create-employee.dto.ts`
- `src/modules/patients/dto/create-patient.dto.ts`
- `src/modules/users/dto/create-user.dto.ts`
- `src/modules/users/dto/update-user.dto.ts`

### Python
- `app/main.py`: Exception handler para RequestValidationError
- `app/api/routes/employees_schemas.py`
- `app/api/routes/patients_schemas.py`
- `app/api/routes/users_schemas.py`

## Pruebas de Validación

Para probar las validaciones:

```bash
# Enviar body vacío
curl -X POST http://localhost:3001/employees \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{}'

# Enviar datos inválidos
curl -X POST http://localhost:3001/employees \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "email": "invalid-email",
    "first_name": "A",
    "base_salary": -100,
    "igss_percentage": 150,
    "employee_type": "INVALID_TYPE"
  }'
```

Ambas requests devolverán errores 400 con mensajes descriptivos.
