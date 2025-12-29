from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.roles import router as roles_router
from app.api.routes.permissions import router as permissions_router
from app.api.routes.employees import router as employees_router
from app.api.routes.patients import router as patients_router
from app.api.routes.areas import router as areas_router
from app.api.routes.specialties import router as specialties_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PsiFirm API (Python)")

# Manejador de HTTPException para formato consistente
@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "statusCode": exc.status_code,
        },
    )

# Manejador de errores de validación (formato compatible con NestJS)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        # Obtener el nombre del campo
        field = ".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else "body"
        
        # Si hay un mensaje personalizado del @field_validator, usarlo directamente
        if error["type"] == "value_error" and "ctx" in error:
            ctx_error = error.get("ctx", {}).get("error")
            if ctx_error:
                error_messages.append(str(ctx_error))
                continue
        
        # Construir mensaje con formato: "field: mensaje"
        msg = error["msg"]
        
        # Agregar contexto adicional si está disponible
        if "ctx" in error:
            ctx = error["ctx"]
            if "min_length" in ctx:
                msg = f"{field} must have at least {ctx['min_length']} characters"
            elif "max_length" in ctx:
                msg = f"{field} must have at most {ctx['max_length']} characters"
            elif "gt" in ctx:
                msg = f"{field} must be greater than {ctx['gt']}"
            elif "ge" in ctx:
                msg = f"{field} must be greater than or equal to {ctx['ge']}"
            elif "lt" in ctx:
                msg = f"{field} must be less than {ctx['lt']}"
            elif "le" in ctx:
                msg = f"{field} must be less than or equal to {ctx['le']}"
            elif "expected" in ctx:
                msg = f"{field} must be one of the allowed values"
        
        # Formato: "field: message"
        if field and field != "body":
            error_messages.append(f"{field}: {msg}")
        else:
            error_messages.append(msg)
    
    return JSONResponse(
        status_code=400,
        content={
            "message": error_messages if error_messages else ["Validation error"],
            "error": "Bad Request",
            "statusCode": 400,
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(permissions_router)
app.include_router(employees_router)
app.include_router(patients_router)
app.include_router(areas_router)
app.include_router(specialties_router)

