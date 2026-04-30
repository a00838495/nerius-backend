"""Seed the database with mock data."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.db.session import SessionLocal, engine
from src.db.models.base import Base
from src.db.models.learning_platform import (
    Area,
    User,
    Role,
    UserRole,
    Course,
    CourseModule,
    Lesson,
    LessonResource,
    Enrollment,
    CourseAssignment,
    Badge,
    CourseBadge,
    UserBadge,
    ForumPost,
    ForumComment,
    RoleName,
    UserStatus,
    PublicationStatus,
    EnrollmentStatus,
    ResourceType,
    GemCategory,
    Gem,
    GemTag,
    GemTagLink,
    GemAreaLink,
    UserGemCollection,
    CourseGem,
    GemVisibility,
    Quiz,
    QuizQuestion,
    QuizQuestionOption,
    QuestionType,
    CourseCertification,
    UserCourseGrant,
    CourseAccessType,
)
from src.core.auth import hash_password


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def seed_database():
    """Seed the database with mock data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("Database already seeded, skipping...")
            return

        # Create areas
        area_tech = Area(
            id=generate_uuid(),
            name="Tecnología",
            created_at=datetime.utcnow(),
        )
        area_business = Area(
            id=generate_uuid(),
            name="Negocios",
            created_at=datetime.utcnow(),
        )
        db.add_all([area_tech, area_business])
        db.flush()

        # Create roles
        role_super_admin = Role(
            id=generate_uuid(),
            name=RoleName.SUPER_ADMIN,
            created_at=datetime.utcnow(),
        )
        role_admin = Role(
            id=generate_uuid(),
            name=RoleName.CONTENT_ADMIN,
            created_at=datetime.utcnow(),
        )
        role_editor = Role(
            id=generate_uuid(),
            name=RoleName.CONTENT_EDITOR,
            created_at=datetime.utcnow(),
        )
        role_viewer = Role(
            id=generate_uuid(),
            name=RoleName.CONTENT_VIEWER,
            created_at=datetime.utcnow(),
        )
        role_user = Role(
            id=generate_uuid(),
            name=RoleName.LEARNER,
            created_at=datetime.utcnow(),
        )
        db.add_all([role_super_admin, role_admin, role_editor, role_viewer, role_user])
        db.flush()

        # Create users
        user_super_admin = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="superadmin@whirlpool.com",
            first_name="Super",
            last_name="Admin",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        user_admin = User(
            id=generate_uuid(),
            area_id=area_business.id,
            email="admin@whirlpool.com",
            first_name="Content",
            last_name="Admin",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Female",
            created_at=datetime.utcnow(),
        )

        user_editor = User(
            id=generate_uuid(),
            area_id=area_business.id,
            email="editor@whirlpool.com",
            first_name="Elena",
            last_name="Editor",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Female",
            created_at=datetime.utcnow(),
        )

        user_viewer = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="viewer@whirlpool.com",
            first_name="Víctor",
            last_name="Viewer",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        user_learner = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="user@whirlpool.com",
            first_name="Juan",
            last_name="Perez",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        user_learner_2 = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="diego.herrera@whirlpool.com",
            first_name="Diego",
            last_name="Herrera",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        user_learner_3 = User(
            id=generate_uuid(),
            area_id=area_business.id,
            email="maria.gomez@whirlpool.com",
            first_name="Maria",
            last_name="Gomez",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Female",
            created_at=datetime.utcnow(),
        )

        user_learner_4 = User(
            id=generate_uuid(),
            area_id=area_tech.id,
            email="luis.torres@whirlpool.com",
            first_name="Luis",
            last_name="Torres",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Male",
            created_at=datetime.utcnow(),
        )

        user_learner_5 = User(
            id=generate_uuid(),
            area_id=area_business.id,
            email="sofia.ramirez@whirlpool.com",
            first_name="Sofia",
            last_name="Ramirez",
            password=hash_password("password123"),
            status=UserStatus.active,
            gender="Female",
            created_at=datetime.utcnow(),
        )

        db.add_all([
            user_super_admin,
            user_admin,
            user_editor,
            user_viewer,
            user_learner,
            user_learner_2,
            user_learner_3,
            user_learner_4,
            user_learner_5,
        ])
        db.flush()

        # Assign roles to users
        user_role_super = UserRole(
            user_id=user_super_admin.id,
            role_id=role_super_admin.id,
            created_at=datetime.utcnow(),
        )
        user_role_admin = UserRole(
            user_id=user_admin.id,
            role_id=role_admin.id,
            created_at=datetime.utcnow(),
        )
        user_role_editor = UserRole(
            user_id=user_editor.id,
            role_id=role_editor.id,
            created_at=datetime.utcnow(),
        )
        user_role_viewer = UserRole(
            user_id=user_viewer.id,
            role_id=role_viewer.id,
            created_at=datetime.utcnow(),
        )
        user_role_user = UserRole(
            user_id=user_learner.id,
            role_id=role_user.id,
            created_at=datetime.utcnow(),
        )
        user_role_user_2 = UserRole(
            user_id=user_learner_2.id,
            role_id=role_user.id,
            created_at=datetime.utcnow(),
        )
        user_role_user_3 = UserRole(
            user_id=user_learner_3.id,
            role_id=role_user.id,
            created_at=datetime.utcnow(),
        )
        user_role_user_4 = UserRole(
            user_id=user_learner_4.id,
            role_id=role_user.id,
            created_at=datetime.utcnow(),
        )
        user_role_user_5 = UserRole(
            user_id=user_learner_5.id,
            role_id=role_user.id,
            created_at=datetime.utcnow(),
        )
        # Every user gets the learner role by default (in addition to any admin role)
        admin_users_learner_base = [
            UserRole(user_id=user_super_admin.id, role_id=role_user.id, created_at=datetime.utcnow()),
            UserRole(user_id=user_admin.id, role_id=role_user.id, created_at=datetime.utcnow()),
            UserRole(user_id=user_editor.id, role_id=role_user.id, created_at=datetime.utcnow()),
            UserRole(user_id=user_viewer.id, role_id=role_user.id, created_at=datetime.utcnow()),
        ]

        db.add_all([
            user_role_super,
            user_role_admin,
            user_role_editor,
            user_role_viewer,
            user_role_user,
            user_role_user_2,
            user_role_user_3,
            user_role_user_4,
            user_role_user_5,
            *admin_users_learner_base,
        ])
        db.flush()

        def build_completed_enrollment(
            user_id: str,
            course_id: str,
            started_days_ago: int,
            completion_days: float,
        ) -> Enrollment:
            started_at = datetime.utcnow() - timedelta(days=started_days_ago)
            completed_at = started_at + timedelta(days=completion_days)
            return Enrollment(
                id=generate_uuid(),
                user_id=user_id,
                course_id=course_id,
                status=EnrollmentStatus.completed,
                progress_percent=100,
                started_at=started_at,
                completed_at=completed_at,
                last_activity_at=completed_at,
                created_at=started_at,
            )

        # Create courses
        course1 = Course(
            id=generate_uuid(), area_id=area_tech.id,
            title="Introducción a Google Gemini para Empresas",
            description="Descubre el potencial de Google Gemini como asistente de inteligencia artificial para el entorno empresarial. Aprende a utilizarlo para aumentar tu productividad desde el primer día.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=240,
            cover_url="https://www.gstatic.com/lamda/images/gemini_aurora_thumbnail_4g_e74822ff0ca4259beb718.png",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course2 = Course(
            id=generate_uuid(), area_id=area_tech.id,
            title="Creación de Gemas Personalizadas en Google Gemini",
            description="Aprende a diseñar, construir y publicar Gemas personalizadas en Google Gemini para automatizar flujos de trabajo y crear asistentes de IA adaptados a las necesidades de tu equipo.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=360,
            cover_url="https://andro4all.com/hero/2024/12/gems-de-google.jpg?width=768&aspect_ratio=16:9&format=nowebp",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course3 = Course(
            id=generate_uuid(), area_id=area_business.id,
            title="Gemas de Google para Ventas y CRM",
            description="Transforma tu proceso de ventas con Gemas de Google Gemini. Automatiza propuestas, analiza tu pipeline y genera reportes de ventas con la potencia de la inteligencia artificial.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=420,
            cover_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSn7f5pNcXhbUy1XiUQ0JB5zBYwbB98NEsNkg&s",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course4 = Course(
            id=generate_uuid(), area_id=area_tech.id,
            title="Google Workspace + Gemini para Productividad",
            description="Domina la integración de Gemini con todas las herramientas de Google Workspace: Gmail, Docs, Sheets y Slides. Multiplica tu productividad con asistencia de IA en cada aplicación.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=600,
            cover_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1PJeq6VwlYN45w6KvEkmVdmn5qLD48AqteA&s",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course5 = Course(
            id=generate_uuid(), area_id=area_business.id,
            title="Gemas de Google para Recursos Humanos",
            description="Revoluciona la gestión de talento con Gemas diseñadas para RRHH. Automatiza el reclutamiento, onboarding, capacitación y evaluación del desempeño con IA.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=480,
            cover_url="https://www.bizneo.com/blog/wp-content/uploads/2019/02/Consultoria-Recursos-Humanos.png",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course6 = Course(
            id=generate_uuid(), area_id=area_business.id,
            title="Gemas de Google para Marketing Digital",
            description="Potencia tu estrategia de marketing con Gemas de Gemini. Crea contenido, analiza métricas y optimiza campañas con la ayuda de la inteligencia artificial.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=360,
            cover_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQGK80Pm-5mgfmX2HU-MR6tKQCMcVUkA2EPQ&s",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course7 = Course(
            id=generate_uuid(), area_id=area_business.id,
            title="Google Meet y Gemini para Reuniones Efectivas",
            description="Transforma tus reuniones con la integración de Google Meet y Gemini. Obtén transcripciones automáticas, minutas inteligentes y seguimiento de acuerdos sin esfuerzo.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=180,
            cover_url="https://reindeersoft.com/_next/image?url=https%3A%2F%2Freindeersoft.com%2Fapi%2Fuploads%2FReindeerSoft-1728644102947.jpg&w=828&q=75",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course8 = Course(
            id=generate_uuid(), area_id=area_business.id,
            title="Google Gemini Advanced para Ejecutivos",
            description="Curso para líderes empresariales que desean aprovechar Gemini Advanced en la toma de decisiones estratégicas, análisis ejecutivo y comunicación de alto nivel.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=300,
            cover_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGMI_bJ8BeUCBzNebgIFpMPMqAk91hlhT88A&s",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course9 = Course(
            id=generate_uuid(), area_id=area_business.id,
            title="Gemas de Google para Finanzas y Contabilidad",
            description="Optimiza el análisis financiero, generación de reportes y control presupuestal con Gemas personalizadas de Google Gemini para equipos de finanzas y contabilidad.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=540,
            cover_url="https://upload.wikimedia.org/wikipedia/commons/3/33/Google_Finance.png",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        course10 = Course(
            id=generate_uuid(), area_id=area_tech.id,
            title="Seguridad y Administración de Google Workspace",
            description="Aprende a administrar y proteger Google Workspace en tu organización. Gestión de usuarios, políticas de seguridad, auditoría y respuesta a incidentes.",
            status=PublicationStatus.PUBLISHED, estimated_minutes=420,
            cover_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHRF0ybXDh5GPkvdobK2MH6VhrRkQbzGhN8w&s",
            created_by_user_id=user_admin.id, created_at=datetime.utcnow(),
        )
        db.add_all([course1, course2, course3, course4, course5,
                    course6, course7, course8, course9, course10])
        db.flush()

        # ==================== COURSE 1: Introducción a Google Gemini para Empresas ====================
        c1_mod1 = CourseModule(id=generate_uuid(), course_id=course1.id, title="¿Qué es Google Gemini?", sort_order=1, created_at=datetime.utcnow())
        c1_m1_l1 = Lesson(id=generate_uuid(), module_id=c1_mod1.id, title="Historia y evolución de Google Gemini", description="Conoce el origen de Gemini, sus versiones y su posición en el ecosistema de IA empresarial.", sort_order=1, estimated_minutes=30, created_at=datetime.utcnow())
        c1_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c1_m1_l1.id, resource_type=ResourceType.VIDEO, title="Introducción oficial a Gemini", external_url="https://www.youtube.com/watch?v=_fuimO6ErKI", duration_seconds=61, created_at=datetime.utcnow())
        c1_m1_l2 = Lesson(id=generate_uuid(), module_id=c1_mod1.id, title="Casos de uso empresariales de Gemini", description="Explora los principales casos de uso de Gemini en el entorno corporativo con ejemplos reales.", sort_order=2, estimated_minutes=35, created_at=datetime.utcnow())
        c1_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c1_m1_l2.id, resource_type=ResourceType.PDF, title="Guía de casos de uso empresariales", external_url="https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Lite-Model-Card.pdf", created_at=datetime.utcnow())
        c1_m1_l3 = Lesson(id=generate_uuid(), module_id=c1_mod1.id, title="Gemini vs otras IAs empresariales", description="Análisis comparativo entre Google Gemini, Microsoft Copilot y ChatGPT Enterprise.", sort_order=3, estimated_minutes=30, created_at=datetime.utcnow())
        c1_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c1_m1_l3.id, resource_type=ResourceType.VIDEO, title="Comparativa de IAs empresariales", external_url="https://www.youtube.com/watch?v=v5H3bonLIeA", duration_seconds=755, created_at=datetime.utcnow())

        c1_mod2 = CourseModule(id=generate_uuid(), course_id=course1.id, title="Primeros Pasos con Gemini", sort_order=2, created_at=datetime.utcnow())
        c1_m2_l1 = Lesson(id=generate_uuid(), module_id=c1_mod2.id, title="Acceso y configuración de Gemini", description="Cómo activar Gemini en tu cuenta Google Workspace y configurarlo para uso empresarial.", sort_order=1, estimated_minutes=25, created_at=datetime.utcnow())
        c1_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c1_m2_l1.id, resource_type=ResourceType.VIDEO, title="Configuración inicial de Gemini", external_url="https://www.youtube.com/watch?v=v3QEdKkFdGM", duration_seconds=900, created_at=datetime.utcnow())
        c1_m2_l2 = Lesson(id=generate_uuid(), module_id=c1_mod2.id, title="Interfaz y funcionalidades básicas", description="Tour completo por la interfaz: chat, historial, configuración y ajustes de respuesta.", sort_order=2, estimated_minutes=30, created_at=datetime.utcnow())
        c1_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c1_m2_l2.id, resource_type=ResourceType.VIDEO, title="Tour por la interfaz de Gemini", external_url="https://www.youtube.com/watch?v=qbqZQFOVfA8", duration_seconds=1500, created_at=datetime.utcnow())
        c1_m2_l3 = Lesson(id=generate_uuid(), module_id=c1_mod2.id, title="Prompts efectivos para el trabajo diario", description="Técnicas de prompting para extraer el máximo valor de Gemini en tareas cotidianas empresariales.", sort_order=3, estimated_minutes=45, created_at=datetime.utcnow())
        c1_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c1_m2_l3.id, resource_type=ResourceType.PDF, title="Guía de prompts para empresas", external_url="https://antonio-richaud.com/biblioteca/archivo/guia-prompts/guia-prompts.pdf", created_at=datetime.utcnow())

        c1_mod3 = CourseModule(id=generate_uuid(), course_id=course1.id, title="Gemini en tu Flujo de Trabajo", sort_order=3, created_at=datetime.utcnow())
        c1_m3_l1 = Lesson(id=generate_uuid(), module_id=c1_mod3.id, title="Integración con las apps de Google Workspace", description="Cómo Gemini funciona dentro de Gmail, Drive, Docs, Sheets y Meet.", sort_order=1, estimated_minutes=40, created_at=datetime.utcnow())
        c1_m3_l1_res = LessonResource(id=generate_uuid(), lesson_id=c1_m3_l1.id, resource_type=ResourceType.VIDEO, title="Gemini en Google Workspace", external_url="https://www.youtube.com/watch?v=o5Ur1pm4oDA", duration_seconds=2400, created_at=datetime.utcnow())
        c1_m3_l2 = Lesson(id=generate_uuid(), module_id=c1_mod3.id, title="Privacidad y datos empresariales en Gemini", description="Políticas de datos de Gemini en Workspace, configuración de privacidad y cumplimiento normativo.", sort_order=2, estimated_minutes=30, created_at=datetime.utcnow())
        c1_m3_l2_res = LessonResource(id=generate_uuid(), lesson_id=c1_m3_l2.id, resource_type=ResourceType.PDF, title="Políticas de privacidad Gemini para Workspace", external_url="https://assets.stevens.edu/mviowpldu823/3iXQ74HU9dPDNmN0C4RFwl/7bd34634a4d8e0dcb22d963fc6746681/Guide_to_Data_Security_and_Protection_in_AI_Tools.pdf", created_at=datetime.utcnow())
        c1_m3_l3 = Lesson(id=generate_uuid(), module_id=c1_mod3.id, title="Ética y uso responsable de IA en la empresa", description="Principios éticos para el uso responsable de Gemini en entornos empresariales.", sort_order=3, estimated_minutes=30, created_at=datetime.utcnow())
        c1_m3_l3_res = LessonResource(id=generate_uuid(), lesson_id=c1_m3_l3.id, resource_type=ResourceType.PDF, title="Guía de ética en IA empresarial", external_url="https://revistas.ibero.mx/ibero/uploads/volumenes/69/pdf/6-etica-en-la-inteligencia-artificial.pdf", created_at=datetime.utcnow())
        # Módulo 4: Evaluación Final (quiz-only)
        c1_mod4 = CourseModule(id=generate_uuid(), course_id=course1.id, title="Evaluación Final", sort_order=4, created_at=datetime.utcnow())
        c1_final = Lesson(id=generate_uuid(), module_id=c1_mod4.id, title="Examen Final: Google Gemini para Empresas", description="Evaluación integral de todos los módulos del curso. Debes obtener 70% para aprobar.", sort_order=1, estimated_minutes=20, created_at=datetime.utcnow())

        db.add_all([
            c1_mod1, c1_m1_l1, c1_m1_l1_res, c1_m1_l2, c1_m1_l2_res, c1_m1_l3, c1_m1_l3_res,
            c1_mod2, c1_m2_l1, c1_m2_l1_res, c1_m2_l2, c1_m2_l2_res, c1_m2_l3, c1_m2_l3_res,
            c1_mod3, c1_m3_l1, c1_m3_l1_res, c1_m3_l2, c1_m3_l2_res, c1_m3_l3, c1_m3_l3_res,
            c1_mod4, c1_final,
        ])
        db.flush()

        # ==================== COURSE 2: Creación de Gemas Personalizadas en Google Gemini ====================
        c2_mod1 = CourseModule(id=generate_uuid(), course_id=course2.id, title="Fundamentos de las Gemas de Gemini", sort_order=1, created_at=datetime.utcnow())
        c2_m1_l1 = Lesson(id=generate_uuid(), module_id=c2_mod1.id, title="¿Qué son las Gemas y para qué sirven?", description="Concepto de Gemas, diferencias con el chat general y ventajas de las Gemas personalizadas para equipos.", sort_order=1, estimated_minutes=30, created_at=datetime.utcnow())
        c2_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c2_m1_l1.id, resource_type=ResourceType.VIDEO, title="Introducción a las Gemas de Gemini", external_url="https://www.youtube.com/embed/gems_intro", duration_seconds=1500, created_at=datetime.utcnow())
        c2_m1_l2 = Lesson(id=generate_uuid(), module_id=c2_mod1.id, title="Anatomía de una Gema exitosa", description="Componentes clave: nombre, instrucciones del sistema, contexto empresarial y ejemplos de respuesta.", sort_order=2, estimated_minutes=40, created_at=datetime.utcnow())
        c2_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c2_m1_l2.id, resource_type=ResourceType.PDF, title="Plantilla de diseño de Gemas", external_url="https://example.com/gems-design-template.pdf", created_at=datetime.utcnow())
        c2_m1_l3 = Lesson(id=generate_uuid(), module_id=c2_mod1.id, title="Gemas públicas vs privadas vs de equipo", description="Diferencias entre los tipos de Gemas, cuándo usar cada una y gestión de permisos de acceso.", sort_order=3, estimated_minutes=25, created_at=datetime.utcnow())
        c2_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c2_m1_l3.id, resource_type=ResourceType.VIDEO, title="Tipos de Gemas en Google Gemini", external_url="https://www.youtube.com/embed/gems_types", duration_seconds=1200, created_at=datetime.utcnow())

        c2_mod2 = CourseModule(id=generate_uuid(), course_id=course2.id, title="Diseño de Instrucciones para Gemas", sort_order=2, created_at=datetime.utcnow())
        c2_m2_l1 = Lesson(id=generate_uuid(), module_id=c2_mod2.id, title="Redacción de instrucciones del sistema", description="Técnicas avanzadas de prompt engineering para escribir instrucciones de sistema claras y efectivas.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c2_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c2_m2_l1.id, resource_type=ResourceType.VIDEO, title="Prompt engineering para Gemas", external_url="https://www.youtube.com/embed/gems_prompt_eng", duration_seconds=2400, created_at=datetime.utcnow())
        c2_m2_l2 = Lesson(id=generate_uuid(), module_id=c2_mod2.id, title="Definición de rol y contexto empresarial", description="Cómo asignar un rol específico a tu Gema y proveer el contexto necesario para respuestas precisas.", sort_order=2, estimated_minutes=45, created_at=datetime.utcnow())
        c2_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c2_m2_l2.id, resource_type=ResourceType.PDF, title="Guía de roles empresariales para Gemas", external_url="https://example.com/gems-roles-guide.pdf", created_at=datetime.utcnow())
        c2_m2_l3 = Lesson(id=generate_uuid(), module_id=c2_mod2.id, title="Pruebas y refinamiento iterativo de Gemas", description="Metodología para probar, evaluar y mejorar iterativamente las instrucciones hasta lograr resultados óptimos.", sort_order=3, estimated_minutes=60, created_at=datetime.utcnow())
        c2_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c2_m2_l3.id, resource_type=ResourceType.VIDEO, title="Ciclo de mejora de Gemas", external_url="https://www.youtube.com/embed/gems_iteration", duration_seconds=3000, created_at=datetime.utcnow())

        c2_mod3 = CourseModule(id=generate_uuid(), course_id=course2.id, title="Publicación y Administración de Gemas", sort_order=3, created_at=datetime.utcnow())
        c2_m3_l1 = Lesson(id=generate_uuid(), module_id=c2_mod3.id, title="Cómo publicar y compartir tu Gema con el equipo", description="Pasos para publicar una Gema, compartirla con colaboradores y gestionar el acceso desde Google Workspace.", sort_order=1, estimated_minutes=30, created_at=datetime.utcnow())
        c2_m3_l1_res = LessonResource(id=generate_uuid(), lesson_id=c2_m3_l1.id, resource_type=ResourceType.VIDEO, title="Publicar y compartir Gemas", external_url="https://www.youtube.com/embed/gems_publish", duration_seconds=1500, created_at=datetime.utcnow())
        c2_m3_l2 = Lesson(id=generate_uuid(), module_id=c2_mod3.id, title="Mantenimiento y actualización de Gemas", description="Ciclo de vida de una Gema: cuándo actualizar, gestión de versiones y comunicación de cambios al equipo.", sort_order=2, estimated_minutes=30, created_at=datetime.utcnow())
        c2_m3_l2_res = LessonResource(id=generate_uuid(), lesson_id=c2_m3_l2.id, resource_type=ResourceType.PDF, title="Plan de mantenimiento de Gemas", external_url="https://example.com/gems-maintenance.pdf", created_at=datetime.utcnow())
        c2_m3_l3 = Lesson(id=generate_uuid(), module_id=c2_mod3.id, title="Métricas de uso y adopción de Gemas", description="Cómo medir el uso, la adopción y el impacto de tus Gemas empresariales para demostrar ROI.", sort_order=3, estimated_minutes=35, created_at=datetime.utcnow())
        c2_m3_l3_res = LessonResource(id=generate_uuid(), lesson_id=c2_m3_l3.id, resource_type=ResourceType.VIDEO, title="Métricas y ROI de Gemas", external_url="https://www.youtube.com/embed/gems_metrics_roi", duration_seconds=1800, created_at=datetime.utcnow())
        # Módulo 4: Evaluación Final (quiz-only)
        c2_mod4 = CourseModule(id=generate_uuid(), course_id=course2.id, title="Evaluación Final", sort_order=4, created_at=datetime.utcnow())
        c2_final = Lesson(id=generate_uuid(), module_id=c2_mod4.id, title="Examen Final: Gemas Personalizadas", description="Evaluación integral de todo lo aprendido sobre creación de Gemas. Debes obtener 70% para aprobar.", sort_order=1, estimated_minutes=25, created_at=datetime.utcnow())

        db.add_all([
            c2_mod1, c2_m1_l1, c2_m1_l1_res, c2_m1_l2, c2_m1_l2_res, c2_m1_l3, c2_m1_l3_res,
            c2_mod2, c2_m2_l1, c2_m2_l1_res, c2_m2_l2, c2_m2_l2_res, c2_m2_l3, c2_m2_l3_res,
            c2_mod3, c2_m3_l1, c2_m3_l1_res, c2_m3_l2, c2_m3_l2_res, c2_m3_l3, c2_m3_l3_res,
            c2_mod4, c2_final,
        ])
        db.flush()

        # ==================== COURSE 3: Gemas de Google para Ventas y CRM (2 módulos x 4 lecciones) ====================
        c3_mod1 = CourseModule(id=generate_uuid(), course_id=course3.id, title="Automatización de Propuestas Comerciales", sort_order=1, created_at=datetime.utcnow())
        c3_m1_l1 = Lesson(id=generate_uuid(), module_id=c3_mod1.id, title="Gema para generación de propuestas comerciales", description="Diseña una Gema especializada en crear propuestas personalizadas y profesionales a partir de datos del cliente.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c3_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c3_m1_l1.id, resource_type=ResourceType.VIDEO, title="Gema de propuestas comerciales", external_url="https://www.youtube.com/embed/gem_proposals", duration_seconds=2400, created_at=datetime.utcnow())
        c3_m1_l2 = Lesson(id=generate_uuid(), module_id=c3_mod1.id, title="Personalización de propuestas por sector e industria", description="Técnicas para que tu Gema adapte tono, contenido y formato según el sector del cliente objetivo.", sort_order=2, estimated_minutes=45, created_at=datetime.utcnow())
        c3_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c3_m1_l2.id, resource_type=ResourceType.PDF, title="Plantillas de propuestas por industria", external_url="https://example.com/sales-proposals-templates.pdf", created_at=datetime.utcnow())
        c3_m1_l3 = Lesson(id=generate_uuid(), module_id=c3_mod1.id, title="Seguimiento de oportunidades con Gemini", description="Usa Gemini para hacer seguimiento automatizado del pipeline de ventas y alertas de riesgo.", sort_order=3, estimated_minutes=40, created_at=datetime.utcnow())
        c3_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c3_m1_l3.id, resource_type=ResourceType.VIDEO, title="Seguimiento de pipeline con Gemini", external_url="https://www.youtube.com/embed/gem_pipeline_tracking", duration_seconds=1800, created_at=datetime.utcnow())
        c3_m1_l4 = Lesson(id=generate_uuid(), module_id=c3_mod1.id, title="Integración con Google Sheets para CRM básico", description="Conecta tu Gema de ventas con Sheets para gestionar contactos y oportunidades como un CRM ligero.", sort_order=4, estimated_minutes=55, created_at=datetime.utcnow())
        c3_m1_l4_res = LessonResource(id=generate_uuid(), lesson_id=c3_m1_l4.id, resource_type=ResourceType.VIDEO, title="CRM en Google Sheets con Gemini", external_url="https://www.youtube.com/embed/gem_sheets_crm", duration_seconds=2700, created_at=datetime.utcnow())

        c3_mod2 = CourseModule(id=generate_uuid(), course_id=course3.id, title="Análisis de Pipeline y Forecasting de Ventas", sort_order=2, created_at=datetime.utcnow())
        c3_m2_l1 = Lesson(id=generate_uuid(), module_id=c3_mod2.id, title="Gema para análisis de datos históricos de ventas", description="Construye una Gema que interprete datos históricos de ventas y detecte tendencias y patrones de mejora.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c3_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c3_m2_l1.id, resource_type=ResourceType.VIDEO, title="Análisis de ventas con Gemini", external_url="https://www.youtube.com/embed/gem_sales_analysis", duration_seconds=2400, created_at=datetime.utcnow())
        c3_m2_l2 = Lesson(id=generate_uuid(), module_id=c3_mod2.id, title="Forecasting de ventas asistido por IA", description="Genera proyecciones de ventas basadas en datos históricos, estacionalidad y factores externos con Gemini.", sort_order=2, estimated_minutes=55, created_at=datetime.utcnow())
        c3_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c3_m2_l2.id, resource_type=ResourceType.PDF, title="Metodología de forecasting con IA", external_url="https://example.com/sales-forecasting-ia.pdf", created_at=datetime.utcnow())
        c3_m2_l3 = Lesson(id=generate_uuid(), module_id=c3_mod2.id, title="Reportes automáticos para dirección comercial", description="Diseña una Gema que genere reportes ejecutivos de ventas listos para presentar a la dirección.", sort_order=3, estimated_minutes=45, created_at=datetime.utcnow())
        c3_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c3_m2_l3.id, resource_type=ResourceType.VIDEO, title="Reportes ejecutivos de ventas con Gemini", external_url="https://www.youtube.com/embed/gem_sales_reports", duration_seconds=2100, created_at=datetime.utcnow())
        c3_m2_l4 = Lesson(id=generate_uuid(), module_id=c3_mod2.id, title="Casos de éxito: Gemini en equipos de ventas", description="Análisis de empresas que han implementado exitosamente Gemini en sus equipos comerciales y lecciones aprendidas.", sort_order=4, estimated_minutes=40, created_at=datetime.utcnow())
        c3_m2_l4_res = LessonResource(id=generate_uuid(), lesson_id=c3_m2_l4.id, resource_type=ResourceType.PDF, title="Casos de éxito: Gemini en ventas", external_url="https://example.com/gemini-sales-cases.pdf", created_at=datetime.utcnow())
        db.add_all([
            c3_mod1, c3_m1_l1, c3_m1_l1_res, c3_m1_l2, c3_m1_l2_res, c3_m1_l3, c3_m1_l3_res, c3_m1_l4, c3_m1_l4_res,
            c3_mod2, c3_m2_l1, c3_m2_l1_res, c3_m2_l2, c3_m2_l2_res, c3_m2_l3, c3_m2_l3_res, c3_m2_l4, c3_m2_l4_res,
        ])
        db.flush()

        # ==================== COURSE 4: Google Workspace + Gemini para Productividad (4 módulos x 4 lecciones) ====================
        c4_mod1 = CourseModule(id=generate_uuid(), course_id=course4.id, title="Gmail con Gemini", sort_order=1, created_at=datetime.utcnow())
        c4_m1_l1 = Lesson(id=generate_uuid(), module_id=c4_mod1.id, title="Redacción inteligente de correos con Gemini", description="Usa Gemini en Gmail para redactar correos profesionales, ajustar el tono y adaptar el mensaje según el destinatario.", sort_order=1, estimated_minutes=35, created_at=datetime.utcnow())
        c4_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c4_m1_l1.id, resource_type=ResourceType.VIDEO, title="Redacción inteligente en Gmail con Gemini", external_url="https://www.youtube.com/embed/gemini_gmail_drafting", duration_seconds=1800, created_at=datetime.utcnow())
        c4_m1_l2 = Lesson(id=generate_uuid(), module_id=c4_mod1.id, title="Resumen automático de hilos de correo", description="Cómo usar Gemini para resumir cadenas largas de correo y extraer puntos clave y acciones pendientes.", sort_order=2, estimated_minutes=25, created_at=datetime.utcnow())
        c4_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c4_m1_l2.id, resource_type=ResourceType.VIDEO, title="Resumen de emails con Gemini", external_url="https://www.youtube.com/embed/gemini_gmail_summary", duration_seconds=1200, created_at=datetime.utcnow())
        c4_m1_l3 = Lesson(id=generate_uuid(), module_id=c4_mod1.id, title="Respuestas rápidas y plantillas con IA", description="Creación de plantillas inteligentes y respuestas rápidas personalizadas con Gemini en Gmail.", sort_order=3, estimated_minutes=30, created_at=datetime.utcnow())
        c4_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c4_m1_l3.id, resource_type=ResourceType.PDF, title="Biblioteca de plantillas de email con IA", external_url="https://example.com/gmail-templates-ai.pdf", created_at=datetime.utcnow())
        c4_m1_l4 = Lesson(id=generate_uuid(), module_id=c4_mod1.id, title="Gestión avanzada de bandeja de entrada con IA", description="Organiza y prioriza tu bandeja de entrada usando las capacidades de clasificación y resumen de Gemini.", sort_order=4, estimated_minutes=30, created_at=datetime.utcnow())
        c4_m1_l4_res = LessonResource(id=generate_uuid(), lesson_id=c4_m1_l4.id, resource_type=ResourceType.VIDEO, title="Inbox Zero con Gemini", external_url="https://www.youtube.com/embed/gemini_inbox_zero", duration_seconds=1800, created_at=datetime.utcnow())

        c4_mod2 = CourseModule(id=generate_uuid(), course_id=course4.id, title="Google Docs con Gemini", sort_order=2, created_at=datetime.utcnow())
        c4_m2_l1 = Lesson(id=generate_uuid(), module_id=c4_mod2.id, title="Generación de contenido en Google Docs", description="Usa el panel lateral de Gemini en Docs para generar, ampliar y estructurar contenido en tu documento.", sort_order=1, estimated_minutes=40, created_at=datetime.utcnow())
        c4_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c4_m2_l1.id, resource_type=ResourceType.VIDEO, title="Generar contenido en Docs con Gemini", external_url="https://www.youtube.com/embed/gemini_docs_content", duration_seconds=2000, created_at=datetime.utcnow())
        c4_m2_l2 = Lesson(id=generate_uuid(), module_id=c4_mod2.id, title="Revisión y corrección asistida por IA", description="Utiliza Gemini para revisar gramática, estilo, claridad y tono en documentos empresariales.", sort_order=2, estimated_minutes=30, created_at=datetime.utcnow())
        c4_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c4_m2_l2.id, resource_type=ResourceType.VIDEO, title="Revisión de documentos con Gemini", external_url="https://www.youtube.com/embed/gemini_docs_review", duration_seconds=1500, created_at=datetime.utcnow())
        c4_m2_l3 = Lesson(id=generate_uuid(), module_id=c4_mod2.id, title="Resúmenes ejecutivos automáticos", description="Genera resúmenes ejecutivos de documentos extensos con un solo prompt manteniendo los puntos clave.", sort_order=3, estimated_minutes=25, created_at=datetime.utcnow())
        c4_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c4_m2_l3.id, resource_type=ResourceType.PDF, title="Técnicas de resumen ejecutivo con IA", external_url="https://example.com/exec-summary-ai.pdf", created_at=datetime.utcnow())
        c4_m2_l4 = Lesson(id=generate_uuid(), module_id=c4_mod2.id, title="Colaboración en tiempo real con asistencia de IA", description="Mejora el trabajo colaborativo en Docs usando Gemini para sintetizar comentarios y sugerir resoluciones.", sort_order=4, estimated_minutes=35, created_at=datetime.utcnow())
        c4_m2_l4_res = LessonResource(id=generate_uuid(), lesson_id=c4_m2_l4.id, resource_type=ResourceType.VIDEO, title="Colaboración asistida por IA en Docs", external_url="https://www.youtube.com/embed/gemini_docs_collab", duration_seconds=1800, created_at=datetime.utcnow())

        c4_mod3 = CourseModule(id=generate_uuid(), course_id=course4.id, title="Google Sheets con Gemini", sort_order=3, created_at=datetime.utcnow())
        c4_m3_l1 = Lesson(id=generate_uuid(), module_id=c4_mod3.id, title="Análisis de datos con lenguaje natural", description="Haz preguntas en lenguaje natural sobre tus hojas de cálculo y obtén análisis instantáneos con Gemini.", sort_order=1, estimated_minutes=45, created_at=datetime.utcnow())
        c4_m3_l1_res = LessonResource(id=generate_uuid(), lesson_id=c4_m3_l1.id, resource_type=ResourceType.VIDEO, title="Análisis de datos en Sheets con Gemini", external_url="https://www.youtube.com/embed/gemini_sheets_nlp", duration_seconds=2100, created_at=datetime.utcnow())
        c4_m3_l2 = Lesson(id=generate_uuid(), module_id=c4_mod3.id, title="Fórmulas y macros generadas por IA", description="Pide a Gemini que cree fórmulas complejas y macros de Apps Script describiendo en palabras lo que necesitas.", sort_order=2, estimated_minutes=45, created_at=datetime.utcnow())
        c4_m3_l2_res = LessonResource(id=generate_uuid(), lesson_id=c4_m3_l2.id, resource_type=ResourceType.VIDEO, title="Fórmulas con IA en Google Sheets", external_url="https://www.youtube.com/embed/gemini_sheets_formulas", duration_seconds=2400, created_at=datetime.utcnow())
        c4_m3_l3 = Lesson(id=generate_uuid(), module_id=c4_mod3.id, title="Visualizaciones automáticas y gráficos inteligentes", description="Genera gráficos y tablas dinámicas automáticamente a partir de tus datos con la ayuda de Gemini.", sort_order=3, estimated_minutes=35, created_at=datetime.utcnow())
        c4_m3_l3_res = LessonResource(id=generate_uuid(), lesson_id=c4_m3_l3.id, resource_type=ResourceType.VIDEO, title="Visualizaciones automáticas con Gemini", external_url="https://www.youtube.com/embed/gemini_sheets_charts", duration_seconds=1800, created_at=datetime.utcnow())
        c4_m3_l4 = Lesson(id=generate_uuid(), module_id=c4_mod3.id, title="Procesamiento de grandes volúmenes de datos", description="Estrategias para usar Gemini en Sheets con datasets grandes: limpieza, transformación y análisis.", sort_order=4, estimated_minutes=50, created_at=datetime.utcnow())
        c4_m3_l4_res = LessonResource(id=generate_uuid(), lesson_id=c4_m3_l4.id, resource_type=ResourceType.PDF, title="Sheets a gran escala con Gemini", external_url="https://example.com/sheets-bigdata-gemini.pdf", created_at=datetime.utcnow())

        c4_mod4 = CourseModule(id=generate_uuid(), course_id=course4.id, title="Google Slides con Gemini", sort_order=4, created_at=datetime.utcnow())
        c4_m4_l1 = Lesson(id=generate_uuid(), module_id=c4_mod4.id, title="Generación de presentaciones desde texto", description="Crea una presentación completa en Slides a partir de un prompt o documento con Gemini generando estructura y contenido.", sort_order=1, estimated_minutes=40, created_at=datetime.utcnow())
        c4_m4_l1_res = LessonResource(id=generate_uuid(), lesson_id=c4_m4_l1.id, resource_type=ResourceType.VIDEO, title="De texto a presentación con Gemini", external_url="https://www.youtube.com/embed/gemini_slides_gen", duration_seconds=2000, created_at=datetime.utcnow())
        c4_m4_l2 = Lesson(id=generate_uuid(), module_id=c4_mod4.id, title="Diseño asistido y temas automáticos", description="Usa las sugerencias de diseño de Gemini para mejorar el aspecto visual de tus presentaciones.", sort_order=2, estimated_minutes=30, created_at=datetime.utcnow())
        c4_m4_l2_res = LessonResource(id=generate_uuid(), lesson_id=c4_m4_l2.id, resource_type=ResourceType.VIDEO, title="Diseño automático en Slides con Gemini", external_url="https://www.youtube.com/embed/gemini_slides_design", duration_seconds=1500, created_at=datetime.utcnow())
        c4_m4_l3 = Lesson(id=generate_uuid(), module_id=c4_mod4.id, title="Notas del presentador inteligentes", description="Genera speaker notes detalladas y personalizadas para cada diapositiva con Gemini.", sort_order=3, estimated_minutes=25, created_at=datetime.utcnow())
        c4_m4_l3_res = LessonResource(id=generate_uuid(), lesson_id=c4_m4_l3.id, resource_type=ResourceType.PDF, title="Guía de speaker notes con IA", external_url="https://example.com/speaker-notes-ai.pdf", created_at=datetime.utcnow())
        c4_m4_l4 = Lesson(id=generate_uuid(), module_id=c4_mod4.id, title="Presentaciones ejecutivas de alto impacto", description="Estrategias para crear presentaciones para juntas directivas usando Gemini como asistente creativo.", sort_order=4, estimated_minutes=45, created_at=datetime.utcnow())
        c4_m4_l4_res = LessonResource(id=generate_uuid(), lesson_id=c4_m4_l4.id, resource_type=ResourceType.VIDEO, title="Presentaciones ejecutivas con Gemini", external_url="https://www.youtube.com/embed/gemini_exec_slides", duration_seconds=2200, created_at=datetime.utcnow())
        # Módulo 5: Evaluación Final (quiz-only)
        c4_mod5 = CourseModule(id=generate_uuid(), course_id=course4.id, title="Evaluación Final", sort_order=5, created_at=datetime.utcnow())
        c4_final = Lesson(id=generate_uuid(), module_id=c4_mod5.id, title="Examen Final: Google Workspace + Gemini", description="Evaluación integral de productividad con Google Workspace y Gemini. Debes obtener 70% para aprobar.", sort_order=1, estimated_minutes=25, created_at=datetime.utcnow())

        db.add_all([
            c4_mod1, c4_m1_l1, c4_m1_l1_res, c4_m1_l2, c4_m1_l2_res, c4_m1_l3, c4_m1_l3_res, c4_m1_l4, c4_m1_l4_res,
            c4_mod2, c4_m2_l1, c4_m2_l1_res, c4_m2_l2, c4_m2_l2_res, c4_m2_l3, c4_m2_l3_res, c4_m2_l4, c4_m2_l4_res,
            c4_mod3, c4_m3_l1, c4_m3_l1_res, c4_m3_l2, c4_m3_l2_res, c4_m3_l3, c4_m3_l3_res, c4_m3_l4, c4_m3_l4_res,
            c4_mod4, c4_m4_l1, c4_m4_l1_res, c4_m4_l2, c4_m4_l2_res, c4_m4_l3, c4_m4_l3_res, c4_m4_l4, c4_m4_l4_res,
            c4_mod5, c4_final,
        ])
        db.flush()

        # ==================== COURSE 5: Gemas de Google para Recursos Humanos ====================
        c5_mod1 = CourseModule(id=generate_uuid(), course_id=course5.id, title="Reclutamiento Inteligente con IA", sort_order=1, created_at=datetime.utcnow())
        c5_m1_l1 = Lesson(id=generate_uuid(), module_id=c5_mod1.id, title="Gema para análisis y filtrado de CVs", description="Diseña una Gema que evalúe CVs según criterios específicos y genere un ranking de candidatos automáticamente.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c5_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c5_m1_l1.id, resource_type=ResourceType.VIDEO, title="Reclutamiento automatizado con Gemini", external_url="https://www.youtube.com/embed/gem_hr_cvs", duration_seconds=2400, created_at=datetime.utcnow())
        c5_m1_l2 = Lesson(id=generate_uuid(), module_id=c5_mod1.id, title="Redacción de ofertas de empleo con IA", description="Usa Gemini para crear ofertas de empleo atractivas, inclusivas y optimizadas para portales de empleo.", sort_order=2, estimated_minutes=40, created_at=datetime.utcnow())
        c5_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c5_m1_l2.id, resource_type=ResourceType.PDF, title="Guía de ofertas inclusivas con IA", external_url="https://example.com/job-postings-ai.pdf", created_at=datetime.utcnow())
        c5_m1_l3 = Lesson(id=generate_uuid(), module_id=c5_mod1.id, title="Preparación de entrevistas con IA", description="Genera sets de preguntas de entrevista personalizados por rol y nivel con guías de evaluación.", sort_order=3, estimated_minutes=45, created_at=datetime.utcnow())
        c5_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c5_m1_l3.id, resource_type=ResourceType.VIDEO, title="Entrevistas estructuradas con Gemini", external_url="https://www.youtube.com/embed/gem_hr_interviews", duration_seconds=2100, created_at=datetime.utcnow())

        c5_mod2 = CourseModule(id=generate_uuid(), course_id=course5.id, title="Onboarding y Capacitación con IA", sort_order=2, created_at=datetime.utcnow())
        c5_m2_l1 = Lesson(id=generate_uuid(), module_id=c5_mod2.id, title="Gema de bienvenida para nuevos colaboradores", description="Crea una Gema que responda preguntas frecuentes, guíe el onboarding y personalice la experiencia del nuevo empleado.", sort_order=1, estimated_minutes=45, created_at=datetime.utcnow())
        c5_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c5_m2_l1.id, resource_type=ResourceType.VIDEO, title="Onboarding Digital con Gemas de Gemini", external_url="https://www.youtube.com/embed/gem_hr_onboarding", duration_seconds=2100, created_at=datetime.utcnow())
        c5_m2_l2 = Lesson(id=generate_uuid(), module_id=c5_mod2.id, title="Creación de materiales de capacitación con IA", description="Genera cursos, guías, quizzes y materiales de formación interna con Gemini ahorrando tiempo al equipo de L&D.", sort_order=2, estimated_minutes=50, created_at=datetime.utcnow())
        c5_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c5_m2_l2.id, resource_type=ResourceType.PDF, title="Frameworks de capacitación con IA", external_url="https://example.com/training-frameworks-ia.pdf", created_at=datetime.utcnow())
        c5_m2_l3 = Lesson(id=generate_uuid(), module_id=c5_mod2.id, title="Evaluación de conocimientos con IA", description="Diseña evaluaciones y assessments automatizados con Gemini para medir el avance del aprendizaje.", sort_order=3, estimated_minutes=40, created_at=datetime.utcnow())
        c5_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c5_m2_l3.id, resource_type=ResourceType.VIDEO, title="Evaluaciones inteligentes con Gemini", external_url="https://www.youtube.com/embed/gem_hr_assessments", duration_seconds=1800, created_at=datetime.utcnow())

        c5_mod3 = CourseModule(id=generate_uuid(), course_id=course5.id, title="Gestión del Desempeño y Clima Laboral", sort_order=3, created_at=datetime.utcnow())
        c5_m3_l1 = Lesson(id=generate_uuid(), module_id=c5_mod3.id, title="Gema para evaluaciones de desempeño", description="Construye una Gema que ayude a redactar evaluaciones objetivas, consistentes y libres de sesgos.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c5_m3_l1_res = LessonResource(id=generate_uuid(), lesson_id=c5_m3_l1.id, resource_type=ResourceType.VIDEO, title="Evaluación de desempeño con Gemini", external_url="https://www.youtube.com/embed/gem_hr_performance", duration_seconds=2400, created_at=datetime.utcnow())
        c5_m3_l2 = Lesson(id=generate_uuid(), module_id=c5_mod3.id, title="Planes de desarrollo individual con IA", description="Genera PDIs personalizados basados en perfil y objetivos de cada colaborador con apoyo de Gemini.", sort_order=2, estimated_minutes=45, created_at=datetime.utcnow())
        c5_m3_l2_res = LessonResource(id=generate_uuid(), lesson_id=c5_m3_l2.id, resource_type=ResourceType.PDF, title="Guía de PDI con Gemini", external_url="https://example.com/pdi-gemini-guide.pdf", created_at=datetime.utcnow())
        c5_m3_l3 = Lesson(id=generate_uuid(), module_id=c5_mod3.id, title="Análisis de clima laboral con IA", description="Diseña y analiza encuestas de clima organizacional con Gemini para identificar áreas de mejora prioritarias.", sort_order=3, estimated_minutes=40, created_at=datetime.utcnow())
        c5_m3_l3_res = LessonResource(id=generate_uuid(), lesson_id=c5_m3_l3.id, resource_type=ResourceType.VIDEO, title="Clima laboral con Gemini", external_url="https://www.youtube.com/embed/gem_hr_climate", duration_seconds=1800, created_at=datetime.utcnow())
        db.add_all([
            c5_mod1, c5_m1_l1, c5_m1_l1_res, c5_m1_l2, c5_m1_l2_res, c5_m1_l3, c5_m1_l3_res,
            c5_mod2, c5_m2_l1, c5_m2_l1_res, c5_m2_l2, c5_m2_l2_res, c5_m2_l3, c5_m2_l3_res,
            c5_mod3, c5_m3_l1, c5_m3_l1_res, c5_m3_l2, c5_m3_l2_res, c5_m3_l3, c5_m3_l3_res,
        ])
        db.flush()

        # ==================== COURSE 6: Gemas de Google para Marketing Digital ====================
        c6_mod1 = CourseModule(id=generate_uuid(), course_id=course6.id, title="Creación de Contenido con IA para Marketing", sort_order=1, created_at=datetime.utcnow())
        c6_m1_l1 = Lesson(id=generate_uuid(), module_id=c6_mod1.id, title="Gema para redacción de contenido de marca", description="Diseña una Gema con la voz y tono de tu marca para generar contenido consistente para redes, blogs y campañas.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c6_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c6_m1_l1.id, resource_type=ResourceType.VIDEO, title="Contenido de marca con Gemas de Gemini", external_url="https://www.youtube.com/embed/gem_marketing_brand", duration_seconds=2400, created_at=datetime.utcnow())
        c6_m1_l2 = Lesson(id=generate_uuid(), module_id=c6_mod1.id, title="Calendarios editoriales automáticos con Gemini", description="Genera calendarios de contenido mensuales adaptados a tus objetivos, audiencia y canales de distribución.", sort_order=2, estimated_minutes=45, created_at=datetime.utcnow())
        c6_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c6_m1_l2.id, resource_type=ResourceType.PDF, title="Plantilla de calendario editorial con IA", external_url="https://example.com/editorial-calendar-ai.pdf", created_at=datetime.utcnow())
        c6_m1_l3 = Lesson(id=generate_uuid(), module_id=c6_mod1.id, title="Adaptación de contenido por canal con IA", description="Técnicas para que Gemini adapte automáticamente el mismo mensaje para LinkedIn, Instagram, email y blog.", sort_order=3, estimated_minutes=40, created_at=datetime.utcnow())
        c6_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c6_m1_l3.id, resource_type=ResourceType.VIDEO, title="Contenido multicanal con Gemini", external_url="https://www.youtube.com/embed/gem_marketing_multichannel", duration_seconds=1800, created_at=datetime.utcnow())

        c6_mod2 = CourseModule(id=generate_uuid(), course_id=course6.id, title="Análisis y Optimización de Campañas con IA", sort_order=2, created_at=datetime.utcnow())
        c6_m2_l1 = Lesson(id=generate_uuid(), module_id=c6_mod2.id, title="Gema para interpretar métricas de marketing", description="Construye una Gema que analice datos de campañas y proporcione recomendaciones accionables en lenguaje sencillo.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c6_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c6_m2_l1.id, resource_type=ResourceType.VIDEO, title="Análisis de métricas con Gemini", external_url="https://www.youtube.com/embed/gem_marketing_metrics", duration_seconds=2400, created_at=datetime.utcnow())
        c6_m2_l2 = Lesson(id=generate_uuid(), module_id=c6_mod2.id, title="Reportes de Google Analytics 4 con IA", description="Integra datos de GA4 con Gemini para generar reportes automáticos con insights y conclusiones ejecutivas.", sort_order=2, estimated_minutes=45, created_at=datetime.utcnow())
        c6_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c6_m2_l2.id, resource_type=ResourceType.PDF, title="Reportes GA4 con Gemini", external_url="https://example.com/ga4-gemini-reports.pdf", created_at=datetime.utcnow())
        c6_m2_l3 = Lesson(id=generate_uuid(), module_id=c6_mod2.id, title="Optimización de campañas en tiempo real con IA", description="Usa Gemini para analizar el rendimiento de campañas activas y sugerir ajustes en presupuesto y audiencias.", sort_order=3, estimated_minutes=45, created_at=datetime.utcnow())
        c6_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c6_m2_l3.id, resource_type=ResourceType.VIDEO, title="Optimización de campañas con Gemini", external_url="https://www.youtube.com/embed/gem_marketing_optimize", duration_seconds=2100, created_at=datetime.utcnow())
        db.add_all([
            c6_mod1, c6_m1_l1, c6_m1_l1_res, c6_m1_l2, c6_m1_l2_res, c6_m1_l3, c6_m1_l3_res,
            c6_mod2, c6_m2_l1, c6_m2_l1_res, c6_m2_l2, c6_m2_l2_res, c6_m2_l3, c6_m2_l3_res,
        ])
        db.flush()

        # ==================== COURSE 7: Google Meet y Gemini para Reuniones Efectivas ====================
        c7_mod1 = CourseModule(id=generate_uuid(), course_id=course7.id, title="Reuniones Productivas con Google Meet", sort_order=1, created_at=datetime.utcnow())
        c7_m1_l1 = Lesson(id=generate_uuid(), module_id=c7_mod1.id, title="Configuración avanzada de Google Meet para empresas", description="Opciones avanzadas: grabación en Drive, fondos corporativos, salas simultáneas y controles del anfitrión.", sort_order=1, estimated_minutes=30, created_at=datetime.utcnow())
        c7_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c7_m1_l1.id, resource_type=ResourceType.VIDEO, title="Google Meet Avanzado para Empresas", external_url="https://www.youtube.com/embed/meet_advanced_config", duration_seconds=1800, created_at=datetime.utcnow())
        c7_m1_l2 = Lesson(id=generate_uuid(), module_id=c7_mod1.id, title="Transcripciones y notas automáticas con Gemini", description="Activa y aprovecha la transcripción automática y las notas inteligentes de Gemini durante reuniones.", sort_order=2, estimated_minutes=35, created_at=datetime.utcnow())
        c7_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c7_m1_l2.id, resource_type=ResourceType.VIDEO, title="Transcripciones automáticas en Google Meet", external_url="https://www.youtube.com/embed/meet_gemini_transcripts", duration_seconds=1800, created_at=datetime.utcnow())

        c7_mod2 = CourseModule(id=generate_uuid(), course_id=course7.id, title="Documentación Post-Reunión con Gemini", sort_order=2, created_at=datetime.utcnow())
        c7_m2_l1 = Lesson(id=generate_uuid(), module_id=c7_mod2.id, title="Generación de minutas automáticas con IA", description="Usa Gemini para convertir la transcripción de una reunión en una minuta estructurada con acuerdos y responsables.", sort_order=1, estimated_minutes=35, created_at=datetime.utcnow())
        c7_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c7_m2_l1.id, resource_type=ResourceType.VIDEO, title="Minutas automáticas con Gemini", external_url="https://www.youtube.com/embed/meet_auto_minutes", duration_seconds=1800, created_at=datetime.utcnow())
        c7_m2_l2 = Lesson(id=generate_uuid(), module_id=c7_mod2.id, title="Seguimiento de acuerdos y tareas con Gemini", description="Extrae automáticamente los compromisos de una reunión y crea tareas en Google Tasks con Gemini.", sort_order=2, estimated_minutes=30, created_at=datetime.utcnow())
        c7_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c7_m2_l2.id, resource_type=ResourceType.PDF, title="Flujo de seguimiento post-reunión con IA", external_url="https://example.com/meeting-followup-ai.pdf", created_at=datetime.utcnow())
        db.add_all([
            c7_mod1, c7_m1_l1, c7_m1_l1_res, c7_m1_l2, c7_m1_l2_res,
            c7_mod2, c7_m2_l1, c7_m2_l1_res, c7_m2_l2, c7_m2_l2_res,
        ])
        db.flush()

        # ==================== COURSE 8: Google Gemini Advanced para Ejecutivos ====================
        c8_mod1 = CourseModule(id=generate_uuid(), course_id=course8.id, title="Toma de Decisiones Estratégicas con Gemini", sort_order=1, created_at=datetime.utcnow())
        c8_m1_l1 = Lesson(id=generate_uuid(), module_id=c8_mod1.id, title="Análisis de escenarios estratégicos con Gemini", description="Usa Gemini Advanced para simular escenarios de negocio, evaluar impactos y comparar alternativas estratégicas.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c8_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c8_m1_l1.id, resource_type=ResourceType.VIDEO, title="Análisis estratégico con Gemini Advanced", external_url="https://www.youtube.com/embed/gemini_exec_scenarios", duration_seconds=2400, created_at=datetime.utcnow())
        c8_m1_l2 = Lesson(id=generate_uuid(), module_id=c8_mod1.id, title="Síntesis de reportes ejecutivos con IA", description="Cómo usar Gemini para condensar informes extensos en resúmenes ejecutivos de alto impacto en minutos.", sort_order=2, estimated_minutes=35, created_at=datetime.utcnow())
        c8_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c8_m1_l2.id, resource_type=ResourceType.PDF, title="Síntesis ejecutiva con Gemini Advanced", external_url="https://example.com/exec-synthesis-gemini.pdf", created_at=datetime.utcnow())
        c8_m1_l3 = Lesson(id=generate_uuid(), module_id=c8_mod1.id, title="Evaluación de riesgos empresariales con IA", description="Metodología para usar Gemini en identificación, evaluación y priorización de riesgos corporativos.", sort_order=3, estimated_minutes=45, created_at=datetime.utcnow())
        c8_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c8_m1_l3.id, resource_type=ResourceType.VIDEO, title="Gestión de riesgos con Gemini", external_url="https://www.youtube.com/embed/gemini_exec_risk", duration_seconds=2100, created_at=datetime.utcnow())

        c8_mod2 = CourseModule(id=generate_uuid(), course_id=course8.id, title="Liderazgo y Comunicación Ejecutiva con IA", sort_order=2, created_at=datetime.utcnow())
        c8_m2_l1 = Lesson(id=generate_uuid(), module_id=c8_mod2.id, title="Gestión de equipos con Google Workspace y Gemini", description="Herramientas para liderar equipos de alto rendimiento combinando las capacidades de Workspace y Gemini.", sort_order=1, estimated_minutes=40, created_at=datetime.utcnow())
        c8_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c8_m2_l1.id, resource_type=ResourceType.VIDEO, title="Liderazgo digital con Gemini", external_url="https://www.youtube.com/embed/gemini_exec_leadership", duration_seconds=2000, created_at=datetime.utcnow())
        c8_m2_l2 = Lesson(id=generate_uuid(), module_id=c8_mod2.id, title="Dashboard ejecutivo con Google Looker Studio", description="Crea dashboards ejecutivos conectados a Google Workspace con Looker Studio para monitoreo en tiempo real.", sort_order=2, estimated_minutes=50, created_at=datetime.utcnow())
        c8_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c8_m2_l2.id, resource_type=ResourceType.VIDEO, title="Dashboard ejecutivo con Looker Studio", external_url="https://www.youtube.com/embed/gemini_exec_dashboard", duration_seconds=2400, created_at=datetime.utcnow())
        c8_m2_l3 = Lesson(id=generate_uuid(), module_id=c8_mod2.id, title="Comunicación estratégica y discursos con IA", description="Usa Gemini para preparar discursos, all-hands, comunicados y narrativas estratégicas de la dirección.", sort_order=3, estimated_minutes=40, created_at=datetime.utcnow())
        c8_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c8_m2_l3.id, resource_type=ResourceType.PDF, title="Comunicación ejecutiva asistida por IA", external_url="https://example.com/exec-comms-ai.pdf", created_at=datetime.utcnow())
        db.add_all([
            c8_mod1, c8_m1_l1, c8_m1_l1_res, c8_m1_l2, c8_m1_l2_res, c8_m1_l3, c8_m1_l3_res,
            c8_mod2, c8_m2_l1, c8_m2_l1_res, c8_m2_l2, c8_m2_l2_res, c8_m2_l3, c8_m2_l3_res,
        ])
        db.flush()

        # ==================== COURSE 9: Gemas de Google para Finanzas y Contabilidad (3 módulos x 4 lecciones) ====================
        c9_mod1 = CourseModule(id=generate_uuid(), course_id=course9.id, title="Análisis Financiero con IA", sort_order=1, created_at=datetime.utcnow())
        c9_m1_l1 = Lesson(id=generate_uuid(), module_id=c9_mod1.id, title="Gema para interpretación de estados financieros", description="Construye una Gema que analice balances, estados de resultados y flujos de caja en lenguaje ejecutivo.", sort_order=1, estimated_minutes=55, created_at=datetime.utcnow())
        c9_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c9_m1_l1.id, resource_type=ResourceType.VIDEO, title="Análisis de estados financieros con Gemini", external_url="https://www.youtube.com/embed/gem_fin_statements", duration_seconds=2700, created_at=datetime.utcnow())
        c9_m1_l2 = Lesson(id=generate_uuid(), module_id=c9_mod1.id, title="Proyecciones financieras y forecasting con Gemini", description="Usa Gemini integrado con Sheets para crear modelos de proyección financiera y escenarios de forecasting.", sort_order=2, estimated_minutes=60, created_at=datetime.utcnow())
        c9_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c9_m1_l2.id, resource_type=ResourceType.VIDEO, title="Forecasting financiero con Gemini", external_url="https://www.youtube.com/embed/gem_fin_forecast", duration_seconds=3000, created_at=datetime.utcnow())
        c9_m1_l3 = Lesson(id=generate_uuid(), module_id=c9_mod1.id, title="Detección de anomalías en datos financieros", description="Técnicas para usar Gemini en la identificación de inconsistencias, posibles fraudes y errores contables.", sort_order=3, estimated_minutes=50, created_at=datetime.utcnow())
        c9_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c9_m1_l3.id, resource_type=ResourceType.PDF, title="Auditoría de datos con Gemini", external_url="https://example.com/financial-anomaly-gemini.pdf", created_at=datetime.utcnow())
        c9_m1_l4 = Lesson(id=generate_uuid(), module_id=c9_mod1.id, title="Integración de Sheets con Gemini para finanzas", description="Configuración avanzada de Sheets para finanzas: conexión con datos externos, fórmulas IA y dashboards.", sort_order=4, estimated_minutes=55, created_at=datetime.utcnow())
        c9_m1_l4_res = LessonResource(id=generate_uuid(), lesson_id=c9_m1_l4.id, resource_type=ResourceType.VIDEO, title="Sheets financiero avanzado con Gemini", external_url="https://www.youtube.com/embed/gem_fin_sheets", duration_seconds=2700, created_at=datetime.utcnow())

        c9_mod2 = CourseModule(id=generate_uuid(), course_id=course9.id, title="Reportes y Control Interno con IA", sort_order=2, created_at=datetime.utcnow())
        c9_m2_l1 = Lesson(id=generate_uuid(), module_id=c9_mod2.id, title="Automatización de reportes financieros periódicos", description="Diseña flujos con Gemini para generar reportes mensuales, trimestrales y anuales de forma automática.", sort_order=1, estimated_minutes=55, created_at=datetime.utcnow())
        c9_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c9_m2_l1.id, resource_type=ResourceType.VIDEO, title="Reportes financieros automáticos con Gemini", external_url="https://www.youtube.com/embed/gem_fin_reports", duration_seconds=2700, created_at=datetime.utcnow())
        c9_m2_l2 = Lesson(id=generate_uuid(), module_id=c9_mod2.id, title="Gema de auditoría y control interno", description="Crea una Gema especializada en verificar cumplimiento de políticas contables y generar observaciones de auditoría.", sort_order=2, estimated_minutes=50, created_at=datetime.utcnow())
        c9_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c9_m2_l2.id, resource_type=ResourceType.PDF, title="Control interno con Gemas de Gemini", external_url="https://example.com/internal-control-gems.pdf", created_at=datetime.utcnow())
        c9_m2_l3 = Lesson(id=generate_uuid(), module_id=c9_mod2.id, title="Dashboards de KPIs financieros con Looker Studio", description="Construye dashboards de indicadores financieros clave conectados a tus datos de Workspace.", sort_order=3, estimated_minutes=55, created_at=datetime.utcnow())
        c9_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c9_m2_l3.id, resource_type=ResourceType.VIDEO, title="KPIs financieros en Looker Studio", external_url="https://www.youtube.com/embed/gem_fin_kpis_dashboard", duration_seconds=2700, created_at=datetime.utcnow())
        c9_m2_l4 = Lesson(id=generate_uuid(), module_id=c9_mod2.id, title="Presentación de resultados financieros a stakeholders", description="Usa Gemini para preparar presentaciones claras de resultados financieros para consejo y accionistas.", sort_order=4, estimated_minutes=45, created_at=datetime.utcnow())
        c9_m2_l4_res = LessonResource(id=generate_uuid(), lesson_id=c9_m2_l4.id, resource_type=ResourceType.PDF, title="Presentaciones financieras ejecutivas con IA", external_url="https://example.com/financial-stakeholder-ai.pdf", created_at=datetime.utcnow())

        c9_mod3 = CourseModule(id=generate_uuid(), course_id=course9.id, title="Control Presupuestal y Planificación Financiera", sort_order=3, created_at=datetime.utcnow())
        c9_m3_l1 = Lesson(id=generate_uuid(), module_id=c9_mod3.id, title="Seguimiento presupuestal inteligente con Gemini", description="Implementa un sistema de seguimiento presupuestal con alertas y análisis automáticos usando Gemini y Sheets.", sort_order=1, estimated_minutes=55, created_at=datetime.utcnow())
        c9_m3_l1_res = LessonResource(id=generate_uuid(), lesson_id=c9_m3_l1.id, resource_type=ResourceType.VIDEO, title="Control presupuestal con Gemini", external_url="https://www.youtube.com/embed/gem_fin_budget_tracking", duration_seconds=2700, created_at=datetime.utcnow())
        c9_m3_l2 = Lesson(id=generate_uuid(), module_id=c9_mod3.id, title="Análisis de variaciones presupuestales con IA", description="Usa Gemini para analizar desviaciones del presupuesto, identificar causas raíz y generar explicaciones ejecutivas.", sort_order=2, estimated_minutes=50, created_at=datetime.utcnow())
        c9_m3_l2_res = LessonResource(id=generate_uuid(), lesson_id=c9_m3_l2.id, resource_type=ResourceType.PDF, title="Análisis de variaciones con Gemini", external_url="https://example.com/budget-variance-ai.pdf", created_at=datetime.utcnow())
        c9_m3_l3 = Lesson(id=generate_uuid(), module_id=c9_mod3.id, title="Optimización de costos con recomendaciones de IA", description="Identifica oportunidades de reducción de costos y eficiencias operativas con el análisis de Gemini.", sort_order=3, estimated_minutes=50, created_at=datetime.utcnow())
        c9_m3_l3_res = LessonResource(id=generate_uuid(), lesson_id=c9_m3_l3.id, resource_type=ResourceType.VIDEO, title="Optimización de costos con Gemini", external_url="https://www.youtube.com/embed/gem_fin_cost_optimize", duration_seconds=2400, created_at=datetime.utcnow())
        c9_m3_l4 = Lesson(id=generate_uuid(), module_id=c9_mod3.id, title="Planificación financiera estratégica a largo plazo", description="Metodología para usar Gemini en la elaboración del plan financiero anual y proyecciones a 3-5 años.", sort_order=4, estimated_minutes=60, created_at=datetime.utcnow())
        c9_m3_l4_res = LessonResource(id=generate_uuid(), lesson_id=c9_m3_l4.id, resource_type=ResourceType.VIDEO, title="Planificación financiera con Gemini", external_url="https://www.youtube.com/embed/gem_fin_strategic_plan", duration_seconds=3000, created_at=datetime.utcnow())
        db.add_all([
            c9_mod1, c9_m1_l1, c9_m1_l1_res, c9_m1_l2, c9_m1_l2_res, c9_m1_l3, c9_m1_l3_res, c9_m1_l4, c9_m1_l4_res,
            c9_mod2, c9_m2_l1, c9_m2_l1_res, c9_m2_l2, c9_m2_l2_res, c9_m2_l3, c9_m2_l3_res, c9_m2_l4, c9_m2_l4_res,
            c9_mod3, c9_m3_l1, c9_m3_l1_res, c9_m3_l2, c9_m3_l2_res, c9_m3_l3, c9_m3_l3_res, c9_m3_l4, c9_m3_l4_res,
        ])
        db.flush()

        # ==================== COURSE 10: Seguridad y Administración de Google Workspace ====================
        c10_mod1 = CourseModule(id=generate_uuid(), course_id=course10.id, title="Administración de Google Workspace", sort_order=1, created_at=datetime.utcnow())
        c10_m1_l1 = Lesson(id=generate_uuid(), module_id=c10_mod1.id, title="Gestión de usuarios y grupos en Google Admin", description="Administra usuarios, grupos de distribución y unidades organizativas desde la consola de administración.", sort_order=1, estimated_minutes=45, created_at=datetime.utcnow())
        c10_m1_l1_res = LessonResource(id=generate_uuid(), lesson_id=c10_m1_l1.id, resource_type=ResourceType.VIDEO, title="Google Admin: Gestión de usuarios", external_url="https://www.youtube.com/embed/workspace_admin_users", duration_seconds=2100, created_at=datetime.utcnow())
        c10_m1_l2 = Lesson(id=generate_uuid(), module_id=c10_mod1.id, title="Configuración de políticas de seguridad empresarial", description="Establece políticas de contraseñas, autenticación de dos factores y DLP en Google Workspace.", sort_order=2, estimated_minutes=50, created_at=datetime.utcnow())
        c10_m1_l2_res = LessonResource(id=generate_uuid(), lesson_id=c10_m1_l2.id, resource_type=ResourceType.VIDEO, title="Políticas de seguridad en Workspace", external_url="https://www.youtube.com/embed/workspace_security_config", duration_seconds=2400, created_at=datetime.utcnow())
        c10_m1_l3 = Lesson(id=generate_uuid(), module_id=c10_mod1.id, title="Auditoría de actividad y registros de acceso", description="Usa las herramientas de auditoría de Google Workspace para monitorear actividad y generar reportes de cumplimiento.", sort_order=3, estimated_minutes=40, created_at=datetime.utcnow())
        c10_m1_l3_res = LessonResource(id=generate_uuid(), lesson_id=c10_m1_l3.id, resource_type=ResourceType.PDF, title="Guía de auditoría en Google Workspace", external_url="https://example.com/workspace-audit-guide.pdf", created_at=datetime.utcnow())

        c10_mod2 = CourseModule(id=generate_uuid(), course_id=course10.id, title="Seguridad Empresarial Avanzada con Google", sort_order=2, created_at=datetime.utcnow())
        c10_m2_l1 = Lesson(id=generate_uuid(), module_id=c10_mod2.id, title="Protección contra amenazas en Gmail y Drive", description="Configura protecciones avanzadas contra phishing, malware y exfiltración de datos en Gmail y Drive.", sort_order=1, estimated_minutes=50, created_at=datetime.utcnow())
        c10_m2_l1_res = LessonResource(id=generate_uuid(), lesson_id=c10_m2_l1.id, resource_type=ResourceType.VIDEO, title="Seguridad avanzada en Gmail y Drive", external_url="https://www.youtube.com/embed/workspace_threat_protection", duration_seconds=2400, created_at=datetime.utcnow())
        c10_m2_l2 = Lesson(id=generate_uuid(), module_id=c10_mod2.id, title="Control de acceso y gestión de identidades", description="Implementa Zero Trust con Google BeyondCorp, SSO, SAML y políticas de acceso basadas en contexto.", sort_order=2, estimated_minutes=55, created_at=datetime.utcnow())
        c10_m2_l2_res = LessonResource(id=generate_uuid(), lesson_id=c10_m2_l2.id, resource_type=ResourceType.VIDEO, title="Zero Trust con Google Workspace", external_url="https://www.youtube.com/embed/workspace_zero_trust", duration_seconds=2700, created_at=datetime.utcnow())
        c10_m2_l3 = Lesson(id=generate_uuid(), module_id=c10_mod2.id, title="Respuesta a incidentes de seguridad en Workspace", description="Procedimientos de respuesta ante incidentes: detección, contención, erradicación y recuperación.", sort_order=3, estimated_minutes=50, created_at=datetime.utcnow())
        c10_m2_l3_res = LessonResource(id=generate_uuid(), lesson_id=c10_m2_l3.id, resource_type=ResourceType.PDF, title="Playbook de incidentes en Google Workspace", external_url="https://example.com/workspace-incident-playbook.pdf", created_at=datetime.utcnow())
        db.add_all([
            c10_mod1, c10_m1_l1, c10_m1_l1_res, c10_m1_l2, c10_m1_l2_res, c10_m1_l3, c10_m1_l3_res,
            c10_mod2, c10_m2_l1, c10_m2_l1_res, c10_m2_l2, c10_m2_l2_res, c10_m2_l3, c10_m2_l3_res,
        ])
        db.flush()

            # Create enrollments for the learner users
        enrollment1 = Enrollment(
            id=generate_uuid(),
            user_id=user_learner.id,
            course_id=course1.id,
            status=EnrollmentStatus.active,
            progress_percent=0,
            created_at=datetime.utcnow(),
        )

        enrollment2 = Enrollment(
            id=generate_uuid(),
            user_id=user_learner.id,
            course_id=course2.id,
            status=EnrollmentStatus.active,
            progress_percent=0,
            created_at=datetime.utcnow(),
        )

        enrollment3 = Enrollment(
            id=generate_uuid(),
            user_id=user_learner.id,
            course_id=course3.id,
            status=EnrollmentStatus.active,
            progress_percent=0,
            created_at=datetime.utcnow(),
        )

        enrollment4 = build_completed_enrollment(
            user_id=user_learner_2.id,
            course_id=course1.id,
            started_days_ago=70,
            completion_days=2.0,
        )
        enrollment5 = build_completed_enrollment(
            user_id=user_learner_2.id,
            course_id=course2.id,
            started_days_ago=64,
            completion_days=3.0,
        )
        enrollment6 = build_completed_enrollment(
            user_id=user_learner_2.id,
            course_id=course4.id,
            started_days_ago=57,
            completion_days=1.5,
        )
        enrollment7 = build_completed_enrollment(
            user_id=user_learner_2.id,
            course_id=course7.id,
            started_days_ago=50,
            completion_days=2.5,
        )
        enrollment8 = build_completed_enrollment(
            user_id=user_learner_2.id,
            course_id=course10.id,
            started_days_ago=43,
            completion_days=3.0,
        )

        enrollment9 = build_completed_enrollment(
            user_id=user_learner_3.id,
            course_id=course1.id,
            started_days_ago=62,
            completion_days=3.5,
        )
        enrollment10 = build_completed_enrollment(
            user_id=user_learner_3.id,
            course_id=course5.id,
            started_days_ago=54,
            completion_days=3.0,
        )
        enrollment11 = build_completed_enrollment(
            user_id=user_learner_3.id,
            course_id=course8.id,
            started_days_ago=46,
            completion_days=2.5,
        )
        enrollment12 = build_completed_enrollment(
            user_id=user_learner_3.id,
            course_id=course9.id,
            started_days_ago=38,
            completion_days=4.0,
        )

        enrollment13 = build_completed_enrollment(
            user_id=user_learner_4.id,
            course_id=course2.id,
            started_days_ago=58,
            completion_days=2.0,
        )
        enrollment14 = build_completed_enrollment(
            user_id=user_learner_4.id,
            course_id=course3.id,
            started_days_ago=52,
            completion_days=2.0,
        )
        enrollment15 = build_completed_enrollment(
            user_id=user_learner_4.id,
            course_id=course4.id,
            started_days_ago=46,
            completion_days=2.0,
        )
        enrollment16 = build_completed_enrollment(
            user_id=user_learner_4.id,
            course_id=course9.id,
            started_days_ago=40,
            completion_days=2.0,
        )

        enrollment17 = build_completed_enrollment(
            user_id=user_learner_5.id,
            course_id=course3.id,
            started_days_ago=34,
            completion_days=1.5,
        )
        enrollment18 = build_completed_enrollment(
            user_id=user_learner_5.id,
            course_id=course6.id,
            started_days_ago=29,
            completion_days=2.0,
        )
        enrollment19 = build_completed_enrollment(
            user_id=user_learner_5.id,
            course_id=course7.id,
            started_days_ago=24,
            completion_days=1.5,
        )

        db.add_all([
            enrollment1,
            enrollment2,
            enrollment3,
            enrollment4,
            enrollment5,
            enrollment6,
            enrollment7,
            enrollment8,
            enrollment9,
            enrollment10,
            enrollment11,
            enrollment12,
            enrollment13,
            enrollment14,
            enrollment15,
            enrollment16,
            enrollment17,
            enrollment18,
            enrollment19,
        ])

        assignment1 = CourseAssignment(
            id=generate_uuid(),
            course_id=course4.id,
            assigned_by_user_id=user_admin.id,
            assigned_to_user_id=user_learner.id,
            due_date=datetime.utcnow() + timedelta(days=10),
            created_at=datetime.utcnow(),
        )
        assignment2 = CourseAssignment(
            id=generate_uuid(),
            course_id=course10.id,
            assigned_by_user_id=user_admin.id,
            assigned_to_user_id=user_learner.id,
            due_date=datetime.utcnow() + timedelta(days=21),
            created_at=datetime.utcnow(),
        )

        db.add_all([assignment1, assignment2])

        # ==================== BADGES ====================
        badge_gemini_explorer = Badge(
            id=generate_uuid(),
            name="Explorador Gemini",
            description="Completaste el curso de Introducción a Google Gemini para Empresas.",
            icon_url="https://thecheis.com/wp-content/uploads/2026/02/google-gemini-icon.png",
            main_color="#4285f4",
            secondary_color="#1a56db",
            created_at=datetime.utcnow(),
        )
        badge_gem_creator = Badge(
            id=generate_uuid(),
            name="Creador de Gemas",
            description="Dominaste el diseño y publicación de Gemas personalizadas en Google Gemini.",
            icon_url="https://png.pngtree.com/png-clipart/20230916/original/pngtree-cartoon-illustration-of-a-blue-treasure-chest-with-colourful-gemstones-open-png-image_12251654.png",
            main_color="#34a853",
            secondary_color="#166534",
            created_at=datetime.utcnow(),
        )
        badge_sales_agent = Badge(
            id=generate_uuid(),
            name="Agente de Ventas IA",
            description="Completaste el curso de Gemas de Google para Ventas y CRM.",
            icon_url="https://cdn3d.iconscout.com/3d/premium/thumb/etiqueta-de-precio-3d-icon-png-download-8579540.png",
            main_color="#fbbc04",
            secondary_color="#b45309",
            created_at=datetime.utcnow(),
        )
        badge_productivity = Badge(
            id=generate_uuid(),
            name="Maestro de Productividad",
            description="Dominaste Google Workspace + Gemini para Productividad.",
            icon_url="https://img.icons8.com/fluency/96/google-workspace.png",
            main_color="#ea4335",
            secondary_color="#b91c1c",
            created_at=datetime.utcnow(),
        )
        badge_hr_digital = Badge(
            id=generate_uuid(),
            name="HR Digital",
            description="Completaste el curso de Gemas de Google para Recursos Humanos.",
            icon_url="https://img.icons8.com/fluency/96/conference-call.png",
            main_color="#8b5cf6",
            secondary_color="#6d28d9",
            created_at=datetime.utcnow(),
        )
        badge_finance_gem = Badge(
            id=generate_uuid(),
            name="Analista Financiero IA",
            description="Completaste el curso de Gemas de Google para Finanzas y Contabilidad.",
            icon_url="https://img.icons8.com/fluency/96/money-bag.png",
            main_color="#10b981",
            secondary_color="#059669",
            created_at=datetime.utcnow(),
        )
        badge_early_bird = Badge(
            id=generate_uuid(),
            name="Early Adopter",
            description="Eres uno de los primeros miembros de la plataforma Nerius.",
            icon_url="https://img.icons8.com/fluency/96/rocket.png",
            main_color="#06b6d4",
            secondary_color="#0369a1",
            created_at=datetime.utcnow(),
        )
        badge_halfway = Badge(
            id=generate_uuid(),
            name="A Mitad del Camino",
            description="Alcanzaste el 50% de progreso en cualquier curso.",
            icon_url="https://img.icons8.com/fluency/96/medal-first-place.png",
            main_color="#f97316",
            secondary_color="#c2410c",
            created_at=datetime.utcnow(),
        )

        db.add_all([
            badge_gemini_explorer, badge_gem_creator, badge_sales_agent,
            badge_productivity, badge_hr_digital, badge_finance_gem,
            badge_early_bird, badge_halfway,
        ])
        db.flush()

        # Link badges to courses (with the progress % at which they're awarded)
        db.add_all([
            CourseBadge(id=generate_uuid(), course_id=course1.id, badge_id=badge_gemini_explorer.id, progress_percentage=100, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course1.id, badge_id=badge_halfway.id, progress_percentage=50, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course2.id, badge_id=badge_gem_creator.id, progress_percentage=100, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course2.id, badge_id=badge_halfway.id, progress_percentage=50, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course3.id, badge_id=badge_sales_agent.id, progress_percentage=100, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course3.id, badge_id=badge_halfway.id, progress_percentage=50, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course4.id, badge_id=badge_productivity.id, progress_percentage=100, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course4.id, badge_id=badge_halfway.id, progress_percentage=50, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course5.id, badge_id=badge_hr_digital.id, progress_percentage=100, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course9.id, badge_id=badge_finance_gem.id, progress_percentage=100, created_at=datetime.utcnow()),
            CourseBadge(id=generate_uuid(), course_id=course9.id, badge_id=badge_halfway.id, progress_percentage=50, created_at=datetime.utcnow()),
        ])
        db.flush()

        # Award badges to the learner (early adopter siempre, halfway por progreso)
        db.add_all([
            UserBadge(id=generate_uuid(), user_id=user_learner.id, badge_id=badge_early_bird.id, awarded_at=datetime.utcnow()),
            UserBadge(id=generate_uuid(), user_id=user_learner.id, badge_id=badge_halfway.id, awarded_at=datetime.utcnow()),
        ])
        db.flush()

        # Create forum posts
        forum_post1 = ForumPost(
            id=generate_uuid(),
            area_id=area_tech.id,
            author_user_id=user_learner.id,
            title="¿Cómo estructurar las instrucciones de una Gema de Gemini para soporte al cliente?",
            content="Estoy creando mi primera Gema personalizada para el equipo de atención al cliente y me surgieron varias dudas. ¿Qué tan detalladas deben ser las instrucciones del sistema? ¿Es mejor darle muchos ejemplos o confiar en la descripción del rol? Ya intenté con instrucciones cortas y la Gema pierde el contexto fácilmente. Me gustaría escuchar experiencias de quienes ya tienen Gemas en producción.",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post2 = ForumPost(
            id=generate_uuid(),
            area_id=area_tech.id,
            author_user_id=user_admin.id,
            title="Gemini en Google Sheets: ¿qué análisis les ha dado mejores resultados?",
            content="Llevamos un mes usando Gemini en Google Sheets para análisis de ventas y los resultados han superado las expectativas. Especialmente el análisis de lenguaje natural sobre nuestras tablas de datos. Pero me gustaría saber: ¿qué otros tipos de análisis han encontrado útiles? ¿Alguien lo usa para proyecciones financieras o detección de anomalías? Compartan sus casos de uso.",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post3 = ForumPost(
            id=generate_uuid(),
            area_id=area_business.id,
            author_user_id=user_super_admin.id,
            title="Gestión del cambio al adoptar Google Gemini en equipos operativos",
            content="Uno de los mayores retos al implementar Gemini en equipos operativos no es técnico, es cultural. Muchos colaboradores sienten que la IA va a reemplazar su trabajo. ¿Cómo han manejado esa percepción? En nuestra empresa hicimos talleres de co-creación donde los empleados diseñaron sus propias Gemas. Eso cambió completamente la actitud del equipo. ¿Qué estrategias han funcionado para ustedes?",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post4 = ForumPost(
            id=generate_uuid(),
            area_id=area_tech.id,
            author_user_id=user_learner.id,
            title="Comparativa: Gemini Advanced vs Microsoft Copilot para el área de IT",
            content="Estamos evaluando si migrar a Google Workspace con Gemini Advanced o seguir con Microsoft 365 y Copilot. Desde el área de IT veo ventajas en ambos lados. Gemini parece más integrado con las herramientas de Google Cloud y tiene mejor soporte para multimodal, pero Copilot tiene una integración más profunda con Teams y el ecosistema Microsoft. ¿Alguien ha hecho esta evaluación recientemente?",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        forum_post5 = ForumPost(
            id=generate_uuid(),
            area_id=area_business.id,
            author_user_id=user_admin.id,
            title="Buenas prácticas para Gemas de RRHH: privacidad y sesgo en IA",
            content="Al crear Gemas para procesos de reclutamiento y evaluación de desempeño, nos encontramos con preguntas importantes sobre privacidad y sesgo. ¿Cómo aseguran que sus Gemas de RRHH no reproduzcan sesgos en la selección de CVs? ¿Qué consideraciones de privacidad están tomando al darle a Gemini acceso a datos de empleados? Sería valioso armar una guía de buenas prácticas entre todos.",
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        db.add_all([forum_post1, forum_post2, forum_post3, forum_post4, forum_post5])
        db.flush()

        # Create forum comments
        comment1_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post1.id,
            author_user_id=user_admin.id,
            content="¡Excelente pregunta! Lo que mejor nos funcionó fue dividir las instrucciones en secciones: primero el ROL (quién es la Gema), luego el CONTEXTO (empresa, área, tono), y finalmente las RESTRICCIONES (qué no debe hacer). Con esa estructura la Gema mantiene el contexto mucho mejor. Te recomiendo también incluir 2-3 ejemplos de conversaciones ideales al final de las instrucciones.",
            created_at=datetime.utcnow(),
        )

        comment1_2 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post1.id,
            author_user_id=user_super_admin.id,
            content="Coincido con el comentario anterior. Algo que también ayuda mucho es definir cómo debe responder cuando no sabe algo. Agrega una instrucción como 'Si no tienes información suficiente, pide más contexto al usuario antes de responder'. Eso reduce mucho las alucinaciones en Gemas de soporte.",
            created_at=datetime.utcnow(),
        )

        comment2_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post2.id,
            author_user_id=user_learner.id,
            content="¡Nos ha pasado exactamente lo mismo! El caso de uso que más nos sorprendió fue pedirle a Gemini que identificara los 5 clientes con mayor riesgo de churn analizando el historial de compras directamente en lenguaje natural, sin fórmulas. ¿Cómo tienen estructurada su hoja de ventas para que Gemini la entienda mejor?",
            created_at=datetime.utcnow(),
        )

        # Respuesta al comentario
        comment2_1_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post2.id,
            author_user_id=user_admin.id,
            parent_comment_id=comment2_1.id,
            content="Buena pregunta. Nosotros usamos encabezados muy descriptivos en cada columna (en lugar de abreviaciones) y agregamos una fila de 'glosario' al inicio de la hoja con descripciones de cada campo. Gemini entiende mucho mejor el contexto así. También ayuda tener los datos limpios sin filas vacías intermedias.",
            created_at=datetime.utcnow(),
        )

        comment3_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post3.id,
            author_user_id=user_learner.id,
            content="La estrategia de co-creación que mencionas es brillante. Nosotros hemos tenido buena respuesta enmarcando las Gemas como 'asistentes' y no como 'reemplazos'. Cada colaborador tiene su propia Gema personal que ellos mismos configuran para sus tareas diarias. Eso genera un sentido de propiedad que cambia completamente la percepción.",
            created_at=datetime.utcnow(),
        )

        comment4_1 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post4.id,
            author_user_id=user_admin.id,
            content="Hicimos esa evaluación hace 6 meses. Para IT puro, Gemini tiene ventaja en integración con Google Cloud y BigQuery. Para empresas con muchos procesos en Teams y SharePoint, Copilot es difícil de desplazar. El factor decisivo para nosotros fue que ya usábamos Gmail y Drive, así que la integración nativa de Gemini fue muy superior en nuestro caso.",
            created_at=datetime.utcnow(),
        )

        comment4_2 = ForumComment(
            id=generate_uuid(),
            post_id=forum_post4.id,
            author_user_id=user_super_admin.id,
            content="Otro punto a considerar: el soporte multimodal de Gemini (texto, imagen, audio, video y código en el mismo prompt) es bastante más maduro que Copilot actualmente. Si tu área de IT maneja muchos diagramas, screenshots de errores o análisis de logs, eso puede ser determinante.",
            created_at=datetime.utcnow(),
        )

        db.add_all([
            comment1_1, comment1_2, comment2_1, comment2_1_1,
            comment3_1, comment4_1, comment4_2
        ])

        # Commit all changes
        db.commit()
        # ============================================================
        # Gem Bank seed data
        # ============================================================

        # Categories
        cat_productivity = GemCategory(
            id=generate_uuid(), name="Productividad",
            description="Gemas para mejorar tu productividad diaria",
            icon="zap", sort_order=1,
        )
        cat_analysis = GemCategory(
            id=generate_uuid(), name="Análisis de Datos",
            description="Gemas para analizar y visualizar datos",
            icon="bar-chart-2", sort_order=2,
        )
        cat_writing = GemCategory(
            id=generate_uuid(), name="Redacción",
            description="Gemas para escritura y comunicación",
            icon="pen-tool", sort_order=3,
        )
        cat_coding = GemCategory(
            id=generate_uuid(), name="Programación",
            description="Gemas para desarrollo y código",
            icon="code", sort_order=4,
        )
        cat_learning = GemCategory(
            id=generate_uuid(), name="Aprendizaje",
            description="Gemas para estudiar y aprender",
            icon="graduation-cap", sort_order=5,
        )
        cat_business = GemCategory(
            id=generate_uuid(), name="Negocios",
            description="Gemas para estrategia y gestión empresarial",
            icon="briefcase", sort_order=6,
        )
        db.add_all([cat_productivity, cat_analysis, cat_writing, cat_coding, cat_learning, cat_business])
        db.flush()

        # Tags
        tag_names = [
            "gemini", "google workspace", "productividad", "datos",
            "excel", "escritura", "código", "python", "ventas",
            "marketing", "rrhh", "finanzas", "reuniones", "presentaciones",
            "email", "reportes", "automatización", "ia",
        ]
        tags = {}
        for name in tag_names:
            t = GemTag(id=generate_uuid(), name=name)
            tags[name] = t
        db.add_all(tags.values())
        db.flush()

        # Helper to create gems
        def create_gem(title, desc, instructions, category, area, creator,
                       starters, tag_list, featured=False, extra_areas=None, gemini_url=None):
            g = Gem(
                id=generate_uuid(),
                category_id=category.id,
                area_id=area.id if area else None,
                created_by_user_id=creator.id,
                title=title,
                description=desc,
                instructions=instructions,
                gemini_url=gemini_url,
                conversation_starters=starters,
                visibility=GemVisibility.PUBLIC,
                is_featured=featured,
                status=PublicationStatus.PUBLISHED,
                usage_count=0,
            )
            db.add(g)
            db.flush()
            for tname in tag_list:
                if tname in tags:
                    db.add(GemTagLink(gem_id=g.id, tag_id=tags[tname].id))
            if extra_areas:
                for a in extra_areas:
                    db.add(GemAreaLink(gem_id=g.id, area_id=a.id))
            return g

        gem1 = create_gem(
            "Asistente de Correos Profesionales",
            "Redacta correos corporativos claros y efectivos en español",
            "Eres un experto en comunicación corporativa. Ayudas a redactar correos electrónicos profesionales, claros y concisos. Adaptas el tono según el contexto: formal para directivos, cordial para colegas, amable para clientes. Siempre sugieres un asunto efectivo y estructura el correo en saludo, cuerpo y cierre.",
            cat_writing, area_business, user_admin,
            ["Redacta un correo para solicitar una reunión", "Ayúdame a responder este correo difícil", "Escribe un correo de seguimiento"],
            ["escritura", "email", "productividad"],
            featured=True, extra_areas=[area_tech],
            gemini_url="https://gemini.google.com/gem/correos-profesionales",
        )

        gem2 = create_gem(
            "Analista de Datos con Python",
            "Analiza datasets y genera visualizaciones con Python y pandas",
            "Eres un analista de datos experto en Python, pandas, matplotlib y seaborn. Ayudas a limpiar, transformar y visualizar datos. Explicas cada paso del análisis y sugieres los gráficos más apropiados para cada tipo de dato. Siempre validas la calidad de los datos antes de analizarlos.",
            cat_analysis, area_tech, user_super_admin,
            ["Analiza este CSV y dame un resumen", "Crea un gráfico de tendencias", "Limpia estos datos duplicados"],
            ["datos", "python", "ia"],
            featured=True,
            gemini_url="https://gemini.google.com/gem/analista-datos-python",
        )

        gem3 = create_gem(
            "Coach de Presentaciones",
            "Diseña y mejora presentaciones ejecutivas impactantes",
            "Eres un coach de presentaciones ejecutivas. Ayudas a estructurar presentaciones con storytelling, datos clave y visuales claros. Sugieres la cantidad ideal de slides, el orden de los temas y cómo hacer transiciones efectivas. Tu objetivo es que cada presentación sea memorable y orientada a resultados.",
            cat_business, area_business, user_admin,
            ["Ayúdame a estructurar mi presentación trimestral", "¿Cómo puedo hacer más impactante esta slide?", "Resume estos datos para una presentación"],
            ["presentaciones", "productividad"],
            featured=True,
            gemini_url="https://gemini.google.com/gem/coach-presentaciones",
        )

        gem4 = create_gem(
            "Asistente de Google Sheets",
            "Crea fórmulas, macros y automatizaciones en Google Sheets",
            "Eres un experto en Google Sheets. Dominas fórmulas avanzadas (QUERY, ARRAYFORMULA, IMPORTRANGE), tablas dinámicas, formato condicional y Apps Script. Explicas cada fórmula paso a paso y ofreces alternativas cuando hay varias soluciones posibles.",
            cat_productivity, area_tech, user_super_admin,
            ["Necesito una fórmula para consolidar datos", "Crea un dashboard automático", "Automatiza este reporte semanal"],
            ["google workspace", "productividad", "automatización", "datos"],
            featured=True, extra_areas=[area_business],
            gemini_url="https://gemini.google.com/gem/google-sheets-experto",
        )

        gem5 = create_gem(
            "Tutor de Gemini para Principiantes",
            "Aprende a usar Google Gemini desde cero paso a paso",
            "Eres un tutor paciente y claro que enseña a usar Google Gemini desde nivel básico. Explicas conceptos de IA generativa de forma sencilla, con ejemplos prácticos del día a día laboral. Guías al usuario con ejercicios progresivos y celebras sus avances.",
            cat_learning, None, user_admin,
            ["¿Qué es Google Gemini y para qué sirve?", "Enséñame a hacer mi primer prompt", "¿Cómo creo una gema personalizada?"],
            ["gemini", "ia", "productividad"],
            featured=True, extra_areas=[area_tech, area_business],
            gemini_url="https://gemini.google.com/gem/tutor-gemini-principiantes",
        )

        gem6 = create_gem(
            "Generador de Reportes Ejecutivos",
            "Transforma datos crudos en reportes ejecutivos claros",
            "Eres un experto en reportes ejecutivos. Transformas datos crudos y métricas en informes claros, con resumen ejecutivo, hallazgos clave, gráficos sugeridos y recomendaciones accionables. Usas lenguaje de negocios y priorizas la información más relevante para la toma de decisiones.",
            cat_business, area_business, user_admin,
            ["Convierte estos datos en un reporte", "Escribe un resumen ejecutivo", "¿Qué KPIs debería incluir?"],
            ["reportes", "datos", "productividad"],
        )

        gem7 = create_gem(
            "Asistente de Código Python",
            "Escribe, depura y optimiza código Python",
            "Eres un desarrollador Python senior. Ayudas a escribir código limpio, eficiente y bien documentado. Sigues PEP 8, sugieres patrones de diseño apropiados y explicas la complejidad algorítmica. Cuando depuras, analizas el error paso a paso antes de proponer la solución.",
            cat_coding, area_tech, user_super_admin,
            ["Revisa este código y sugiere mejoras", "¿Cómo implemento esto en Python?", "Ayúdame a depurar este error"],
            ["código", "python"],
        )

        gem8 = create_gem(
            "Planificador de Reuniones Efectivas",
            "Estructura reuniones productivas con agenda y seguimiento",
            "Eres un facilitador de reuniones experto. Ayudas a crear agendas efectivas, definir objetivos claros, asignar tiempos y roles. Después de la reunión, generas minutas estructuradas con acuerdos, responsables y fechas. Tu meta es que cada reunión tenga un propósito claro y resultados medibles.",
            cat_productivity, area_business, user_admin,
            ["Crea una agenda para mi reunión semanal", "Genera la minuta de esta reunión", "¿Cómo hago reuniones más cortas?"],
            ["reuniones", "productividad", "google workspace"],
            extra_areas=[area_tech],
        )

        gem9 = create_gem(
            "Estratega de Marketing Digital",
            "Diseña estrategias de marketing y campañas digitales",
            "Eres un estratega de marketing digital con experiencia en SEO, SEM, redes sociales y email marketing. Ayudas a diseñar campañas, analizar métricas de rendimiento y optimizar el ROI. Conoces las mejores prácticas de cada canal y adaptas las estrategias al presupuesto disponible.",
            cat_business, area_business, user_admin,
            ["Diseña una campaña para este producto", "Analiza estas métricas de marketing", "¿Cómo mejoro mi SEO?"],
            ["marketing", "datos", "ia"],
        )

        gem10 = create_gem(
            "Asistente de Onboarding RRHH",
            "Guía procesos de onboarding y gestión de talento",
            "Eres un especialista en recursos humanos y onboarding. Ayudas a diseñar procesos de bienvenida para nuevos empleados, crear checklists, planificar la primera semana y generar materiales de inducción. Conoces las mejores prácticas para retención de talento y cultura organizacional.",
            cat_business, area_business, user_admin,
            ["Crea un plan de onboarding de 30 días", "¿Qué documentos necesito para un nuevo ingreso?", "Diseña una encuesta de clima laboral"],
            ["rrhh", "productividad"],
        )

        db.flush()

        # Associate some gems with courses (use first course available)
        # Associate gems with courses
        db.add(CourseGem(id=generate_uuid(), course_id=course1.id, gem_id=gem5.id, sort_order=0))
        db.add(CourseGem(id=generate_uuid(), course_id=course1.id, gem_id=gem4.id, sort_order=1))
        db.add(CourseGem(id=generate_uuid(), course_id=course2.id, gem_id=gem1.id, sort_order=0))
        db.add(CourseGem(id=generate_uuid(), course_id=course2.id, gem_id=gem7.id, sort_order=1))
        db.add(CourseGem(id=generate_uuid(), course_id=course3.id, gem_id=gem9.id, sort_order=0))

        # Save some gems to learner's collection
        db.add(UserGemCollection(id=generate_uuid(), user_id=user_learner.id, gem_id=gem1.id))
        db.add(UserGemCollection(id=generate_uuid(), user_id=user_learner.id, gem_id=gem4.id))
        db.add(UserGemCollection(id=generate_uuid(), user_id=user_learner.id, gem_id=gem5.id))

        db.flush()

        # ============================================================
        # Quizzes seed data
        # ============================================================

        # Get first lesson of course1 (Introducción a Google Gemini) for quiz
        first_lesson = db.query(Lesson).join(CourseModule).filter(
            CourseModule.course_id == course1.id
        ).order_by(CourseModule.sort_order, Lesson.sort_order).first()

        if first_lesson:
            quiz1 = Quiz(
                id=generate_uuid(),
                lesson_id=first_lesson.id,
                title="Evaluación: Conceptos Básicos de Gemini",
                description="Verifica tu comprensión de los conceptos fundamentales de Google Gemini",
                passing_score=70,
                max_attempts=3,
                time_limit_seconds=600,
                is_required=True,
            )
            db.add(quiz1)
            db.flush()

            # Question 1: Multiple Choice
            q1 = QuizQuestion(
                id=generate_uuid(), quiz_id=quiz1.id,
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="¿Qué es Google Gemini?",
                explanation="Google Gemini es un modelo de inteligencia artificial multimodal desarrollado por Google DeepMind.",
                points=2, sort_order=1,
            )
            db.add(q1)
            db.flush()
            for i, (text, correct) in enumerate([
                ("Un motor de búsqueda", False),
                ("Un modelo de IA multimodal de Google", True),
                ("Un sistema operativo", False),
                ("Una red social", False),
            ], 1):
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q1.id, option_text=text, is_correct=correct, sort_order=i))

            # Question 2: True/False
            q2 = QuizQuestion(
                id=generate_uuid(), quiz_id=quiz1.id,
                question_type=QuestionType.TRUE_FALSE,
                question_text="Google Gemini puede procesar texto, imágenes y audio simultáneamente.",
                explanation="Correcto. Gemini es multimodal, lo que significa que puede entender y generar diferentes tipos de contenido.",
                points=1, sort_order=2,
            )
            db.add(q2)
            db.flush()
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2.id, option_text="Verdadero", is_correct=True, sort_order=1))
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2.id, option_text="Falso", is_correct=False, sort_order=2))

            # Question 3: Multiple Choice
            q3 = QuizQuestion(
                id=generate_uuid(), quiz_id=quiz1.id,
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="¿Cuál es la ventaja principal de usar Gemas personalizadas en Gemini?",
                explanation="Las Gemas permiten crear asistentes especializados con instrucciones personalizadas para tareas específicas.",
                points=2, sort_order=3,
            )
            db.add(q3)
            db.flush()
            for i, (text, correct) in enumerate([
                ("Reducen el costo de la suscripción", False),
                ("Permiten crear asistentes especializados para tareas específicas", True),
                ("Aumentan la velocidad de internet", False),
                ("Reemplazan completamente al equipo de trabajo", False),
            ], 1):
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q3.id, option_text=text, is_correct=correct, sort_order=i))

            # Question 4: Short Answer
            q4 = QuizQuestion(
                id=generate_uuid(), quiz_id=quiz1.id,
                question_type=QuestionType.SHORT_ANSWER,
                question_text="Menciona un caso de uso de Google Gemini en el ámbito empresarial.",
                explanation="Algunos ejemplos incluyen: análisis de datos, redacción de documentos, atención al cliente automatizada, generación de reportes, etc.",
                points=2, sort_order=4,
            )
            db.add(q4)

            # Question 5: True/False
            q5 = QuizQuestion(
                id=generate_uuid(), quiz_id=quiz1.id,
                question_type=QuestionType.TRUE_FALSE,
                question_text="Las Gemas de Gemini requieren conocimientos avanzados de programación para configurarse.",
                explanation="Falso. Las Gemas se configuran mediante instrucciones en lenguaje natural, no requieren programación.",
                points=1, sort_order=5,
            )
            db.add(q5)
            db.flush()
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q5.id, option_text="Verdadero", is_correct=False, sort_order=1))
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q5.id, option_text="Falso", is_correct=True, sort_order=2))

        # ── Quiz 2: Curso 2 — Creación de Gemas (last lesson of module 2) ──
        # Uses ordering + matching + multiple_choice
        c2_last_lesson = c2_m2_l3  # "Pruebas y refinamiento iterativo de Gemas"
        quiz2 = Quiz(
            id=generate_uuid(),
            lesson_id=c2_last_lesson.id,
            title="Evaluación: Creación de Gemas Personalizadas",
            description="Demuestra tu dominio en la creación y refinamiento de Gemas de Gemini",
            passing_score=60,
            max_attempts=5,
            time_limit_seconds=900,
            is_required=True,
        )
        db.add(quiz2)
        db.flush()

        # Q1: Ordering — pasos para crear una gema
        q2_1 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz2.id,
            question_type=QuestionType.ORDERING,
            question_text="Ordena los pasos correctos para crear una Gema personalizada:",
            explanation="El orden correcto es: definir objetivo → escribir instrucciones → probar con ejemplos → refinar iterativamente.",
            points=3, sort_order=1,
        )
        db.add(q2_1)
        db.flush()
        for i, text in enumerate([
            "Definir el objetivo y rol de la Gema",
            "Escribir las instrucciones del sistema",
            "Probar la Gema con ejemplos reales",
            "Refinar iterativamente según resultados",
        ], 1):
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2_1.id, option_text=text, is_correct=True, sort_order=i))

        # Q2: Matching — emparejar conceptos con definiciones
        q2_2 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz2.id,
            question_type=QuestionType.MATCHING,
            question_text="Empareja cada componente de una Gema con su descripción:",
            explanation="Cada componente tiene una función específica en la configuración de la Gema.",
            points=4, sort_order=2,
        )
        db.add(q2_2)
        db.flush()
        for i, (text, target) in enumerate([
            ("Instrucciones del sistema", "Define el comportamiento y personalidad de la Gema"),
            ("Conversation starters", "Sugerencias iniciales para el usuario"),
            ("Nombre de la Gema", "Identificador visible para los usuarios"),
            ("Contexto empresarial", "Información específica del negocio que la Gema debe conocer"),
        ], 1):
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2_2.id, option_text=text, is_correct=True, sort_order=i, match_target=target))

        # Q3: Multiple Choice
        q2_3 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz2.id,
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="¿Cuál es la mejor práctica al escribir instrucciones para una Gema?",
            explanation="Las instrucciones deben ser específicas y con ejemplos concretos para obtener respuestas consistentes.",
            points=2, sort_order=3,
        )
        db.add(q2_3)
        db.flush()
        for i, (text, correct) in enumerate([
            ("Escribir instrucciones lo más cortas posible", False),
            ("Ser específico, incluir ejemplos y definir el tono de respuesta", True),
            ("Dejar las instrucciones vacías para mayor flexibilidad", False),
            ("Copiar instrucciones de otras Gemas sin adaptarlas", False),
        ], 1):
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2_3.id, option_text=text, is_correct=correct, sort_order=i))

        # Q4: True/False
        q2_4 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz2.id,
            question_type=QuestionType.TRUE_FALSE,
            question_text="Una Gema puede ser compartida con todo el equipo a través de Google Workspace.",
            explanation="Correcto. Las Gemas pueden ser públicas, privadas o compartidas con equipos específicos dentro de Workspace.",
            points=1, sort_order=4,
        )
        db.add(q2_4)
        db.flush()
        db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2_4.id, option_text="Verdadero", is_correct=True, sort_order=1))
        db.add(QuizQuestionOption(id=generate_uuid(), question_id=q2_4.id, option_text="Falso", is_correct=False, sort_order=2))

        # ── Quiz 3: Curso 3 — Ventas y CRM (last lesson of module 1) ──
        c3_quiz_lesson = c3_m1_l4  # "Integración con Google Sheets para CRM básico"
        quiz3 = Quiz(
            id=generate_uuid(),
            lesson_id=c3_quiz_lesson.id,
            title="Evaluación: Gemas para Ventas y CRM",
            description="Evalúa tu conocimiento sobre el uso de Gemas de Gemini para ventas",
            passing_score=70,
            max_attempts=3,
            time_limit_seconds=None,  # Sin límite de tiempo
            is_required=True,
        )
        db.add(quiz3)
        db.flush()

        # Q1: Multiple Choice
        q3_1 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz3.id,
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="¿Qué función de Google Sheets es más útil para conectar datos de CRM con Gemini?",
            explanation="IMPORTRANGE permite importar datos de otras hojas y QUERY permite consultar y filtrar datos, ambas esenciales para CRM.",
            points=2, sort_order=1,
        )
        db.add(q3_1)
        db.flush()
        for i, (text, correct) in enumerate([
            ("CONCATENATE y TRIM", False),
            ("IMPORTRANGE y QUERY", True),
            ("SUM y AVERAGE", False),
            ("VLOOKUP solamente", False),
        ], 1):
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q3_1.id, option_text=text, is_correct=correct, sort_order=i))

        # Q2: Ordering — pipeline de ventas
        q3_2 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz3.id,
            question_type=QuestionType.ORDERING,
            question_text="Ordena las etapas del pipeline de ventas asistido por Gemini:",
            explanation="El pipeline correcto sigue: prospección → calificación → propuesta → negociación → cierre.",
            points=3, sort_order=2,
        )
        db.add(q3_2)
        db.flush()
        for i, text in enumerate([
            "Prospección de clientes potenciales",
            "Calificación de leads con IA",
            "Generación de propuesta personalizada",
            "Negociación y seguimiento",
            "Cierre y documentación",
        ], 1):
            db.add(QuizQuestionOption(id=generate_uuid(), question_id=q3_2.id, option_text=text, is_correct=True, sort_order=i))

        # Q3: Short Answer
        q3_3 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz3.id,
            question_type=QuestionType.SHORT_ANSWER,
            question_text="Describe una ventaja de usar una Gema de Gemini para generar propuestas comerciales en lugar de hacerlas manualmente.",
            explanation="Las Gemas pueden personalizar propuestas automáticamente según datos del cliente, ahorrando tiempo y mejorando la consistencia.",
            points=2, sort_order=3,
        )
        db.add(q3_3)

        # Q4: True/False
        q3_4 = QuizQuestion(
            id=generate_uuid(), quiz_id=quiz3.id,
            question_type=QuestionType.TRUE_FALSE,
            question_text="Google Sheets puede funcionar como un CRM básico cuando se combina con Gemas de Gemini.",
            explanation="Verdadero. Con fórmulas avanzadas y la asistencia de Gemini, Sheets puede gestionar contactos, oportunidades y seguimientos.",
            points=1, sort_order=4,
        )
        db.add(q3_4)
        db.flush()
        db.add(QuizQuestionOption(id=generate_uuid(), question_id=q3_4.id, option_text="Verdadero", is_correct=True, sort_order=1))
        db.add(QuizQuestionOption(id=generate_uuid(), question_id=q3_4.id, option_text="Falso", is_correct=False, sort_order=2))

        db.flush()

        # ── Quiz Final: Curso 1 — Introducción a Google Gemini ──
        quiz_final_c1 = Quiz(
            id=generate_uuid(), lesson_id=c1_final.id,
            title="Examen Final: Google Gemini para Empresas",
            description="Evaluación integral que cubre todos los módulos del curso. Aprueba con 70% para completar el curso.",
            passing_score=70, max_attempts=3, time_limit_seconds=1200, is_required=True,
        )
        db.add(quiz_final_c1)
        db.flush()

        for sort, (qtype, text, explanation, opts) in enumerate([
            (QuestionType.MULTIPLE_CHOICE, "¿Cuál de las siguientes NO es una capacidad de Google Gemini?",
             "Gemini es multimodal (texto, imagen, audio, video) pero no puede ejecutar transacciones bancarias directamente.",
             [("Generar texto a partir de imágenes", False), ("Resumir documentos largos", False),
              ("Ejecutar transacciones bancarias automáticas", True), ("Analizar datos en hojas de cálculo", False)]),
            (QuestionType.TRUE_FALSE, "Gemini en Google Workspace tiene acceso a los datos empresariales del usuario con las mismas políticas de privacidad que el resto de Workspace.",
             "Verdadero. Gemini en Workspace opera bajo las mismas políticas de privacidad y cumplimiento.", None),
            (QuestionType.MULTIPLE_CHOICE, "¿Qué técnica de prompting produce mejores resultados en Gemini?",
             "Dar contexto, ser específico y proporcionar ejemplos produce respuestas más precisas y útiles.",
             [("Escribir prompts lo más cortos posible", False), ("Dar contexto, ser específico y dar ejemplos", True),
              ("Usar solo palabras clave sin oraciones", False), ("Repetir la misma pregunta varias veces", False)]),
            (QuestionType.MATCHING, "Empareja cada aplicación de Google Workspace con su principal beneficio al integrar Gemini:",
             "Cada aplicación tiene capacidades específicas de IA.",
             [("Gmail", "Redacción y resumen de correos"), ("Google Docs", "Generación y revisión de contenido"),
              ("Google Sheets", "Análisis de datos con lenguaje natural"), ("Google Slides", "Creación automática de presentaciones")]),
            (QuestionType.ORDERING, "Ordena los pasos recomendados para implementar Gemini en una empresa:",
             "La implementación gradual asegura mejor adopción.",
             ["Evaluar necesidades del equipo", "Configurar Gemini en Workspace", "Capacitar al equipo con casos de uso",
              "Medir resultados y optimizar"]),
            (QuestionType.SHORT_ANSWER, "¿Qué consideración ética es más importante al usar Gemini con datos de clientes?",
             "La privacidad, el consentimiento y la transparencia sobre el uso de IA son fundamentales.", None),
        ], 1):
            q = QuizQuestion(id=generate_uuid(), quiz_id=quiz_final_c1.id, question_type=qtype,
                             question_text=text, explanation=explanation, points=2, sort_order=sort)
            db.add(q)
            db.flush()
            if qtype == QuestionType.MULTIPLE_CHOICE and opts:
                for i, (ot, oc) in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=oc, sort_order=i))
            elif qtype == QuestionType.TRUE_FALSE:
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text="Verdadero", is_correct=True, sort_order=1))
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text="Falso", is_correct=False, sort_order=2))
            elif qtype == QuestionType.MATCHING and opts:
                for i, (ot, mt) in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=True, sort_order=i, match_target=mt))
            elif qtype == QuestionType.ORDERING and opts:
                for i, ot in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=True, sort_order=i))

        # ── Quiz Final: Curso 2 — Creación de Gemas Personalizadas ──
        quiz_final_c2 = Quiz(
            id=generate_uuid(), lesson_id=c2_final.id,
            title="Examen Final: Gemas Personalizadas",
            description="Demuestra tu dominio en diseño, creación y gestión de Gemas de Google Gemini.",
            passing_score=70, max_attempts=3, time_limit_seconds=1200, is_required=True,
        )
        db.add(quiz_final_c2)
        db.flush()

        for sort, (qtype, text, explanation, opts) in enumerate([
            (QuestionType.ORDERING, "Ordena el ciclo completo de vida de una Gema empresarial:",
             "Una Gema exitosa pasa por diseño, desarrollo, prueba, publicación y mantenimiento continuo.",
             ["Identificar necesidad del equipo", "Diseñar instrucciones del sistema", "Probar con usuarios reales",
              "Publicar y compartir", "Monitorear uso y actualizar"]),
            (QuestionType.MULTIPLE_CHOICE, "¿Qué elemento es MÁS crítico en las instrucciones del sistema de una Gema?",
             "Un rol claro y contexto específico son la base de instrucciones efectivas.",
             [("El nombre de la Gema", False), ("El rol y contexto específico del asistente", True),
              ("La cantidad de palabras", False), ("El idioma de las instrucciones", False)]),
            (QuestionType.MATCHING, "Relaciona cada tipo de Gema con su mejor caso de uso:",
             "Cada tipo tiene ventajas específicas según el contexto.",
             [("Gema privada", "Uso personal o prototipos"), ("Gema de equipo", "Procesos departamentales"),
              ("Gema pública", "Recursos compartidos con toda la organización")]),
            (QuestionType.TRUE_FALSE, "Es recomendable actualizar las instrucciones de una Gema cada vez que cambian los procesos del equipo.",
             "Verdadero. Las Gemas deben mantenerse alineadas con los procesos actuales para ser efectivas.", None),
            (QuestionType.SHORT_ANSWER, "Describe cómo medirías el éxito de una Gema empresarial desplegada en tu equipo.",
             "Se puede medir por adopción (usuarios activos), satisfacción, tiempo ahorrado y calidad de los resultados.", None),
        ], 1):
            q = QuizQuestion(id=generate_uuid(), quiz_id=quiz_final_c2.id, question_type=qtype,
                             question_text=text, explanation=explanation, points=2, sort_order=sort)
            db.add(q)
            db.flush()
            if qtype == QuestionType.MULTIPLE_CHOICE and opts:
                for i, (ot, oc) in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=oc, sort_order=i))
            elif qtype == QuestionType.TRUE_FALSE:
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text="Verdadero", is_correct=True, sort_order=1))
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text="Falso", is_correct=False, sort_order=2))
            elif qtype == QuestionType.MATCHING and opts:
                for i, (ot, mt) in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=True, sort_order=i, match_target=mt))
            elif qtype == QuestionType.ORDERING and opts:
                for i, ot in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=True, sort_order=i))

        # ── Quiz Final: Curso 4 — Google Workspace + Gemini ──
        quiz_final_c4 = Quiz(
            id=generate_uuid(), lesson_id=c4_final.id,
            title="Examen Final: Google Workspace + Gemini",
            description="Evaluación integral sobre el uso de Gemini en Gmail, Docs, Sheets y Slides.",
            passing_score=70, max_attempts=3, time_limit_seconds=1500, is_required=True,
        )
        db.add(quiz_final_c4)
        db.flush()

        for sort, (qtype, text, explanation, opts) in enumerate([
            (QuestionType.MATCHING, "Empareja cada funcionalidad de Gemini con la app de Workspace donde se usa:",
             "Cada app de Workspace tiene integraciones específicas de Gemini.",
             [("Redacción inteligente de correos", "Gmail"), ("Fórmulas con lenguaje natural", "Sheets"),
              ("Resúmenes ejecutivos de documentos", "Docs"), ("Speaker notes automáticas", "Slides")]),
            (QuestionType.MULTIPLE_CHOICE, "¿Cuál es la ventaja principal de usar Gemini en Google Sheets?",
             "Sheets + Gemini permite hacer análisis de datos usando preguntas en lenguaje natural.",
             [("Cambiar colores de las celdas automáticamente", False), ("Analizar datos usando lenguaje natural", True),
              ("Reemplazar Excel completamente", False), ("Enviar hojas por correo automáticamente", False)]),
            (QuestionType.ORDERING, "Ordena el flujo de trabajo para crear una presentación ejecutiva con Gemini:",
             "El flujo óptimo empieza con el contenido y termina con el ensayo.",
             ["Redactar el contenido en Docs con Gemini", "Generar la presentación en Slides", "Agregar speaker notes con IA",
              "Revisar y ajustar el diseño", "Ensayar con las notas generadas"]),
            (QuestionType.TRUE_FALSE, "Gemini puede generar gráficos automáticamente en Google Sheets a partir de datos existentes.",
             "Verdadero. Gemini analiza los datos y sugiere las visualizaciones más apropiadas.", None),
            (QuestionType.MULTIPLE_CHOICE, "¿Qué técnica es MÁS efectiva para resumir hilos largos de correo en Gmail con Gemini?",
             "Pedir un resumen con puntos de acción produce los resultados más útiles.",
             [("Reenviar el hilo a otro correo", False), ("Pedir un resumen con puntos de acción específicos", True),
              ("Leer cada correo individualmente", False), ("Usar solo el buscador de Gmail", False)]),
            (QuestionType.SHORT_ANSWER, "¿Cómo usarías Gemini en Google Docs para mejorar un documento que tiene problemas de claridad y tono?",
             "Se puede pedir a Gemini que revise el tono, simplifique el lenguaje y sugiera una estructura más clara.", None),
        ], 1):
            q = QuizQuestion(id=generate_uuid(), quiz_id=quiz_final_c4.id, question_type=qtype,
                             question_text=text, explanation=explanation, points=2, sort_order=sort)
            db.add(q)
            db.flush()
            if qtype == QuestionType.MULTIPLE_CHOICE and opts:
                for i, (ot, oc) in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=oc, sort_order=i))
            elif qtype == QuestionType.TRUE_FALSE:
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text="Verdadero", is_correct=True, sort_order=1))
                db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text="Falso", is_correct=False, sort_order=2))
            elif qtype == QuestionType.MATCHING and opts:
                for i, (ot, mt) in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=True, sort_order=i, match_target=mt))
            elif qtype == QuestionType.ORDERING and opts:
                for i, ot in enumerate(opts, 1):
                    db.add(QuizQuestionOption(id=generate_uuid(), question_id=q.id, option_text=ot, is_correct=True, sort_order=i))

        db.flush()

        # ============================================================
        # Certifications seed data
        # ============================================================

        cert1 = CourseCertification(
            id=generate_uuid(),
            course_id=course1.id,
            title="Certificación en Google Gemini para Empresas",
            description="Certifica tus conocimientos en el uso de Google Gemini en entornos empresariales. Válida por 1 año.",
            cost=50.00,
            validity_days=365,
        )
        db.add(cert1)

        cert2 = CourseCertification(
            id=generate_uuid(),
            course_id=course2.id,
            title="Certificación en Gemas Personalizadas de Gemini",
            description="Certifica tu capacidad de crear, configurar y administrar Gemas de Google Gemini. Válida por 1 año.",
            cost=50.00,
            validity_days=365,
        )
        db.add(cert2)

        cert3 = CourseCertification(
            id=generate_uuid(),
            course_id=course4.id,
            title="Certificación en Google Workspace + Gemini",
            description="Certifica tu dominio de Gemini integrado con Gmail, Docs, Sheets y Slides. Válida por 1 año.",
            cost=50.00,
            validity_days=365,
        )
        db.add(cert3)

        # ============================================================
        # Course Access Grants seed data
        # ============================================================

        # Grant learner access to all courses (all are free by default, but demo the grants)
        for c in [course1, course2, course3, course4, course5]:
            db.add(UserCourseGrant(
                id=generate_uuid(),
                user_id=user_learner.id,
                course_id=c.id,
                granted_by_user_id=user_admin.id,
            ))

        db.flush()
        db.commit()

        print("✓ Database seeded successfully!")
        print("\n📝 Mock Users Created:")
        print("  - Super Admin: superadmin@example.com (password: password123)")
        print("  - Content Admin: admin@example.com (password: password123)")
        print("  - Content Editor: editor@example.com (password: password123)")
        print("  - Content Viewer: viewer@example.com (password: password123)")
        print("  - Learner: user@example.com (password: password123)")
        print("  - Learner: diego.herrera@example.com (password: password123)")
        print("  - Learner: maria.gomez@example.com (password: password123)")
        print("  - Learner: luis.torres@example.com (password: password123)")
        print("  - Learner: sofia.ramirez@example.com (password: password123)")
        print("\n📚 Cursos Creados:")
        print("  - Introducción a Google Gemini para Empresas (3 módulos, 9 lecciones)")
        print("  - Creación de Gemas Personalizadas en Google Gemini (3 módulos, 9 lecciones)")
        print("  - Gemas de Google para Ventas y CRM (2 módulos x 4 lecciones)")
        print("  - Google Workspace + Gemini para Productividad (4 módulos x 4 lecciones)")
        print("  - Gemas de Google para Recursos Humanos (3 módulos, 9 lecciones)")
        print("  - Gemas de Google para Marketing Digital (2 módulos, 6 lecciones)")
        print("  - Google Meet y Gemini para Reuniones Efectivas (2 módulos, 4 lecciones)")
        print("  - Google Gemini Advanced para Ejecutivos (2 módulos, 6 lecciones)")
        print("  - Gemas de Google para Finanzas y Contabilidad (3 módulos x 4 lecciones)")
        print("  - Seguridad y Administración de Google Workspace (2 módulos, 6 lecciones)")
        print("\n💬 Mock Forum Posts Created:")
        print("  - 5 forum posts with comments")
        print("\n📌 Mock Course Assignments Created:")
        print("  - 2 cursos asignados a user@example.com")
        print("\n� Mock Badges Created:")
        print("  - 7 badges (5 por completar cursos, 1 early bird, 1 halfway)")
        print("  - 8 relaciones curso-badge con porcentajes de obtención")
        print("  - 2 badges otorgados al learner")
        print("\n💎 Mock Gem Bank Created:")
        print("  - 6 categorías, 18 tags, 10 gemas (5 destacadas)")
        print("  - 3 gemas guardadas en colección del learner")
        print("  - Gemas asociadas a 3 cursos")
        print("\n📝 Quizzes Created:")
        print("  - Quiz lección (Curso 1): 5 preguntas — 70%, 3 intentos, 10min")
        print("  - Quiz lección (Curso 2): 4 preguntas — 60%, 5 intentos, 15min")
        print("  - Quiz lección (Curso 3): 4 preguntas — 70%, 3 intentos, sin límite")
        print("  - FINAL (Curso 1): 6 preguntas (2 MC, 1 T/F, 1 matching, 1 ordering, 1 SA) — 70%, 20min")
        print("  - FINAL (Curso 2): 5 preguntas (1 ordering, 1 MC, 1 matching, 1 T/F, 1 SA) — 70%, 20min")
        print("  - FINAL (Curso 4): 6 preguntas (1 matching, 2 MC, 1 ordering, 1 T/F, 1 SA) — 70%, 25min")
        print("\n📜 Certifications Created ($50 USD cada una):")
        print("  - Certificación en Google Gemini para Empresas (Curso 1)")
        print("  - Certificación en Gemas Personalizadas (Curso 2)")
        print("  - Certificación en Google Workspace + Gemini (Curso 4)")
        print("\n🔑 Course Grants:")
        print("  - Learner tiene acceso a todos los cursos")
        print("\n🎯 Total: 10 courses, 46 lessons, 7 badges, 10 gems, 6 quizzes (30 preguntas), 3 certs ($50)")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
