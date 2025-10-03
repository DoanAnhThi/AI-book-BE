#!/bin/bash

# Test endpoint /create-content/ để kiểm tra placeholder replacement
# Chạy lệnh: chmod +x test_create_content.sh && ./test_create_content.sh

IMAGE_URL="https://assets-us-01.kc-usercontent.com/5cb25086-82d2-4c89-94f0-8450813a0fd3/0c3fcefb-bc28-4af6-985e-0c3b499ae832/Elon_Musk_Royal_Society.jpg?fm=jpg&auto=format"
CHARACTER_NAME="Nguyễn Văn A"

echo "📝 Testing /create-content/ endpoint - Character Name Replacement"
echo "================================================================"
echo "👤 Character Name: $CHARACTER_NAME"
echo "📖 Book: Category 01, Book 01"
echo "📄 Stories: 1 story (01) - 2 pages"
echo "🔍 Checking: {character_name} placeholder replacement"
echo ""

curl -X POST "http://localhost:8000/api/v1/create-content/" \
  -H "Content-Type: application/json" \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\", 
    \"stories\": [
      {\"story_id\": \"01\"}
    ],
    \"gender\": \"male\",
    \"language\": \"vi\",
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" \
  --max-time 300 \
  -o test/run/content_test.pdf \
  -w "Status: %{http_code}, Time: %{time_total}s, Size: %{size_download} bytes\n"

echo ""
echo "✅ Test completed!"
echo "📁 File saved: test/run/content_test.pdf"
echo ""
echo "🔍 Expected: Character name '$CHARACTER_NAME' should replace {character_name} in content"
echo ""
echo "📖 Sample story content should show:"
echo "  'Wusstest du, $CHARACTER_NAME? Der Glockenschlag von Big Ben...'"
echo "  Instead of: 'Wusstest du, {character_name}? Der Glockenschlag von Big Ben...'"
echo ""
echo "💡 Tip: Open the PDF to verify character name replacement!"
