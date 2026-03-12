#!/bin/bash

# Script para probar los endpoints de cursos y enrolamiento
BASE_URL="http://localhost:8000/api/v1"
COOKIES_FILE="/tmp/nerius_cookies.txt"

echo "=============================================="
echo "   PRUEBA DE ENDPOINTS DE CURSOS Y ENROLAMIENTO"
echo "=============================================="
echo ""

# Limpiar cookies anteriores
rm -f "$COOKIES_FILE"

echo "=== 1. LOGIN CON USUARIO LEARNER1 ==="
curl -s -c "$COOKIES_FILE" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }' | python3 -m json.tool
echo -e "\n"

echo "=== 2. OBTENER TODOS LOS CURSOS PUBLICADOS ==="
curl -s -b "$COOKIES_FILE" "$BASE_URL/courses" | python3 -m json.tool
echo -e "\n"

echo "=== 3. OBTENER CURSOS RECOMENDADOS (no inscritos) ==="
curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/recommended" | python3 -m json.tool
echo -e "\n"

echo "=== 4. OBTENER CURSOS PENDIENTES (con enrollment activo) ==="
curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/pending" | python3 -m json.tool
echo -e "\n"

# Obtener el primer curso recomendado
FIRST_COURSE=$(curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/recommended")
COURSE_ID=$(echo "$FIRST_COURSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)

if [ -n "$COURSE_ID" ]; then
    echo "=== 5. ENROLLAR EN CURSO: $COURSE_ID ==="
    curl -s -b "$COOKIES_FILE" -X POST "$BASE_URL/courses/$COURSE_ID/enroll" \
      -H "Content-Type: application/json" \
      -w "\nHTTP Status: %{http_code}\n" | python3 -m json.tool 2>/dev/null || echo "Error en el enrolamiento"
    echo -e "\n"
    
    echo "=== 6. VERIFICAR CURSOS PENDIENTES (debería incluir el nuevo) ==="
    curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/pending" | python3 -m json.tool
    echo -e "\n"
    
    echo "=== 7. VERIFICAR CURSOS RECOMENDADOS (debería excluir el enrollado) ==="
    curl -s -b "$COOKIES_FILE" "$BASE_URL/courses/user/recommended" | python3 -m json.tool
    echo -e "\n"
    
    echo "=== 8. INTENTAR ENROLLAR NUEVAMENTE (debería dar error 409) ==="
    curl -s -b "$COOKIES_FILE" -X POST "$BASE_URL/courses/$COURSE_ID/enroll" \
      -H "Content-Type: application/json" \
      -w "\nHTTP Status: %{http_code}\n"
    echo -e "\n"
else
    echo "No hay cursos recomendados disponibles para probar el enrolamiento"
    echo -e "\n"
fi

# Limpiar cookies
rm -f "$COOKIES_FILE"

echo "=============================================="
echo "   PRUEBAS COMPLETADAS"
echo "=============================================="

