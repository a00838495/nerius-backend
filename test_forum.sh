#!/bin/bash

# Script de pruebas para endpoints del foro
BASE_URL="http://localhost:8000/api/v1"

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================="
echo "   PRUEBAS DE ENDPOINTS DEL FORO"
echo -e "==============================================${NC}"
echo ""

# ==========================================
# 1. OBTENER PRIMEROS 10 POSTS DEL FORO
# ==========================================
echo -e "${GREEN}=== 1. LISTAR PRIMEROS 10 POSTS DEL FORO ===${NC}"
FORUM_POSTS=$(curl -s "$BASE_URL/forum")
echo "$FORUM_POSTS" | python3 -m json.tool

POSTS_COUNT=$(echo "$FORUM_POSTS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo -e "${YELLOW}Total posts encontrados: $POSTS_COUNT${NC}"

# Extraer ID del primer post para pruebas
FIRST_POST_ID=$(echo "$FORUM_POSTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)
FIRST_POST_TITLE=$(echo "$FORUM_POSTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['title'] if data else '')" 2>/dev/null)
FIRST_POST_COMMENTS=$(echo "$FORUM_POSTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['comments_count'] if data else 0)" 2>/dev/null)

echo -e "${YELLOW}Primer Post ID: $FIRST_POST_ID${NC}"
echo -e "${YELLOW}Título: $FIRST_POST_TITLE${NC}"
echo -e "${YELLOW}Comentarios: $FIRST_POST_COMMENTS${NC}"
echo ""

# ==========================================
# 2. OBTENER DETALLES DE UN POST ESPECÍFICO
# ==========================================
if [ -n "$FIRST_POST_ID" ]; then
    echo -e "${GREEN}=== 2. OBTENER DETALLE DEL POST ===${NC}"
    POST_DETAIL=$(curl -s "$BASE_URL/forum/$FIRST_POST_ID")
    
    echo "$POST_DETAIL" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"ID: {data.get('id')}\")
print(f\"Título: {data.get('title')}\")
print(f\"Autor: {data.get('author', {}).get('first_name')} {data.get('author', {}).get('last_name')}\")
print(f\"Estado: {data.get('status')}\")
print(f\"Comentarios: {data.get('comments_count')}\")
print(f\"Creado: {data.get('created_at')}\")
print(f\"\\nContenido:\\n{data.get('content')[:200]}...\")
" 2>/dev/null
    echo ""
    
    # ==========================================
    # 3. OBTENER COMENTARIOS DEL POST
    # ==========================================
    echo -e "${GREEN}=== 3. OBTENER COMENTARIOS DEL POST ===${NC}"
    COMMENTS=$(curl -s "$BASE_URL/forum/$FIRST_POST_ID/comments")
    
    COMMENTS_COUNT=$(echo "$COMMENTS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    echo -e "${YELLOW}Total comentarios (top-level): $COMMENTS_COUNT${NC}"
    echo ""
    
    if [ "$COMMENTS_COUNT" -gt 0 ]; then
        echo "$COMMENTS" | python3 -c "
import sys, json
comments = json.load(sys.stdin)
print('Comentarios:')
print('─' * 80)
for i, comment in enumerate(comments, 1):
    author = comment.get('author', {})
    author_name = f\"{author.get('first_name')} {author.get('last_name')}\"
    replies = comment.get('replies_count', 0)
    content_preview = comment.get('content', '')[:100]
    
    print(f\"{i}. {author_name}\")
    print(f\"   Respuestas: {replies}\")
    print(f\"   {content_preview}...\")
    print()
" 2>/dev/null
    else
        echo -e "${YELLOW}No hay comentarios en este post${NC}"
    fi
    echo ""
fi

# ==========================================
# 4. PROBAR PAGINACIÓN
# ==========================================
echo -e "${GREEN}=== 4. PROBAR PAGINACIÓN (skip=0, limit=3) ===${NC}"
PAGINATED_POSTS=$(curl -s "$BASE_URL/forum?limit=3&skip=0")

echo "$PAGINATED_POSTS" | python3 -c "
import sys, json
posts = json.load(sys.stdin)
print(f'Posts retornados: {len(posts)}')
print()
for post in posts:
    print(f\"• {post['title']}\")
    print(f\"  Autor: {post['author']['first_name']} {post['author']['last_name']}\")
    print(f\"  Comentarios: {post['comments_count']}\")
    print()
" 2>/dev/null
echo ""

# ==========================================
# 5. PROBAR POST INEXISTENTE
# ==========================================
echo -e "${GREEN}=== 5. PROBAR POST INEXISTENTE (debe dar 404) ===${NC}"
INVALID_POST=$(curl -s "$BASE_URL/forum/00000000-0000-0000-0000-000000000000" \
  -w "\nHTTP Status: %{http_code}\n")

echo "$INVALID_POST"
echo ""

echo -e "${BLUE}=============================================="
echo "   ✓ PRUEBAS DEL FORO COMPLETADAS"
echo -e "==============================================${NC}"
echo ""
echo -e "${YELLOW}RESUMEN:${NC}"
echo "• Total posts disponibles: $POSTS_COUNT"
echo "• Post de ejemplo: $FIRST_POST_TITLE"
echo "• Comentarios en post de ejemplo: $FIRST_POST_COMMENTS"
