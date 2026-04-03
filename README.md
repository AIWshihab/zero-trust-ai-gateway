# Zero Trust AI Gateway

Example request:

```bash
curl -X POST "https://api.us-west-2.modal.direct/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>" \
  -d '{"model":"zai-org/GLM-5-FP8","messages":[{"role":"user","content":"Hi there"}],"max_tokens":500}'
```
