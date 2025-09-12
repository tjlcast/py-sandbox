curl -X POST "http://localhost:8000/execute" \
-H "Content-Type: application/json" \
-d '{
  "code": "for i in range(5):\n    print(f\"Number: {i}\")"
}'