# API Authentication and Rate Limits
## Authentication
All requests to the production API must include an `X-API-Key` header containing a valid user token. Unauthorized requests will return a 401 Unauthorized error code.

## Rate Limiting
The API enforces a strict rate limit of 100 requests per minute per API key. If you exceed this threshold, the server will respond with a 429 Too Many Requests status code and include a `Retry-After` header indicating how many seconds you must wait.