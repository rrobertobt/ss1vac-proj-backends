from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.routes.auth import router as auth_router
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

# Manejador de errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Construir un mensaje más legible
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"][1:])
        error_messages.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=400,
        content={
            "message": "; ".join(error_messages) if error_messages else "Error de validación",
            "statusCode": 400,
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta esto según tus necesidades
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
