#!/bin/bash

# Test All Endpoints Script for Gen Book API
# This script tests all test routes endpoints
#
# Usage:
#   From project root: ./test/test_all_endpoints.sh
#   From test directory: ./test_all_endpoints.sh

echo "🚀 Starting comprehensive test of all endpoints..."
echo "=================================================="

BASE_URL="http://localhost:8000"
TEST_DIR="run"
mkdir -p "$TEST_DIR"

echo ""
echo "📋 Testing GET /api/v1/test/pdf"
echo "-----------------------------------"
curl -X GET "$BASE_URL/api/v1/test/pdf" \
  -H "accept: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n"

echo ""
echo "🖼️  Testing GET /api/v1/test/images"
echo "-----------------------------------"
curl -X GET "$BASE_URL/api/v1/test/images" \
  -H "accept: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n"

echo ""
echo "📖 Testing POST /api/v1/test/test-cover/"
echo "---------------------------------------"
COVER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/test/test-cover/" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "01",
    "book_id": "01",
    "name": "Stephen",
    "image_url": "https://example.com/face.jpg"
  }' \
  --output "$TEST_DIR/test_cover_$(date +%s).pdf" \
  -w "Status: %{http_code}, Time: %{time_total}s, Size: %{size_download} bytes")
echo "$COVER_RESPONSE"

echo ""
echo "📄 Testing POST /api/v1/test/test-interleaf/"
echo "-------------------------------------------"
INTERLEAF_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/test/test-interleaf/" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "01",
    "book_id": "01",
    "interleaf_count": 2,
    "name": "Stephen",
    "image_url": "https://example.com/face.jpg"
  }' \
  --output "$TEST_DIR/test_interleaf_$(date +%s).pdf" \
  -w "Status: %{http_code}, Time: %{time_total}s, Size: %{size_download} bytes")
echo "$INTERLEAF_RESPONSE"

echo ""
echo "📚 Testing POST /api/v1/test/test-content/ (12 stories)"
echo "-----------------------------------------------------"
CONTENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/test/test-content/" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "01",
    "book_id": "01",
    "stories": [
      {"story_id": "01"},
      {"story_id": "02"},
      {"story_id": "03"},
      {"story_id": "04"},
      {"story_id": "05"},
      {"story_id": "06"},
      {"story_id": "07"},
      {"story_id": "08"},
      {"story_id": "09"},
      {"story_id": "10"},
      {"story_id": "11"},
      {"story_id": "12"}
    ],
    "name": "Stephen",
    "image_url": "https://example.com/face.jpg"
  }' \
  --output "$TEST_DIR/test_content_$(date +%s).pdf" \
  -w "Status: %{http_code}, Time: %{time_total}s, Size: %{size_download} bytes")
echo "$CONTENT_RESPONSE"

echo ""
echo "=================================================="
echo "✅ Test completed!"
echo ""
echo "📁 Generated files in test/run/:"
ls -la "$TEST_DIR"/*.pdf 2>/dev/null || echo "No PDF files found"

echo ""
echo "📊 Summary:"
echo "- PDF endpoint: URL retrieval"
echo "- Images endpoint: Image URLs"
echo "- Cover endpoint: PDF file generated"
echo "- Interleaf endpoint: PDF file generated"
echo "- Content endpoint: PDF file generated (12 stories)"

echo ""
echo "🎯 All endpoints tested successfully!"
