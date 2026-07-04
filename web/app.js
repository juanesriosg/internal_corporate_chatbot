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
const runInfoEl = document.querySelector("#run-info");
const feedbackCommentInput = document.querySelector("#feedback-comment");
const feedbackUpButton = document.querySelector("#feedback-up");
const feedbackDownButton = document.querySelector("#feedback-down");
const feedbackMessage = document.querySelector("#feedback-message");

let currentResponse = null;
let currentQuestion = "";
let currentUserId = "";

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

feedbackUpButton.addEventListener("click", () => submitFeedback("up"));
feedbackDownButton.addEventListener("click", () => submitFeedback("down"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const apiUrl = normalizeApiUrl(apiUrlInput.value);
  const question = questionInput.value.trim();
  const userId = userIdInput.value;

  if (!apiUrl || !question) {
    return;
  }

  window.localStorage.setItem("chatbot_api_url", apiUrl);
  currentQuestion = question;
  currentUserId = userId;
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
    setStatus(
      payload.fallback_used ? "Fallback" : payload.refusal ? "Refused" : "Answered",
      payload.fallback_used ? "warn" : payload.refusal ? "warn" : "ok",
    );
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
  currentResponse = payload;
  answerEl.classList.remove("empty", "error");
  answerEl.textContent = payload.answer || "No answer returned.";
  renderList(
    citationsEl,
    payload.citations || [],
    (citation) => `${citation.title} (${citation.chunk_id})`,
  );
  renderList(chunksEl, payload.retrieved_chunk_ids || [], (chunkId) => chunkId);
  renderRunInfo(payload);
  setFeedbackEnabled(true);
  feedbackMessage.textContent = "";
}

function renderRunInfo(payload) {
  const timings = payload.timings_ms || {};
  const items = [
    `Request: ${payload.request_id}`,
    `Provider: ${payload.provider}`,
    `Fallback: ${payload.fallback_used ? "yes" : "no"}`,
  ];

  if (payload.fallback_reason) {
    items.push(`Fallback reason: ${payload.fallback_reason}`);
  }

  Object.entries(timings).forEach(([key, value]) => {
    items.push(`${key}: ${value} ms`);
  });

  renderList(runInfoEl, items, (item) => item);
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
  currentResponse = null;
  answerEl.classList.remove("empty");
  answerEl.classList.add("error");
  answerEl.textContent = error.message || "Request failed.";
  citationsEl.replaceChildren();
  chunksEl.replaceChildren();
  runInfoEl.replaceChildren();
  setFeedbackEnabled(false);
}

function renderEmpty() {
  currentResponse = null;
  answerEl.classList.add("empty");
  answerEl.classList.remove("error");
  answerEl.textContent = "No answer yet.";
  citationsEl.replaceChildren();
  chunksEl.replaceChildren();
  runInfoEl.replaceChildren();
  feedbackCommentInput.value = "";
  feedbackMessage.textContent = "";
  setFeedbackEnabled(false);
}

function setLoading(isLoading) {
  askButton.disabled = isLoading;
  askButton.textContent = isLoading ? "Asking..." : "Ask";
}

async function submitFeedback(rating) {
  if (!currentResponse) {
    return;
  }

  const apiUrl = normalizeApiUrl(apiUrlInput.value);
  setFeedbackLoading(true);
  feedbackMessage.textContent = "Saving...";

  try {
    const response = await fetch(`${apiUrl}/feedback`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify({
        request_id: currentResponse.request_id,
        user_id: currentUserId,
        rating,
        question: currentQuestion,
        answer: currentResponse.answer,
        comment: feedbackCommentInput.value.trim(),
      }),
    });
    const payload = await parsePayload(response);
    if (!response.ok) {
      throw new Error(payload.detail || `Feedback failed with ${response.status}`);
    }
    feedbackMessage.textContent = "Saved.";
  } catch (error) {
    feedbackMessage.textContent = error.message || "Feedback failed.";
  } finally {
    setFeedbackLoading(false);
  }
}

function setFeedbackEnabled(isEnabled) {
  feedbackUpButton.disabled = !isEnabled;
  feedbackDownButton.disabled = !isEnabled;
}

function setFeedbackLoading(isLoading) {
  feedbackUpButton.disabled = isLoading;
  feedbackDownButton.disabled = isLoading;
}

function setStatus(label, state = "neutral") {
  statusPill.textContent = label;
  statusPill.dataset.state = state;
}

function normalizeApiUrl(value) {
  return value.trim().replace(/\/+$/, "");
}
