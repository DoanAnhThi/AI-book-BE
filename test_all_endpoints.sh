#!/bin/bash

# Test script cho tất cả PDF generation endpoints
# Chạy lệnh: chmod +x test_all_endpoints.sh && ./test_all_endpoints.sh

IMAGE_URL="https://assets-us-01.kc-usercontent.com/5cb25086-82d2-4c89-94f0-8450813a0fd3/0c3fcefb-bc28-4af6-985e-0c3b499ae832/Elon_Musk_Royal_Society.png?fm=png&auto=format"
CHARACTER_NAME="Nguyễn Văn A"  # Thay đổi tên nhân vật ở đây

echo "🚀 Testing tất cả PDF Generation Endpoints"
echo "============================================"
echo "👤 Tên nhân vật: $CHARACTER_NAME"
echo "📂 Lưu kết quả vào: test/run/"
echo ""

# Test 1: create_cover
echo "📖 Testing create_cover endpoint..."
curl -X POST 'http://localhost:8000/api/v1/create-cover/' \
  -H 'Content-Type: application/json' \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\",
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" --max-time 120 -o test/run/cover.pdf -w "Status: %{http_code}, Time: %{time_total}s\n"

echo ""

# Test 2: create_interleaf
echo "📄 Testing create_interleaf endpoint..."
curl -X POST 'http://localhost:8000/api/v1/create-interleaf/' \
  -H 'Content-Type: application/json' \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\",
    \"interleaf_count\": 1,
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" --max-time 120 -o test/run/interleaf.pdf -w "Status: %{http_code}, Time: %{time_total}s\n"

echo ""

# Test 3: create_content
echo "📝 Testing create_content endpoint..."
curl -X POST 'http://localhost:8000/api/v1/create-content/' \
  -H 'Content-Type: application/json' \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\",
    \"stories\": [{\"story_id\": \"01\"}],
    \"gender\": \"male\",
    \"language\": \"vi\",
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" --max-time 300 -o test/run/content.pdf -w "Status: %{http_code}, Time: %{time_total}s\n"

echo ""

# Test 4: create_book
echo "📚 Testing create_book endpoint..."
curl -X POST 'http://localhost:8000/api/v1/create-book/' \
  -H 'Content-Type: application/json' \
  -d "{
    \"category_id\": \"01\",
    \"book_id\": \"01\",
    \"stories\": [{\"story_id\": \"01\"}],
    \"gender\": \"male\",
    \"language\": \"vi\",
    \"name\": \"$CHARACTER_NAME\",
    \"image_url\": \"$IMAGE_URL\"
  }" --max-time 300 -o test/run/book.pdf -w "Status: %{http_code}, Time: %{time_total}s\n"

echo ""
echo "✅ Test completed!"
echo "📁 Generated files in test/run/:"
ls -la test/run/*.pdf 2>/dev/null || echo "No PDF files generated yet"
echo ""
echo "💡 Note: PDF generation takes 60-120+ seconds per endpoint"
echo "💡 Change CHARACTER_NAME variable at the top to test with different names"
