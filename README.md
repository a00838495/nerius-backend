# Nerius Backend — Super Admin Module

Módulo de Super Admin para el backend de Nerius. Agrega 20 endpoints nuevos bajo
`/api/v1/superadmin/*` y un middleware de métricas de requests.

## ✨ Funcionalidades

### 1. Dashboard de Salud del Sistema
- `GET /superadmin/health/system` — CPU, memoria, disco, proceso (usa `psutil`)
- `GET /superadmin/health/database` — latencia DB, tamaño, top tablas
- `GET /superadmin/health/summary` — resumen consolidado para el dashboard

### 2. Monitoreo de Sesiones
- `GET /superadmin/sessions` — lista paginada con filtros
- `GET /superadmin/sessions/stats` — estadísticas (activas, últimas 24h, por día)
- `GET /superadmin/sessions/suspicious` — usuarios con sesiones desde múltiples IPs
- `DELETE /superadmin/sessions/{target_session_id}` — forzar logout
- `DELETE /superadmin/sessions/user/{user_id}` — logout de todas las sesiones de un usuario
- `POST /superadmin/sessions/cleanup` — limpiar expiradas

### 3. Métricas Técnicas
- `GET /superadmin/metrics/requests` — top y slowest endpoints
- `GET /superadmin/metrics/errors` — errores 4xx/5xx por endpoint
- `GET /superadmin/metrics/active-users` — usuarios activos por hora/día
- `GET /superadmin/metrics/database` — row count por tabla

### 4. Auditoría
- `GET /superadmin/audit-logs` — lista paginada con filtros
- `GET /superadmin/audit-logs/{log_id}` — detalle
- `GET /superadmin/audit-logs/actions` — catálogo de acciones disponibles
- `GET /superadmin/audit-logs/export` — export CSV

### 5. Actividad de Admins
- `GET /superadmin/admins/activity` — overview de todos los admins
- `GET /superadmin/admins/{user_id}/history` — historial de cambios de rol
- `GET /superadmin/admins/{user_id}/actions` — acciones recientes

---

## 📦 Archivos

### Nuevos
```
src/api/routes/superadmin.py                              ← 20 endpoints
src/core/audit.py                                         ← helper para audit logs
src/core/metrics.py                                       ← middleware de métricas
src/db/models/audit.py                                    ← modelos AuditLog y RequestMetric
src/schemas/superadmin.py                                 ← Pydantic schemas
alembic/versions/a7b3c9d2e1f4_add_audit_logs_and_request_metrics.py
```

### Modificados
```
src/main.py                       ← registra el middleware
src/api/router.py                 ← registra el router superadmin
src/db/models/__init__.py         ← exporta AuditLog y RequestMetric
src/api/routes/auth.py            ← audit logs en login/logout
src/api/routes/admin.py           ← audit logs en cambios de rol y CRUD de cursos
requirements.txt                  ← + psutil
```

---

## 🚀 Instalación

1. **Copia los archivos a tu proyecto** respetando la estructura.

2. **Instala la nueva dependencia:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Aplica la migración:**
   ```bash
   alembic upgrade head
   ```

4. **(Si no usas Alembic)** las nuevas tablas se crearán automáticamente con
   `Base.metadata.create_all()` si lo tienes en tu setup.

5. **Reinicia el servidor:**
   ```bash
   uvicorn src.main:app --reload
   ```

6. **Verifica en Scalar:** `http://localhost:8000/scalar` — deberías ver la nueva
   sección `superadmin` con los 20 endpoints.

---

## 🧪 Probar manualmente

```bash
# 1. Login como super admin
curl -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "superadmin@example.com", "password": "password123"}'

# 2. Health summary
curl -b cookies.txt http://localhost:8000/api/v1/superadmin/health/summary | jq

# 3. Listar sesiones activas
curl -b cookies.txt http://localhost:8000/api/v1/superadmin/sessions | jq

# 4. Ver audit logs
curl -b cookies.txt http://localhost:8000/api/v1/superadmin/audit-logs | jq
```

---

## 🔐 Permisos

Todos los endpoints usan `require_super_admin`. Solo usuarios con rol
`super_admin` pueden acceder. Cualquier otro rol recibe 403.

---

## 📊 Acciones de auditoría registradas automáticamente

| Acción | Cuándo se registra |
|---|---|
| `auth.login` | Login exitoso |
| `auth.login_failed` | Login con credenciales inválidas |
| `auth.logout` | Logout |
| `user.role_changed` | Super admin cambia rol de un usuario |
| `course.created` | Admin crea un curso |
| `course.updated` | Admin actualiza un curso |
| `course.published` | Curso pasa a estado published |
| `course.archived` | Curso pasa a estado archived |
| `course.deleted` | Soft-delete de un curso |
| `session.revoked` | Super admin revoca una sesión |
| `session.revoked_all` | Super admin revoca todas las sesiones de un usuario |
| `session.cleanup` | Limpieza de sesiones expiradas |

Para registrar tus propios eventos desde otros endpoints:

```python
from src.core.audit import AuditAction, log_action

log_action(
    db,
    AuditAction.CERT_APPROVED,  # o cualquier string custom
    user_id=current_user.id,
    resource_type="certification",
    resource_id=cert_id,
    description=f"Certificación aprobada para {target_user.email}",
    extra_data={"target_user_id": target_user.id},
    request=request,  # FastAPI Request, opcional — extrae IP y user-agent
)
```

---

## ⚙️ Notas técnicas

- **`request_metrics` puede crecer rápido.** El middleware no inserta para paths
  en `SKIP_PATH_PREFIXES` (`/health`, `/docs`, `/scalar`, etc.). Se recomienda
  agregar un cron / job programado para limpiar registros viejos:
  ```sql
  DELETE FROM request_metrics WHERE created_at < NOW() - INTERVAL 30 DAY;
  ```
- **`psutil`** funciona en Linux/macOS/Windows. En contenedores reporta el
  uso del proceso, no del host.
- El middleware usa una **sesión de DB independiente** para escribir métricas,
  así nunca interfiere con la sesión del request.
- Las escrituras a `audit_logs` y `request_metrics` son **fail-safe**: si
  falla la escritura, el request original no se ve afectado.

---

## 🐛 Issue conocido

El path param `session_id` colisiona con el `Cookie("session_id")` del
sistema de auth (mismo issue documentado en `FRONTEND_INTEGRATION.md`). Por
eso el endpoint usa `target_session_id` en la URL:

```
DELETE /superadmin/sessions/{target_session_id}
```

---

Hecho con ❤️ para la plataforma Nerius.
