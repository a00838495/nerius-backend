#!/bin/bash

# Script de pruebas completo para endpoints de cursos
BASE_URL="http://localhost:8000/api/v1"
COOKIES_FILE="/tmp/nerius_test_cookies.txt"

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================="
echo "   PRUEBAS COMPLETAS DE ENDPOINTS DE CURSOS"
echo -e "==============================================${NC}"
echo ""

# Limpiar cookies anteriores
rm -f "$COOKIES_FILE"

# ==========================================
# 1. AUTENTICACIÓN
# ==========================================
echo -e "${GREEN}=== 1. LOGIN ===${NC}"
LOGIN_RESPONSE=$(curl -s -c "$COOKIES_FILE" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }')

echo "$LOGIN_RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('user', {}).get('id', ''))" 2>/dev/null)
echo -e "${YELLOW}User ID: $USER_ID${NC}"
echo ""

# ==========================================
# 2. LISTAR TODOS LOS CURSOS PUBLICADOS
# ==========================================
echo -e "${GREEN}=== 2. LISTAR CURSOS PUBLICADOS ===${NC}"
ALL_COURSES=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses")
echo "$ALL_COURSES" | python3 -m json.tool
TOTAL_COURSES=$(echo "$ALL_COURSES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo -e "${YELLOW}Total cursos publicados: $TOTAL_COURSES${NC}"
echo ""

# ==========================================
# 3. OBTENER CURSOS RECOMENDADOS
# ==========================================
echo -e "${GREEN}=== 3. CURSOS RECOMENDADOS (no inscritos) ===${NC}"
RECOMMENDED=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/recommended")
echo "$RECOMMENDED" | python3 -m json.tool
RECOMMENDED_COUNT=$(echo "$RECOMMENDED" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo -e "${YELLOW}Cursos recomendados: $RECOMMENDED_COUNT${NC}"

# Obtener ID de un curso recomendado para enrollar
RECOMMENDED_COURSE_ID=$(echo "$RECOMMENDED" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)
echo -e "${YELLOW}Curso recomendado para prueba: $RECOMMENDED_COURSE_ID${NC}"
echo ""

# ==========================================
# 4. OBTENER CURSOS PENDIENTES
# ==========================================
echo -e "${GREEN}=== 4. CURSOS PENDIENTES (con enrollment activo) ===${NC}"
PENDING=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/pending")
echo "$PENDING" | python3 -m json.tool
PENDING_COUNT=$(echo "$PENDING" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo -e "${YELLOW}Cursos pendientes: $PENDING_COUNT${NC}"

# Obtener ID de un curso pendiente para pruebas detalladas
ENROLLED_COURSE_ID=$(echo "$PENDING" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['course_id'] if data else '')" 2>/dev/null)
echo -e "${YELLOW}Curso enrollado para pruebas: $ENROLLED_COURSE_ID${NC}"
echo ""

# ==========================================
# 5. ENROLLAR EN CURSO RECOMENDADO
# ==========================================
if [ -n "$RECOMMENDED_COURSE_ID" ]; then
    echo -e "${GREEN}=== 5. ENROLLAR EN CURSO RECOMENDADO ===${NC}"
    ENROLL_RESPONSE=$(curl -s -b "$COOKIES_FILE" -X POST "$BASE_URL/courses/$RECOMMENDED_COURSE_ID/enroll" \
      -H "Content-Type: application/json")
    
    echo "$ENROLL_RESPONSE" | python3 -m json.tool
    
    # Verificar código de respuesta
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIES_FILE" -X POST "$BASE_URL/courses/$RECOMMENDED_COURSE_ID/enroll" -H "Content-Type: application/json")
    
    if [ "$HTTP_CODE" -eq "201" ] || [ "$HTTP_CODE" -eq "409" ]; then
        echo -e "${YELLOW}✓ Enrollment exitoso o ya existente${NC}"
        # Si fue exitoso, usar este curso para el resto de pruebas
        if [ "$HTTP_CODE" -eq "201" ]; then
            ENROLLED_COURSE_ID="$RECOMMENDED_COURSE_ID"
        fi
    else
        echo -e "${RED}✗ Error en enrollment: HTTP $HTTP_CODE${NC}"
    fi
    echo ""
    
    # ==========================================
    # 6. INTENTAR ENROLLAR NUEVAMENTE (debe dar 409)
    # ==========================================
    echo -e "${GREEN}=== 6. INTENTAR ENROLLAR NUEVAMENTE (debe dar 409) ===${NC}"
    DUPLICATE_ENROLL=$(curl -s -b "$COOKIES_FILE" -X POST "$BASE_URL/courses/$RECOMMENDED_COURSE_ID/enroll" \
      -H "Content-Type: application/json" \
      -w "\nHTTP Status: %{http_code}\n")
    
    echo "$DUPLICATE_ENROLL"
    echo ""
fi

# ==========================================
# 7. VER CURSO DETALLADO (carga inicial)
# ==========================================
if [ -n "$ENROLLED_COURSE_ID" ]; then
    echo -e "${GREEN}=== 7. CURSO DETALLADO - Carga Inicial ===${NC}"
    COURSE_DETAIL=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/$ENROLLED_COURSE_ID/detailed")
    echo "$COURSE_DETAIL" | python3 -m json.tool
    
    # Extraer IDs del primer módulo y primera lección
    FIRST_MODULE_ID=$(echo "$COURSE_DETAIL" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('first_module', {}).get('id', ''))" 2>/dev/null)
    FIRST_LESSON_ID=$(echo "$COURSE_DETAIL" | python3 -c "import sys, json; data=json.load(sys.stdin); lessons=data.get('first_module', {}).get('lessons', []); print(lessons[0]['id'] if lessons else '')" 2>/dev/null)
    SECOND_LESSON_ID=$(echo "$COURSE_DETAIL" | python3 -c "import sys, json; data=json.load(sys.stdin); lessons=data.get('first_module', {}).get('lessons', []); print(lessons[1]['id'] if len(lessons) > 1 else '')" 2>/dev/null)
    
    echo -e "${YELLOW}Primer Módulo: $FIRST_MODULE_ID${NC}"
    echo -e "${YELLOW}Primera Lección: $FIRST_LESSON_ID${NC}"
    echo -e "${YELLOW}Segunda Lección: $SECOND_LESSON_ID${NC}"
    echo ""
    
    # ==========================================
    # 8. CURSO DETALLADO CON FOCUS EN SEGUNDA LECCIÓN
    # ==========================================
    if [ -n "$SECOND_LESSON_ID" ]; then
        echo -e "${GREEN}=== 8. CURSO DETALLADO - Focus en Segunda Lección ===${NC}"
        FOCUSED_DETAIL=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/$ENROLLED_COURSE_ID/detailed?focus_module_id=$FIRST_MODULE_ID&focus_lesson_id=$SECOND_LESSON_ID")
        
        # Mostrar solo información relevante
        echo "$FOCUSED_DETAIL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
module = data.get('first_module', {})
print('Módulo:', module.get('title'))
print('Lecciones:')
for lesson in module.get('lessons', []):
    has_resources = len(lesson.get('resources', [])) > 0
    marker = '📚' if has_resources else '📝'
    print(f\"  {marker} {lesson['title']} - Recursos: {len(lesson.get('resources', []))}\")
" 2>/dev/null
        echo ""
    fi
    
    # ==========================================
    # 9. ACTUALIZAR PROGRESO DE LECCIÓN
    # ==========================================
    if [ -n "$FIRST_LESSON_ID" ]; then
        echo -e "${GREEN}=== 9. ACTUALIZAR PROGRESO - 50% en progreso ===${NC}"
        PROGRESS_UPDATE=$(curl -s -b "$COOKIES_FILE" -X PUT \
          "$BASE_URL/courses/$ENROLLED_COURSE_ID/lessons/$FIRST_LESSON_ID/progress" \
          -H "Content-Type: application/json" \
          -d '{
            "progress_percent": 50.0,
            "time_spent_seconds": 300,
            "status": "in_progress"
          }')
        
        echo "$PROGRESS_UPDATE" | python3 -m json.tool
        echo ""
        
        echo -e "${GREEN}=== 10. ACTUALIZAR PROGRESO - 100% completado ===${NC}"
        PROGRESS_COMPLETE=$(curl -s -b "$COOKIES_FILE" -X PUT \
          "$BASE_URL/courses/$ENROLLED_COURSE_ID/lessons/$FIRST_LESSON_ID/progress" \
          -H "Content-Type: application/json" \
          -d '{
            "progress_percent": 100.0,
            "time_spent_seconds": 900,
            "status": "completed"
          }')
        
        echo "$PROGRESS_COMPLETE" | python3 -m json.tool
        echo ""
        
        # ==========================================
        # 11. VERIFICAR PROGRESO ACTUALIZADO
        # ==========================================
        echo -e "${GREEN}=== 11. VERIFICAR PROGRESO ACTUALIZADO ===${NC}"
        UPDATED_DETAIL=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/$ENROLLED_COURSE_ID/detailed")
        
        echo "$UPDATED_DETAIL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
enrollment = data.get('enrollment', {})
module = data.get('first_module', {})
print(f\"📊 Progreso del Curso: {enrollment.get('progress_percent')}%\")
print(f\"📖 Estado: {enrollment.get('status')}\")
print('\\nProgreso por Lección:')
for lesson in module.get('lessons', []):
    progress = lesson.get('progress')
    if progress:
        print(f\"  • {lesson['title']}: {progress['progress_percent']}% ({progress['status']})\")
    else:
        print(f\"  • {lesson['title']}: Sin iniciar\")
" 2>/dev/null
        echo ""
    fi
    
    # ==========================================
    # 12. VERIFICAR CURSOS PENDIENTES ACTUALIZADOS
    # ==========================================
    echo -e "${GREEN}=== 12. VERIFICAR CURSOS PENDIENTES ACTUALIZADOS ===${NC}"
    UPDATED_PENDING=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/pending")
    
    echo "$UPDATED_PENDING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total cursos activos: {len(data)}\")
for enrollment in data:
    course = enrollment.get('course', {})
    print(f\"\\n• {course.get('title')}\")
    print(f\"  Progreso: {enrollment['progress_percent']}%\")
    print(f\"  Estado: {enrollment['status']}\")
" 2>/dev/null
    echo ""
fi

# ==========================================
# 13. VERIFICAR CURSOS RECOMENDADOS ACTUALIZADOS
# ==========================================
echo -e "${GREEN}=== 13. CURSOS RECOMENDADOS ACTUALIZADOS ===${NC}"
FINAL_RECOMMENDED=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/recommended")
FINAL_RECOMMENDED_COUNT=$(echo "$FINAL_RECOMMENDED" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo -e "${YELLOW}Cursos recomendados restantes: $FINAL_RECOMMENDED_COUNT${NC}"
echo ""

# Limpiar cookies
rm -f "$COOKIES_FILE"

echo -e "${BLUE}=============================================="
echo "   ✓ PRUEBAS COMPLETADAS"
echo -e "==============================================${NC}"
echo ""
echo -e "${YELLOW}RESUMEN:${NC}"
echo "• Cursos publicados totales: $TOTAL_COURSES"
echo "• Cursos recomendados iniciales: $RECOMMENDED_COUNT"
echo "• Cursos pendientes: $PENDING_COUNT"
echo "• Cursos recomendados finales: $FINAL_RECOMMENDED_COUNT"
