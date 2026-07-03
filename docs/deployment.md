# Deployment

This project uses GitHub Actions to demonstrate CI/CD:

- CI runs lint and tests.
- GitHub Pages hosts the static web UI from `web/`.
- The API is built as a Docker image and published to GitHub Container Registry.
- The API can optionally be deployed to Azure Container Apps when Azure secrets
  and variables are configured.

## Important Constraint

GitHub Pages is static hosting. It cannot run the FastAPI backend and it cannot
protect server secrets. The OpenAI API key must stay in the API runtime, never
in `web/`, `config.js`, GitHub Pages, or browser JavaScript.

The static UI can be public, but `/chat` must be protected by server-side API
authentication. The implemented API supports Basic Auth for that purpose.

## Local Web UI

Run the API first:

```bash
python -m app.backend.rag.ingest --source mock_data --out .local
uvicorn app.backend.main:app --reload
```

Serve the static UI:

```bash
python -m http.server 5173 --directory web
```

Open:

```text
http://127.0.0.1:5173
```

For local smoke tests, API auth can stay disabled:

```text
API_AUTH_ENABLED=false
```

For a deployed API, enable it:

```text
API_AUTH_ENABLED=true
API_BASIC_USERNAME=<reviewer-username>
API_BASIC_PASSWORD=<strong-password>
CORS_ALLOWED_ORIGINS=https://<github-user-or-org>.github.io
```

## GitHub Pages UI

Workflow:

```text
.github/workflows/pages.yml
```

Repository settings:

1. Go to Settings -> Pages.
2. Set the Pages source to GitHub Actions.
3. Add repository variable `CHATBOT_API_URL` with the deployed API base URL.

Do not add any secrets to the static UI. `CHATBOT_API_URL` is only the public API
base URL; the API itself is protected by Basic Auth.

## API Container

Workflow:

```text
.github/workflows/api-container.yml
```

On every push to `main`, the workflow builds and publishes:

```text
ghcr.io/<owner>/<repo>/chatbot-api:<commit-sha>
ghcr.io/<owner>/<repo>/chatbot-api:latest
```

That proves the API can be built by CI/CD. A real hosted API still needs a
compute platform. The included workflow can update an existing Azure Container
App if these are configured:

Repository variables:

```text
AZURE_CONTAINER_APP_NAME
AZURE_RESOURCE_GROUP
OPENAI_CHAT_MODEL
OPENAI_EMBEDDING_MODEL
CORS_ALLOWED_ORIGINS
```

Repository secrets:

```text
AZURE_CREDENTIALS
OPENAI_API_KEY
API_BASIC_USERNAME
API_BASIC_PASSWORD
```

`AZURE_CREDENTIALS` should be the JSON credential expected by `azure/login`.

If the Azure values are missing, the workflow still publishes the container
image to GHCR and skips the Azure deploy step.

## Security Notes

- Keep `.env` local and uncommitted.
- Keep `OPENAI_API_KEY` only in API runtime secrets.
- Do not put the API password in `web/config.js`.
- Use HTTPS for the deployed API.
- Set `CORS_ALLOWED_ORIGINS` to the GitHub Pages origin, not `*`, for the
  deployed environment.
- Rotate `API_BASIC_PASSWORD` after sharing a review link.
- If the repo or Pages site is public, assume the page can be found. The API
  authentication is what prevents OpenAI usage.
