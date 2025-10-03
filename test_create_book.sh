#!/bin/bash

# Test endpoint /create-book/
# Chạy lệnh: chmod +x test_create_book.sh && ./test_create_book.sh

IMAGE_URL="https://assets-us-01.kc-usercontent.com/5cb25086-82d2-4c89-94f0-8450813a0fd3/0c3fcefb-bc28-4af6-985e-0c3b499ae832/Elon_Musk_Royal_Society.jpeg?fm=jpeg&auto=format"
CHARACTER_NAME="Nguyễn Văn A"

echo "📚 Testing /create-book/ endpoint"
echo "=================================="
echo "👤 Character: $CHARACTER_NAME"
echo "📖 Book: Category 01, Book 01"
echo "📄 Stories: 3 stories (01, 02, 03)"
echo ""

RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/create-book/" \
  -H "Content-Type: application/json" \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\",
    \"stories\": [
      {\"story_id\": \"01\"},
      {\"story_id\": \"02\"},
      {\"story_id\": \"03\"}
    ],
    \"gender\": \"boy\",
    \"language\": \"VN\",
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" \
  --max-time 600 \
  -w "Status: %{http_code}, Time: %{time_total}s, Size: %{size_download} bytes")

echo ""
echo "📄 API Response:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract download URL from response
DOWNLOAD_URL=$(echo "$RESPONSE" | jq -r '.download_url' 2>/dev/null)

if [ "$DOWNLOAD_URL" != "null" ] && [ -n "$DOWNLOAD_URL" ]; then
    echo "📥 Downloading PDF from: $DOWNLOAD_URL"
    curl -o "test/run/book_test.pdf" "$DOWNLOAD_URL" \
      --max-time 300 \
      -w "Download Status: %{http_code}, Size: %{size_download} bytes\n"
    echo ""
    echo "✅ PDF downloaded successfully!"
    echo "📁 File saved: test/run/book_test.pdf"
else
    echo "❌ Failed to get download URL from response"
fi

echo ""
echo "📊 Expected structure:"
echo "  - Cover: 1 page"
echo "  - Story 1: 2 pages"
echo "  - Story 2: 2 pages"
echo "  - Interleaf 1: 2 pages"
echo "  - Story 3: 2 pages"
echo "  - Total: 9 pages"
echo ""
echo "💡 Note: PDF generation takes 2-5+ minutes"
echo "💡 Change CHARACTER_NAME and IMAGE_URL variables to test with different data"
