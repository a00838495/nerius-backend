# 📚 Nerius Learning Platform - API Documentation

## 🚀 Endpoints Implementados

### 1. **Health Check**
Verifica si el servidor está funcionando.

**Request:**
```bash
GET http://localhost:8000/api/v1/health/
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. **Login (Iniciar Sesión)**
Autenticación de usuario con email y contraseña. Retorna una cookie de sesión.

**Request:**
```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid-del-usuario",
    "email": "user@example.com",
    "first_name": "Juan",
    "last_name": "Perez",
    "status": "active"
  }
}
```

**Cookie Set:** `session_id` (HttpOnly, 7 días de expiración)

---

### 3. **Get Current User Info (Usuario Actual)**
Obtiene información del usuario actualmente autenticado.

**Request:**
```bash
GET http://localhost:8000/api/v1/auth/me
```

**Requiere:** Cookie `session_id` (se envía automáticamente en el navegador)

**Response:**
```json
{
  "id": "uuid-del-usuario",
  "email": "user@example.com",
  "first_name": "Juan",
  "last_name": "Perez",
  "status": "active"
}
```

---

### 4. **Logout (Cerrar Sesión)**
Invalida la sesión y elimina la cookie.

**Request:**
```bash
POST http://localhost:8000/api/v1/auth/logout
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

---

### 5. **Get All Published Courses (Obtener Cursos Disponibles)**
Obtiene la lista de todos los cursos publicados en la plataforma (sin requerir autenticación).

**Request:**
```bash
GET http://localhost:8000/api/v1/courses/
```

**Response:**
```json
[
  {
    "id": "uuid-curso",
    "title": "Python for Beginners",
    "description": "Learn the basics of Python programming language.",
    "status": "published",
    "estimated_minutes": 480,
    "cover_url": "https://via.placeholder.com/300x200?text=Python"
  },
  {
    "id": "uuid-curso",
    "title": "Web Development with FastAPI",
    "description": "Build modern web applications with FastAPI.",
    "status": "published",
    "estimated_minutes": 600,
    "cover_url": "https://via.placeholder.com/300x200?text=FastAPI"
  },
  ...
]
```

---

### 6. **Get User's Pending Courses (Obtener Cursos Pendientes del Usuario)**
Obtiene los cursos en los que el usuario está actualmente inscrito (con estado ACTIVE).

**Request:**
```bash
GET http://localhost:8000/api/v1/courses/user/pending
```

**Requiere:** Cookie `session_id` (usuario autenticado)

**Response:**
```json
[
  {
    "id": "uuid-enrollment",
    "course_id": "uuid-curso",
    "status": "active",
    "progress_percent": 45.0,
    "course": {
      "id": "uuid-curso",
      "title": "Python for Beginners",
      "description": "Learn the basics of Python programming language.",
      "status": "published",
      "estimated_minutes": 480,
      "cover_url": "https://via.placeholder.com/300x200?text=Python"
    }
  },
  {
    "id": "uuid-enrollment",
    "course_id": "uuid-curso",
    "status": "active",
    "progress_percent": 20.0,
    "course": {
      "id": "uuid-curso",
      "title": "Web Development with FastAPI",
      "description": "Build modern web applications with FastAPI.",
      "status": "published",
      "estimated_minutes": 600,
      "cover_url": "https://via.placeholder.com/300x200?text=FastAPI"
    }
  }
]
```

---

## 👥 Mock Users (Datos de Prueba)

| Email | Password | Rol |
|-------|----------|-----|
| superadmin@example.com | password123 | Super Admin |
| admin@example.com | password123 | Content Admin |
| user@example.com | password123 | Learner (Usuario Regular) |

---

## 📚 Mock Courses (Cursos Disponibles)

1. **Python for Beginners** - 480 minutos
2. **Web Development with FastAPI** - 600 minutos
3. **Business Management 101** - 360 minutos
4. **Database Design and SQL** - 420 minutos
5. **Leadership Skills** - 300 minutos

**El usuario "user@example.com" está inscrito en 3 cursos:**
- Python for Beginners (45% de progreso)
- Web Development with FastAPI (20% de progreso)
- Business Management 101 (0% de progreso)

---

## 🔐 Autenticación y Sesiones

- **Cookie Security:** HttpOnly (protegida contra XSS)
- **SameSite:** Lax (protegida contra CSRF)
- **Duración de Sesión:** 7 días
- **Almacenamiento:** En memoria (para producción se recomienda usar Redis)

---

## 🧪 Flujo Completo de Uso

### 1. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }' \
  -c cookies.txt
```

### 2. Get User Info (usando cookie)
```bash
curl http://localhost:8000/api/v1/auth/me \
  -b cookies.txt
```

### 3. Get All Courses
```bash
curl http://localhost:8000/api/v1/courses/
```

### 4. Get Pending Courses (requiere autenticación)
```bash
curl http://localhost:8000/api/v1/courses/user/pending \
  -b cookies.txt
```

### 5. Logout
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -b cookies.txt \
  -c cookies.txt
```

---

## ⚙️ Configuración

- **Base URL:** http://localhost:8000
- **API Version:** /api/v1/
- **CORS:** Habilitado para localhost:3000, localhost:5173, localhost:8080
- **Database:** SQLite (app.db) en desarrollo

---

## 📝 Notas Importantes para Frontend

1. **Cookies Automáticas:** Las cookies se manejan automáticamente en el navegador
2. **CORS:** Ya está configurado para acepta credenciales desde el frontend
3. **Session Check:** Usar `/api/v1/auth/me` para verificar si la sesión es válida
4. **Error Handling:** Los errores de autenticación retornan código 401
5. **Localhost Only:** Actualmente configurado solo para localhost (cambiar en producción)
