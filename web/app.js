const config = window.CHATBOT_CONFIG || {};

const form = document.querySelector("#chat-form");
const apiUrlInput = document.querySelector("#api-url");
const apiUserInput = document.querySelector("#api-user");
const apiPasswordInput = document.querySelector("#api-password");
const userIdInput = document.querySelector("#user-id");
const questionInput = document.querySelector("#question");
const askButton = document.querySelector("#ask-button");
const clearButton = document.querySelector("#clear-button");
const statusPill = document.querySelector("#status-pill");
const answerEl = document.querySelector("#answer");
const citationsEl = document.querySelector("#citations");
const chunksEl = document.querySelector("#chunks");

const savedApiUrl = window.localStorage.getItem("chatbot_api_url");
apiUrlInput.value = config.apiBaseUrl || savedApiUrl || "http://127.0.0.1:8000";

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    userIdInput.value = button.dataset.user;
    questionInput.focus();
  });
});

clearButton.addEventListener("click", () => {
  questionInput.value = "";
  renderEmpty();
  setStatus("Ready", "neutral");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const apiUrl = normalizeApiUrl(apiUrlInput.value);
  const question = questionInput.value.trim();
  const userId = userIdInput.value;

  if (!apiUrl || !question) {
    return;
  }

  window.localStorage.setItem("chatbot_api_url", apiUrl);
  setLoading(true);
  setStatus("Asking", "busy");

  try {
    const response = await fetch(`${apiUrl}/chat`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify({
        user_id: userId,
        question,
      }),
    });

    const payload = await parsePayload(response);
    if (!response.ok) {
      throw new Error(payload.detail || `Request failed with ${response.status}`);
    }

    renderResponse(payload);
    setStatus(payload.refusal ? "Refused" : "Answered", payload.refusal ? "warn" : "ok");
  } catch (error) {
    renderError(error);
    setStatus("Error", "error");
  } finally {
    setLoading(false);
  }
});

function buildHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };

  const username = apiUserInput.value.trim();
  const password = apiPasswordInput.value;
  if (username || password) {
    headers.Authorization = `Basic ${window.btoa(`${username}:${password}`)}`;
  }

  return headers;
}

async function parsePayload(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return { detail: await response.text() };
}

function renderResponse(payload) {
  answerEl.classList.remove("empty", "error");
  answerEl.textContent = payload.answer || "No answer returned.";
  renderList(
    citationsEl,
    payload.citations || [],
    (citation) => `${citation.title} (${citation.chunk_id})`,
  );
  renderList(chunksEl, payload.retrieved_chunk_ids || [], (chunkId) => chunkId);
}

function renderList(target, items, formatter) {
  target.replaceChildren();
  if (!items.length) {
    const item = document.createElement("li");
    item.className = "muted";
    item.textContent = "None";
    target.append(item);
    return;
  }

  items.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = formatter(value);
    target.append(item);
  });
}

function renderError(error) {
  answerEl.classList.remove("empty");
  answerEl.classList.add("error");
  answerEl.textContent = error.message || "Request failed.";
  citationsEl.replaceChildren();
  chunksEl.replaceChildren();
}

function renderEmpty() {
  answerEl.classList.add("empty");
  answerEl.classList.remove("error");
  answerEl.textContent = "No answer yet.";
  citationsEl.replaceChildren();
  chunksEl.replaceChildren();
}

function setLoading(isLoading) {
  askButton.disabled = isLoading;
  askButton.textContent = isLoading ? "Asking..." : "Ask";
}

function setStatus(label, state = "neutral") {
  statusPill.textContent = label;
  statusPill.dataset.state = state;
}

function normalizeApiUrl(value) {
  return value.trim().replace(/\/+$/, "");
}
