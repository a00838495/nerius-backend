# Análisis de la Base de Datos — Plataforma Nerius

Análisis completo del modelo de datos del backend: entidades principales, tablas de unión (relaciones N:M), entidades dependientes, y descripción narrativa de todas las relaciones.

**Fuentes analizadas:**
- [src/db/models/learning_platform.py](src/db/models/learning_platform.py)
- [src/db/models/audit.py](src/db/models/audit.py)
- [src/db/models/base.py](src/db/models/base.py)
- [src/db/models/__init__.py](src/db/models/__init__.py)

**Stack:** SQLAlchemy 2.x (estilo `Mapped[...]` + `mapped_column`), UUIDs en `CHAR(36)`, enums no-nativos (string).

---

## 1. Visión general del dominio

El sistema implementa una **plataforma de aprendizaje (LMS)** estructurada en seis subdominios:

| Subdominio | Tablas principales | Propósito |
|---|---|---|
| **Identidad y acceso** | `areas`, `users`, `roles`, `user_roles`, `sessions` | Autenticación, autorización por roles, organización por áreas. |
| **Contenido educativo** | `courses`, `course_modules`, `lessons`, `lesson_resources` | Jerarquía de contenido. |
| **Aprendizaje del usuario** | `enrollments`, `course_assignments`, `lesson_progress`, `user_badges`, `badges`, `course_badges` | Matrículas, asignaciones con fecha límite, progreso, gamificación. |
| **Evaluación** | `quizzes`, `quiz_questions`, `quiz_question_options`, `quiz_attempts`, `quiz_attempt_responses` | Cuestionarios y resultados. |
| **Banco de Gems** | `gems`, `gem_categories`, `gem_tags`, `gem_tag_links`, `gem_area_links`, `user_gem_collection`, `course_gems`, `lesson_gems` | Prompts/recursos para Gemini. |
| **Foros y observabilidad** | `forum_posts`, `forum_comments`, `analytics_events`, `audit_logs`, `request_metrics` | Comunidad, telemetría, auditoría. |
| **Certificaciones y acceso** | `course_certifications`, `user_certifications`, `user_course_grants` | Emisión de certificados y control de acceso a cursos restringidos. |

---

## 2. Entidades principales (tablas raíz)

Conceptos fundamentales del negocio. Casi todas usan UUID (`CHAR(36)`) como PK y un timestamp `created_at`.

| Entidad | Tabla | Descripción |
|---|---|---|
| **Area** | `areas` | Áreas/departamentos. Agrupa usuarios, cursos, posts del foro y gems. Nombre único. |
| **User** | `users` | Usuario. Pertenece opcionalmente a un área. Estados: `active`, `inactive`, `suspended`. Email único. |
| **Role** | `roles` | Roles del sistema: `super_admin`, `content_admin`, `content_editor`, `content_viewer`, `learner`. Nombre único. |
| **Course** | `courses` | Curso. Estados: `draft`/`published`/`archived`. Tipos de acceso: `free`/`restricted`. |
| **CourseModule** | `course_modules` | Módulo dentro de un curso, ordenado por `sort_order`. |
| **Lesson** | `lessons` | Lección dentro de un módulo, ordenada por `sort_order`. |
| **LessonResource** | `lesson_resources` | Recurso de una lección: `video`, `pdf`, `podcast` o `slide`. |
| **Badge** | `badges` | Insignia con colores y descripción. |
| **ForumPost** | `forum_posts` | Post del foro, con autor, área, categoría y estado de publicación. |
| **ForumComment** | `forum_comments` | Comentario en un post; soporta respuestas anidadas (auto-referencia). |
| **Gem** | `gems` | Prompt/recurso para Gemini con instrucciones, visibilidad (`private`/`shared`/`public`) y estado. |
| **GemCategory** | `gem_categories` | Categoría que agrupa gems. Nombre único. |
| **GemTag** | `gem_tags` | Etiqueta libre para gems. Nombre único. |
| **Quiz** | `quizzes` | Cuestionario asociado **1:1** a una lección (`lesson_id` único). |
| **QuizQuestion** | `quiz_questions` | Pregunta de un quiz. Tipos: `multiple_choice`, `true_false`, `short_answer`, `ordering`, `matching`. |
| **QuizQuestionOption** | `quiz_question_options` | Opción de respuesta para una pregunta. |
| **CourseCertification** | `course_certifications` | Definición de certificación asociada **1:1** a un curso. |

### Entidades transaccionales / de seguimiento

| Entidad | Tabla | Descripción |
|---|---|---|
| **Session** | `sessions` | Sesión activa de autenticación (token, expiración, IP, user agent). PK: token de 64 chars. |
| **Enrollment** | `enrollments` | Matrícula de un usuario en un curso (con progreso, score, estado). |
| **CourseAssignment** | `course_assignments` | Curso asignado por un admin/líder a un usuario, con `due_date`. |
| **LessonProgress** | `lesson_progress` | Progreso de una lección dentro de una matrícula. |
| **UserBadge** | `user_badges` | Insignia ganada por un usuario (con `awarded_at`). |
| **QuizAttempt** | `quiz_attempts` | Intento de un usuario sobre un quiz, ligado a su matrícula. |
| **QuizAttemptResponse** | `quiz_attempt_responses` | Respuesta dada a una pregunta dentro de un intento. |
| **UserCertification** | `user_certifications` | Solicitud/emisión de certificación (`requested`/`approved`/`issued`/`rejected`). |
| **UserCourseGrant** | `user_course_grants` | Acceso explícito otorgado a un usuario para un curso `restricted`. |
| **AnalyticsEvent** | `analytics_events` | Evento analítico (alto volumen, PK `BIGINT`). |
| **AuditLog** | `audit_logs` | Registro de acciones críticas (login, cambio de rol, publicación, etc.). |
| **RequestMetric** | `request_metrics` | Métrica por petición HTTP (alto volumen, PK INT autoincrement). |

---

## 3. Tablas de unión (relaciones N:M)

Tablas cuya razón de existir es vincular dos entidades principales:

| Tabla | Vincula | Notas |
|---|---|---|
| `user_roles` | `users` ↔ `roles` | PK compuesta (`user_id`, `role_id`). Guarda quién asignó el rol (`assigned_by_user_id`). |
| `course_badges` | `courses` ↔ `badges` | Configura qué insignia se obtiene en un curso y a qué `progress_percentage` se otorga. |
| `user_badges` | `users` ↔ `badges` | Registra insignias ganadas por usuario, con `awarded_at`. |
| `gem_tag_links` | `gems` ↔ `gem_tags` | PK compuesta. |
| `gem_area_links` | `gems` ↔ `areas` | PK compuesta. **Adicional** a la columna directa `gems.area_id`. |
| `user_gem_collection` | `users` ↔ `gems` | Gems guardadas por un usuario, con `notes` y `saved_at`. |
| `course_gems` | `courses` ↔ `gems` | Gems vinculadas a un curso, con `sort_order`. |
| `lesson_gems` | `lessons` ↔ `gems` | Gems vinculadas a una lección, con `sort_order`. |

---

## 4. Diagrama de relaciones (resumen textual)

```
Area ──┬── 1:N ── User
       ├── 1:N ── Course
       ├── 1:N ── ForumPost
       ├── 1:N ── Gem (via area_id directo)
       ├── N:M ── Gem (via gem_area_links)
       └── 1:N ── AnalyticsEvent

User ──┬── N:M ── Role               (user_roles)
       ├── 1:N ── Session
       ├── 1:N ── Enrollment ─────── 1:N ── LessonProgress
       │                       └──── 1:N ── QuizAttempt ── 1:N ── QuizAttemptResponse
       ├── 1:N ── CourseAssignment   (recibidas y enviadas)
       ├── N:M ── Badge              (user_badges)
       ├── 1:N ── ForumPost
       ├── 1:N ── ForumComment
       ├── 1:N ── Gem                (created_by)
       ├── N:M ── Gem                (user_gem_collection — gems guardadas)
       ├── 1:N ── UserCertification
       ├── 1:N ── UserCourseGrant
       └── 1:N ── AuditLog / RequestMetric / AnalyticsEvent

Course ──┬── 1:N ── CourseModule ── 1:N ── Lesson ── 1:N ── LessonResource
         │                                       ├── 1:1 ── Quiz ── 1:N ── QuizQuestion ── 1:N ── QuizQuestionOption
         │                                       └── N:M ── Gem        (lesson_gems)
         ├── 1:N ── Enrollment
         ├── 1:N ── CourseAssignment
         ├── N:M ── Badge      (course_badges)
         ├── N:M ── Gem        (course_gems)
         ├── 1:1 ── CourseCertification ── 1:N ── UserCertification
         └── 1:N ── UserCourseGrant

ForumPost ── 1:N ── ForumComment ── (auto-referencia para replies)

Gem ──┬── N:1 ── GemCategory
      ├── N:M ── GemTag         (gem_tag_links)
      ├── N:M ── Area           (gem_area_links)
      ├── N:M ── User           (user_gem_collection)
      ├── N:M ── Course         (course_gems)
      └── N:M ── Lesson         (lesson_gems)
```

---

## 5. Descripción narrativa de TODAS las relaciones

### 5.1 Identidad y organización

- Un **área** puede agrupar **muchos usuarios**; un **usuario** pertenece a **un área (opcional)**. Si el área se elimina, el `area_id` del usuario queda en `NULL` (`SET NULL`).
- Un **usuario** puede tener **muchos roles**, y un **rol** puede ser asignado a **muchos usuarios** (relación N:M vía `user_roles`).
- Un **usuario** puede haber **asignado roles a muchos otros usuarios** (autocolumna `assigned_by_user_id` en `user_roles`).
- Un **usuario** puede tener **muchas sesiones** activas; al borrar el usuario, sus sesiones se eliminan en cascada.

### 5.2 Cursos, módulos, lecciones y recursos

- Un **área** puede contener **muchos cursos**; un **curso** pertenece a **un área (opcional)**.
- Un **usuario** (típicamente `content_admin`) puede **crear muchos cursos**; un **curso** tiene **un creador** (`RESTRICT` en delete: no se puede borrar al creador si tiene cursos).
- Un **curso** está compuesto por **muchos módulos**; cada **módulo** pertenece a **un solo curso** (cascade delete).
- Un **módulo** contiene **muchas lecciones**; cada **lección** pertenece a **un solo módulo** (cascade delete).
- Una **lección** tiene **muchos recursos** (`LessonResource`: video, pdf, podcast, slide); un **recurso** pertenece a **una sola lección**.

### 5.3 Matrículas, asignaciones y progreso

- Un **usuario** puede matricularse en **muchos cursos**, y un **curso** puede tener **muchos usuarios matriculados** (relación N:M vía `enrollments`, con `UNIQUE(user_id, course_id)` — un usuario no puede tener dos matrículas en el mismo curso).
- Un **usuario** puede **recibir muchas asignaciones de cursos** (`CourseAssignment`), y un **curso** puede ser **asignado a muchos usuarios**, con un `due_date`. Adicionalmente, un **usuario** puede haber **enviado/asignado muchos cursos** a otros usuarios (`assigned_by_user_id`).
- Una **matrícula** tiene **muchos registros de progreso de lección** (`LessonProgress`), uno por cada lección iniciada/completada — la unicidad `(enrollment_id, lesson_id)` impide duplicados.
- Una **lección** puede tener **muchos registros de progreso** (uno por cada matrícula que la haya tocado).

### 5.4 Insignias (badges)

- Un **curso** puede otorgar **muchas insignias**, y una **insignia** puede estar configurada en **muchos cursos** (N:M vía `course_badges`). Cada vínculo guarda el `progress_percentage` requerido para otorgarla.
- Un **usuario** puede ganar **muchas insignias**, y una **insignia** puede ser ganada por **muchos usuarios** (N:M vía `user_badges`, con `awarded_at`).

### 5.5 Banco de Gems (prompts de Gemini)

- Una **gem** pertenece a **una categoría (opcional)**; una **categoría** puede tener **muchas gems**.
- Una **gem** tiene **un creador** (`User`, con `RESTRICT` en delete); un **usuario** puede haber **creado muchas gems**.
- Una **gem** se relaciona con **un área (opcional)** vía la columna directa `area_id`, **además** de poder asociarse a **muchas áreas** vía `gem_area_links` (relación N:M).
- Una **gem** puede tener **muchas etiquetas**, y una **etiqueta** puede estar en **muchas gems** (N:M vía `gem_tag_links`).
- **Muchas gems pueden ser guardadas por muchos usuarios** (N:M vía `user_gem_collection`); cada entrada tiene `saved_at` y `notes` opcionales.
- Una **gem** puede estar vinculada a **muchos cursos**, y un **curso** puede tener **muchas gems** asociadas (N:M vía `course_gems`, con `sort_order`).
- Una **gem** puede estar vinculada a **muchas lecciones**, y una **lección** puede tener **muchas gems** asociadas (N:M vía `lesson_gems`, con `sort_order`).

### 5.6 Quizzes y evaluaciones

- Una **lección** tiene **a lo más un quiz** (relación 1:1, `quizzes.lesson_id` con `unique=True`).
- Un **quiz** contiene **muchas preguntas** (`QuizQuestion`); cada **pregunta** pertenece a **un solo quiz**.
- Una **pregunta** tiene **muchas opciones** (`QuizQuestionOption`); cada **opción** pertenece a **una sola pregunta**. Una opción puede tener `match_target` (para preguntas tipo `matching`).
- Un **usuario** puede realizar **muchos intentos** sobre un mismo quiz (numerados con `attempt_number`), con `UNIQUE(quiz_id, user_id, attempt_number)`. Cada **intento** está ligado a la **matrícula** correspondiente del usuario en el curso.
- Un **intento** contiene **muchas respuestas** (`QuizAttemptResponse`), una por pregunta (`UNIQUE(attempt_id, question_id)`). Una **respuesta** puede referenciar **una opción seleccionada (opcional)** o llevar texto libre / JSON para `ordering`/`matching`.

### 5.7 Certificaciones y control de acceso

- Un **curso** tiene **a lo más una definición de certificación** (`CourseCertification`, 1:1 con `course_id` único). Esta define costo y días de validez.
- Una **definición de certificación** puede generar **muchas certificaciones de usuario** (`UserCertification`).
- Un **usuario** puede tener **muchas certificaciones**, una por cada `course_certification_id` — la unicidad `(user_id, course_certification_id)` evita duplicados. Cada `UserCertification` referencia también la **matrícula** del usuario en ese curso, y atraviesa estados `requested → approved → issued`, o `rejected`.
- Para cursos con `access_type = restricted`, un **usuario** puede tener **muchos accesos otorgados** (`UserCourseGrant`), y un **curso restringido** puede tener **muchos usuarios autorizados**. Cada grant guarda quién lo concedió (`granted_by_user_id`).

### 5.8 Foro

- Un **área** puede tener **muchos posts**; un **post** pertenece a **un área (opcional)**.
- Un **usuario** puede ser autor de **muchos posts**; un **post** tiene **un autor** (cascade delete con el usuario).
- Un **post** tiene **muchos comentarios**; un **comentario** pertenece a **un solo post**.
- Un **usuario** puede ser autor de **muchos comentarios**.
- Un **comentario** puede ser respuesta a **otro comentario** (auto-referencia `parent_comment_id`), permitiendo hilos anidados; al borrar el padre, las respuestas quedan con `parent_comment_id = NULL` (`SET NULL`) — no se borran en cascada.

### 5.9 Observabilidad y auditoría

- Un **usuario** puede generar **muchos eventos analíticos**, y un evento puede asociarse opcionalmente a **un área**, **un curso** y **una lección** (todos `SET NULL` en delete). Tabla de alto volumen, PK `BIGINT`.
- Un **usuario** puede tener **muchos audit logs** asociados (acciones críticas: login, cambio de rol, publicación, etc.). **Sin** relación SQLAlchemy `back_populates` para mantener la tabla aislada.
- Un **usuario** puede tener **muchos `RequestMetric`** asociados (una fila por petición HTTP). Tabla de alto volumen con PK INT autoincrement.

---

## 6. Convenciones del esquema

- **PKs**: la mayoría son UUID en formato `CHAR(36)`. Excepciones:
  - `analytics_events` → `BIGINT` autoincrement.
  - `request_metrics` → `INT` autoincrement.
  - `sessions` → token string de 64 chars.
  - `user_roles`, `gem_tag_links`, `gem_area_links` → PK compuesta de las dos FKs.
- **Mixins**: `UUIDPrimaryKeyMixin` y `CreatedAtMixin` se aplican a casi todas las entidades.
- **Enums**: definidos como `Enum(..., native_enum=False)` — se persisten como strings, lo que facilita migraciones entre motores.
- **`ON DELETE`**:
  - `CASCADE`: cuando la entidad hija no tiene sentido sin la padre (lecciones de un módulo, comentarios de un post, opciones de una pregunta).
  - `SET NULL`: cuando la relación es contextual y se quiere preservar la entidad hija (área de un usuario, autor de un audit log, área de un post).
  - `RESTRICT`: para proteger creadores (no se puede borrar un usuario que creó cursos o gems).
- **`UniqueConstraint`** se usa ampliamente para evitar duplicados:
  - Matrículas (`user_id` + `course_id`)
  - Asignaciones (`assigned_to_user_id` + `course_id`)
  - Insignias por usuario (`user_id` + `badge_id`)
  - Intentos numerados (`quiz_id` + `user_id` + `attempt_number`)
  - Vínculos N:M (todos)
  - Orden de elementos hermanos (`sort_order` por padre — módulos, lecciones, preguntas, opciones)
- **Índices** explícitos en columnas de búsqueda frecuente: `area_id+status`, `user_id`, `expires_at`, `event_name+event_time`, `path`, `due_date`, etc.
- **Timestamps**: `created_at` siempre; `updated_at` en entidades editables (cursos, posts, gems, quizzes); `last_activity_at` en sesiones, matrículas y progreso.

---

## 7. Resumen de relaciones (cardinalidades)

| Relación | Cardinalidad | Tabla / FK |
|---|---|---|
| Área ↔ Usuario | 1:N | `users.area_id` |
| Área ↔ Curso | 1:N | `courses.area_id` |
| Área ↔ ForumPost | 1:N | `forum_posts.area_id` |
| Área ↔ Gem (directa) | 1:N | `gems.area_id` |
| Área ↔ Gem (extra) | N:M | `gem_area_links` |
| Área ↔ AnalyticsEvent | 1:N | `analytics_events.area_id` |
| Usuario ↔ Rol | N:M | `user_roles` |
| Usuario ↔ Sesión | 1:N | `sessions.user_id` |
| Usuario ↔ Enrollment | 1:N | `enrollments.user_id` |
| Usuario ↔ Curso (matrícula) | N:M | `enrollments` |
| Usuario ↔ Curso (asignación) | N:M | `course_assignments` |
| Usuario ↔ Curso (acceso a restringidos) | N:M | `user_course_grants` |
| Usuario ↔ Badge | N:M | `user_badges` |
| Usuario ↔ Gem (creador) | 1:N | `gems.created_by_user_id` |
| Usuario ↔ Gem (colección) | N:M | `user_gem_collection` |
| Usuario ↔ ForumPost | 1:N | `forum_posts.author_user_id` |
| Usuario ↔ ForumComment | 1:N | `forum_comments.author_user_id` |
| Usuario ↔ QuizAttempt | 1:N | `quiz_attempts.user_id` |
| Usuario ↔ UserCertification | 1:N | `user_certifications.user_id` |
| Usuario ↔ AuditLog | 1:N | `audit_logs.user_id` |
| Usuario ↔ RequestMetric | 1:N | `request_metrics.user_id` |
| Curso ↔ Módulo | 1:N | `course_modules.course_id` |
| Módulo ↔ Lección | 1:N | `lessons.module_id` |
| Lección ↔ Recurso | 1:N | `lesson_resources.lesson_id` |
| Lección ↔ Quiz | 1:1 | `quizzes.lesson_id` (UNIQUE) |
| Curso ↔ Badge | N:M | `course_badges` |
| Curso ↔ Gem | N:M | `course_gems` |
| Lección ↔ Gem | N:M | `lesson_gems` |
| Curso ↔ Certificación | 1:1 | `course_certifications.course_id` (UNIQUE) |
| Certificación ↔ UserCertification | 1:N | `user_certifications.course_certification_id` |
| Enrollment ↔ LessonProgress | 1:N | `lesson_progress.enrollment_id` |
| Enrollment ↔ QuizAttempt | 1:N | `quiz_attempts.enrollment_id` |
| Enrollment ↔ UserCertification | 1:N | `user_certifications.enrollment_id` |
| Quiz ↔ Question | 1:N | `quiz_questions.quiz_id` |
| Question ↔ Option | 1:N | `quiz_question_options.question_id` |
| Attempt ↔ Response | 1:N | `quiz_attempt_responses.attempt_id` |
| Response ↔ Option (seleccionada) | N:1 (opcional) | `quiz_attempt_responses.selected_option_id` |
| ForumPost ↔ ForumComment | 1:N | `forum_comments.post_id` |
| ForumComment ↔ ForumComment (replies) | 1:N (auto) | `forum_comments.parent_comment_id` |
| Gem ↔ GemCategory | N:1 | `gems.category_id` |
| Gem ↔ GemTag | N:M | `gem_tag_links` |

---

## 8. Conclusiones

- El **núcleo** del modelo es **`User` + `Course`**, con `Area` como dimensión organizativa transversal presente en cinco entidades distintas.
- La jerarquía de contenido es estricta: **Course → Module → Lesson → Resource/Quiz**, con eliminación en cascada hacia abajo.
- El **progreso del usuario** se modela en tres niveles encadenados: matrícula (curso) → progreso por lección → intentos de quiz, todos ligados entre sí mediante `enrollment_id`.
- El **banco de Gems** es el subsistema más conectado: se vincula a Áreas (doble: directa y N:M), Categorías, Tags, Usuarios (creador y colección), Cursos y Lecciones — un total de **6 tipos de relaciones** desde la entidad `Gem`.
- Las **certificaciones** y los **grants** de acceso introducen un control de acceso adicional sobre cursos restringidos, separado del sistema de roles.
- Los modelos de **observabilidad** (`analytics_events`, `audit_logs`, `request_metrics`) están deliberadamente desacoplados (sin `back_populates`) para no contaminar el modelo central y permitir alto volumen.
- El uso de **enums no nativos**, **UUIDs** y **`SET NULL` agresivo** sugiere que el diseño está pensado para portabilidad entre motores de BD (SQLite local, MySQL/PostgreSQL en producción) y resiliencia ante eliminación de entidades.
