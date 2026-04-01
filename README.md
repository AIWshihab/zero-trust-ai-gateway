curl -X POST "https://api.us-west-2.modal.direct/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer modalresearch_oMfipVYQvV0w8_E79XxNr52VhL2t1Cn8eu4f4tY_Ruw" \
  -d '{"model": "zai-org/GLM-5-FP8", "messages": [{"role": "user", "content": "Hi there"}], "max_tokens": 500}'