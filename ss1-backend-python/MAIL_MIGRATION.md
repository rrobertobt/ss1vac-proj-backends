# Migración de Amazon SES a Mailtrap

## Cambios Realizados

Se reemplazó el servicio de Amazon SES por la librería oficial de Mailtrap.

### Archivos Modificados

1. **`app/services/mail_ses.py` → `app/services/mail_mailtrap.py`**
   - Reemplazada clase `SesMailService` por `MailService`
   - Implementación usando `mailtrap` (librería oficial) en lugar de `boto3`
   - Uso de la API de Mailtrap con token de autenticación

2. **`app/core/config.py`**
   - Removidas variables de AWS y SMTP
   - Agregadas variables de Mailtrap:
     - `MAILTRAP_API_TOKEN`: Token de API de Mailtrap
     - `MAIL_FROM`: Email remitente
     - `MAIL_FROM_NAME`: Nombre del remitente (default: PsiFirm)

3. **`app/api/routes/auth.py`**
   - Actualizado import de `mail_ses` a `mail_mailtrap`
   - La clase `MailService` mantiene la misma interfaz

## Instalación

Primero, instala la librería oficial de Mailtrap:

```bash
pip install mailtrap
```

O agrega a tu `requirements.txt`:
```
mailtrap>=2.0.0
```

## Configuración

### Variables de Entorno

Actualiza tu archivo `.env` con las siguientes variables:

```env
# Mail Configuration (Mailtrap)
MAILTRAP_API_TOKEN=tu-api-token-aqui
MAIL_FROM=noreply@psifirm.com
MAIL_FROM_NAME=PsiFirm
```

### Obtener el API Token de Mailtrap

1. Crea una cuenta en [Mailtrap.io](https://mailtrap.io)
2. Ve a tu inbox de Email Testing
3. En la sección de integración, busca "API" 
4. Copia tu API Token
5. Pégalo en la variable `MAILTRAP_API_TOKEN`

**Nota:** El API Token es diferente de las credenciales SMTP. Es más seguro y fácil de usar.

## Características

- ✅ Librería oficial de Mailtrap
- ✅ Autenticación con API Token (más seguro)
- ✅ Sin configuración de SMTP
- ✅ Soporte nativo para categorías de email
- ✅ Compatible con la API existente
- ✅ No requiere dependencias de AWS

## Testing

Para probar el envío de emails:

1. Instala la librería: `pip install mailtrap`
2. Configura `MAILTRAP_API_TOKEN` en `.env`
3. Ejecuta el servidor: `uvicorn app.main:app --reload`
4. Intenta hacer login con un usuario que tenga 2FA activado
5. Verifica que el email llegue a tu inbox de Mailtrap

## Comparación con SMTP

### Antes (SMTP):
```python
# Requería configurar host, puerto, usuario, contraseña
MAIL_HOST=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=usuario
MAIL_PASSWORD=password
```

### Ahora (API):
```python
# Solo requiere un API token
MAILTRAP_API_TOKEN=tu-token
```

## Ventajas de la API vs SMTP

1. **Más simple**: Solo necesitas un token
2. **Más seguro**: No expones credenciales SMTP
3. **Mejor integración**: Librería oficial con soporte completo
4. **Más características**: Acceso a todas las funciones de Mailtrap
5. **Mejor debugging**: Respuestas más claras de la API

## Notas

- La librería `mailtrap` usa la API REST de Mailtrap
- El método `send_text_email()` mantiene la misma firma, por lo que no hay cambios en `auth_service.py`
- Los emails se categorizan automáticamente como "2FA" para mejor organización
- La respuesta del envío incluye información útil para debugging
