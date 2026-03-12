#!/bin/bash

# Script para probar el cálculo de progreso del curso
BASE_URL="http://localhost:8000/api/v1"
COOKIES_FILE="/tmp/nerius_progress_test.txt"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=============================================="
echo "   PRUEBA DE CÁLCULO DE PROGRESO"
echo -e "==============================================${NC}"
echo ""

rm -f "$COOKIES_FILE"

# Login
echo -e "${GREEN}=== 1. LOGIN ===${NC}"
curl -s -c "$COOKIES_FILE" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' > /dev/null

# Obtener un curso enrollado
echo -e "${GREEN}=== 2. OBTENER CURSO ENROLLADO ===${NC}"
PENDING=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/pending")
COURSE_ID=$(echo "$PENDING" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['course_id'] if data else '')" 2>/dev/null)

if [ -z "$COURSE_ID" ]; then
    echo -e "${YELLOW}No hay cursos enrollados. Enrollando en uno...${NC}"
    ALL_COURSES=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses")
    COURSE_ID=$(echo "$ALL_COURSES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)
    
    if [ -n "$COURSE_ID" ]; then
        curl -s -b "$COOKIES_FILE" -X POST "$BASE_URL/courses/$COURSE_ID/enroll" \
          -H "Content-Type: application/json" > /dev/null
        echo -e "${YELLOW}Enrollado en curso: $COURSE_ID${NC}"
    else
        echo -e "${RED}No se pudo enrollar${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}Usando curso: $COURSE_ID${NC}"
echo ""

# Obtener detalles del curso
echo -e "${GREEN}=== 3. OBTENER ESTRUCTURA DEL CURSO ===${NC}"
COURSE_DETAIL=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/$COURSE_ID/detailed")

# Extraer información de las lecciones
echo "$COURSE_DETAIL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
module = data.get('first_module', {})
lessons = module.get('lessons', [])
enrollment = data.get('enrollment', {})

print(f'Curso: {data.get(\"title\")}')
print(f'Progreso actual: {enrollment.get(\"progress_percent\")}%')
print(f'Total de lecciones: {len(lessons)}')
print()
print('Lecciones:')
for i, lesson in enumerate(lessons, 1):
    progress = lesson.get('progress')
    if progress:
        print(f'{i}. {lesson[\"title\"]}: {progress.get(\"progress_percent\")}% ({progress.get(\"status\")})')
    else:
        print(f'{i}. {lesson[\"title\"]}: Sin progreso')
" 2>/dev/null

# Extraer IDs de las lecciones
LESSON_IDS=$(echo "$COURSE_DETAIL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
module = data.get('first_module', {})
lessons = module.get('lessons', [])
for lesson in lessons:
    print(lesson['id'])
" 2>/dev/null)

LESSON_ARRAY=($LESSON_IDS)
TOTAL_LESSONS=${#LESSON_ARRAY[@]}
MODULE_ID=$(echo "$COURSE_DETAIL" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('first_module', {}).get('id', ''))" 2>/dev/null)

echo ""
echo -e "${YELLOW}Total de lecciones encontradas: $TOTAL_LESSONS${NC}"
echo ""

# Actualizar progreso de cada lección con diferentes valores
echo -e "${GREEN}=== 4. ACTUALIZAR PROGRESO DE LECCIONES ===${NC}"

if [ $TOTAL_LESSONS -ge 1 ]; then
    echo "• Actualizando lección 1 a 50%..."
    RESULT=$(curl -s -b "$COOKIES_FILE" -X PUT \
      "$BASE_URL/courses/$COURSE_ID/lessons/${LESSON_ARRAY[0]}/progress" \
      -H "Content-Type: application/json" \
      -d '{"progress_percent": 50.0, "time_spent_seconds": 300, "status": "in_progress"}')
    
    ENROLLMENT_PROGRESS=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('enrollment_progress_percent', 0))" 2>/dev/null)
    echo -e "${YELLOW}  Progreso del curso: $ENROLLMENT_PROGRESS%${NC}"
fi

if [ $TOTAL_LESSONS -ge 2 ]; then
    echo "• Actualizando lección 2 a 100% (completada)..."
    RESULT=$(curl -s -b "$COOKIES_FILE" -X PUT \
      "$BASE_URL/courses/$COURSE_ID/lessons/${LESSON_ARRAY[1]}/progress" \
      -H "Content-Type: application/json" \
      -d '{"progress_percent": 100.0, "time_spent_seconds": 600, "status": "completed"}')
    
    ENROLLMENT_PROGRESS=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('enrollment_progress_percent', 0))" 2>/dev/null)
    echo -e "${YELLOW}  Progreso del curso: $ENROLLMENT_PROGRESS%${NC}"
fi

if [ $TOTAL_LESSONS -ge 3 ]; then
    echo "• Actualizando lección 3 a 25%..."
    RESULT=$(curl -s -b "$COOKIES_FILE" -X PUT \
      "$BASE_URL/courses/$COURSE_ID/lessons/${LESSON_ARRAY[2]}/progress" \
      -H "Content-Type: application/json" \
      -d '{"progress_percent": 25.0, "time_spent_seconds": 150, "status": "in_progress"}')
    
    ENROLLMENT_PROGRESS=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('enrollment_progress_percent', 0))" 2>/dev/null)
    echo -e "${YELLOW}  Progreso del curso: $ENROLLMENT_PROGRESS%${NC}"
fi

echo ""

# Verificar cálculo final
echo -e "${GREEN}=== 5. VERIFICAR PROGRESO FINAL ===${NC}"
FINAL_DETAIL=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/$COURSE_ID/detailed")

echo "$FINAL_DETAIL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
module = data.get('first_module', {})
lessons = module.get('lessons', [])
enrollment = data.get('enrollment', {})

total_lessons = len(lessons)
total_progress = 0

print('Cálculo detallado:')
print('─' * 60)
for i, lesson in enumerate(lessons, 1):
    progress = lesson.get('progress')
    if progress:
        prog_percent = progress.get('progress_percent', 0)
        status = progress.get('status', 'unknown')
        print(f'{i}. {lesson[\"title\"]}: {prog_percent}% ({status})')
        total_progress += prog_percent
    else:
        print(f'{i}. {lesson[\"title\"]}: 0% (sin progreso)')
        total_progress += 0

expected_avg = total_progress / total_lessons if total_lessons > 0 else 0
actual_progress = enrollment.get('progress_percent', 0)

print('─' * 60)
print(f'Suma total: {total_progress}%')
print(f'Total lecciones: {total_lessons}')
print(f'Promedio esperado: {expected_avg:.2f}%')
print(f'Progreso en enrollment: {actual_progress}%')
print()
if abs(expected_avg - actual_progress) < 0.01:
    print('✓ CÁLCULO CORRECTO')
else:
    print('✗ ERROR EN EL CÁLCULO')
" 2>/dev/null

rm -f "$COOKIES_FILE"

echo ""
echo -e "${BLUE}=============================================="
echo "   ✓ PRUEBA COMPLETADA"
echo -e "==============================================${NC}"
