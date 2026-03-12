#!/bin/bash

# 🧪 Test Script para Nerius Learning Platform API
# Ejecutar: bash test_endpoints.sh

BASE_URL="http://localhost:8000/api/v1"
COOKIE_FILE="cookies.txt"

echo "🚀 Iniciando pruebas de API..."
echo "================================"

# 1. Health Check
echo -e "\n✅ 1. Health Check"
curl -s $BASE_URL/health/ | python -m json.tool

# 2. Login como usuario regular
echo -e "\n\n✅ 2. Login (user@example.com)"
curl -s -X POST $BASE_URL/auth/login \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"email\": \"user@example.com\",\n    \"password\": \"password123\"\n  }' \\\n  -c $COOKIE_FILE | python -m json.tool

# 3. Obtener información del usuario actual
echo -e "\n\n✅ 3. Get Current User Info"
curl -s $BASE_URL/auth/me \\\n  -b $COOKIE_FILE | python -m json.tool

# 4. Obtener todos los cursos disponibles
echo -e "\n\n✅ 4. Get All Published Courses"
curl -s $BASE_URL/courses/ | python -m json.tool

# 5. Obtener cursos pendientes del usuario
echo -e "\n\n✅ 5. Get User's Pending Courses"
curl -s $BASE_URL/courses/user/pending \\\n  -b $COOKIE_FILE | python -m json.tool

# 6. Logout
echo -e "\n\n✅ 6. Logout"
curl -s -X POST $BASE_URL/auth/logout \\\n  -b $COOKIE_FILE | python -m json.tool

echo -e "\n\n✅ Pruebas completadas!"
echo \"Cookie guardada en: $COOKIE_FILE\"
