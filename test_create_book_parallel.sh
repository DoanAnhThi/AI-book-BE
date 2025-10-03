#!/bin/bash

# Test endpoint /create-book/ với xử lý bất đồng bộ (parallel)
# Chạy lệnh: chmod +x test_create_book_parallel.sh && ./test_create_book_parallel.sh

IMAGE_URL="https://assets-us-01.kc-usercontent.com/5cb25086-82d2-4c89-94f0-8450813a0fd3/0c3fcefb-bc28-4af6-985e-0c3b499ae832/Elon_Musk_Royal_Society.jpg?fm=jpg&auto=format"
CHARACTER_NAME="Nguyễn Văn A"

echo "🚀 Testing /create-book/ endpoint (PARALLEL VERSION)"
echo "==================================================="
echo "👤 Character: $CHARACTER_NAME"
echo "📖 Book: Category 01, Book 01"
echo "📄 Stories: 4 stories (01, 02, 03, 04)"
echo "⚡ Parallel processing: Stories & pages processed concurrently"
echo ""

start_time=$(date +%s)

curl -X POST "http://localhost:8000/api/v1/create-book/" \
  -H "Content-Type: application/json" \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\", 
    \"stories\": [
      {\"story_id\": \"01\"},
      {\"story_id\": \"02\"},
      {\"story_id\": \"03\"},
      {\"story_id\": \"04\"}
    ],
    \"gender\": \"male\",
    \"language\": \"vi\",
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" \
  --max-time 600 \
  -o test/run/book_parallel_test.pdf \
  -w "Status: %{http_code}, Time: %{time_total}s, Size: %{size_download} bytes
"

end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo "✅ Test completed!"
echo "📁 File saved: test/run/book_parallel_test.pdf"
echo "⏱️  Total execution time: ${duration} seconds"
echo ""
echo "📊 Expected structure with parallel processing:"
echo "  - Cover: 1 page"
echo "  - Story 1-2: 4 pages + Interleaf 1: 2 pages"
echo "  - Story 3-4: 4 pages + Interleaf 2: 2 pages"
echo "  - Total: 13 pages"
echo ""
echo "⚡ Performance improvements:"
echo "  - Stories processed concurrently (not sequentially)"
echo "  - Pages within each story processed concurrently (01 & 02 at same time)"
echo "  - Cover and content preparation run in parallel"
echo ""
echo "💡 Note: Parallel processing significantly reduces total generation time!"
