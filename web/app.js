const config = window.CHATBOT_CONFIG || {};

const form = document.querySelector("#chat-form");
const apiUrlInput = document.querySelector("#api-url");
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
const tabButtons = document.querySelectorAll(".tab-button[data-view]");
const viewPanels = document.querySelectorAll("[data-view-panel]");
const refreshEvalButton = document.querySelector("#refresh-eval");
const evalArtifactEl = document.querySelector("#eval-artifact");
const evalStatusEl = document.querySelector("#eval-status");
const evalSummaryEl = document.querySelector("#eval-summary");
const evalQuestionsEl = document.querySelector("#eval-questions");
const evalAclEl = document.querySelector("#eval-acl");
const refreshFeedbackButton = document.querySelector("#refresh-feedback");
const feedbackArtifactEl = document.querySelector("#feedback-artifact");
const feedbackStatusEl = document.querySelector("#feedback-status");
const feedbackSummaryEl = document.querySelector("#feedback-summary");
const feedbackRecordsEl = document.querySelector("#feedback-records");

let currentResponse = null;
let currentQuestion = "";
let currentUserId = "";

const savedApiUrl = window.localStorage.getItem("chatbot_api_url");
apiUrlInput.value = config.apiBaseUrl || savedApiUrl || "http://127.0.0.1:8000";

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setView(button.dataset.view, { scroll: true });
  });
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    userIdInput.value = button.dataset.user;
    setView("chat");
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
refreshEvalButton.addEventListener("click", loadEvalResults);
refreshFeedbackButton.addEventListener("click", loadFeedbackRecords);

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
  return {
    "Content-Type": "application/json",
  };
}

function buildGetHeaders() {
  return {};
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
  renderMarkdown(answerEl, payload.answer || "No answer returned.");
  renderList(
    citationsEl,
    payload.citations || [],
    (citation) => citation.title,
  );
  renderList(
    chunksEl,
    displaySourcesFor(payload),
    (source) => source.title,
  );
  renderRunInfo(payload);
  setFeedbackEnabled(true);
  feedbackMessage.textContent = "";
}

function displaySourcesFor(payload) {
  if (payload.retrieved_sources?.length) {
    return payload.retrieved_sources;
  }

  return (payload.retrieved_chunk_ids || []).map((chunkId) => ({
    title: formatChunkIdAsTitle(chunkId),
  }));
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

function renderMarkdown(target, markdown) {
  target.replaceChildren();

  const lines = String(markdown).split(/\r?\n/);
  let paragraphLines = [];
  let currentList = null;

  const flushParagraph = () => {
    if (!paragraphLines.length) {
      return;
    }

    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, paragraphLines.join(" "));
    target.append(paragraph);
    paragraphLines = [];
  };

  const closeList = () => {
    currentList = null;
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      closeList();
      return;
    }

    const bulletMatch = trimmed.match(/^[-*]\s+(.+)$/);
    const numberedMatch = trimmed.match(/^\d+[.)]\s+(.+)$/);

    if (bulletMatch || numberedMatch) {
      flushParagraph();
      const listTag = bulletMatch ? "ul" : "ol";
      if (!currentList || currentList.tagName.toLowerCase() !== listTag) {
        closeList();
        currentList = document.createElement(listTag);
        target.append(currentList);
      }

      const item = document.createElement("li");
      appendInlineMarkdown(item, bulletMatch?.[1] || numberedMatch?.[1] || "");
      currentList.append(item);
      return;
    }

    closeList();
    paragraphLines.push(trimmed);
  });

  flushParagraph();
}

function appendInlineMarkdown(target, text) {
  const pattern = /(`[^`]+`|\*\*[^*]+?\*\*|\*[^*\n]+?\*)/g;
  let cursor = 0;
  let match = pattern.exec(text);

  while (match) {
    appendText(target, text.slice(cursor, match.index));
    const token = match[0];

    if (token.startsWith("`")) {
      const code = document.createElement("code");
      code.textContent = token.slice(1, -1);
      target.append(code);
    } else if (token.startsWith("**")) {
      const strong = document.createElement("strong");
      appendInlineMarkdown(strong, token.slice(2, -2));
      target.append(strong);
    } else {
      const emphasis = document.createElement("em");
      appendInlineMarkdown(emphasis, token.slice(1, -1));
      target.append(emphasis);
    }

    cursor = match.index + token.length;
    match = pattern.exec(text);
  }

  appendText(target, text.slice(cursor));
}

function appendText(target, text) {
  if (text) {
    target.append(document.createTextNode(text));
  }
}

async function loadEvalResults() {
  const apiUrl = normalizeApiUrl(apiUrlInput.value);
  if (!apiUrl) {
    return;
  }

  window.localStorage.setItem("chatbot_api_url", apiUrl);
  setButtonLoading(refreshEvalButton, true, "Refresh", "Loading...");
  evalStatusEl.textContent = "Loading...";
  setStatus("Loading", "busy");

  try {
    const response = await fetch(`${apiUrl}/eval-results`, {
      headers: buildGetHeaders(),
    });
    const payload = await parsePayload(response);
    if (!response.ok) {
      throw new Error(payload.detail || `Eval results failed with ${response.status}`);
    }
    renderEvalResults(payload);
    setStatus(payload.status === "ready" ? "Ready" : "Missing", payload.status === "ready" ? "ok" : "warn");
  } catch (error) {
    evalStatusEl.textContent = error.message || "Eval results failed.";
    evalSummaryEl.replaceChildren();
    renderEmptyBlock(evalQuestionsEl);
    renderEmptyBlock(evalAclEl);
    setStatus("Error", "error");
  } finally {
    setButtonLoading(refreshEvalButton, false, "Refresh", "Loading...");
  }
}

function renderEvalResults(payload) {
  evalArtifactEl.textContent = payload.artifact || "No artifact.";
  if (payload.status === "missing" || !payload.results) {
    evalStatusEl.textContent = "No eval results found.";
    evalSummaryEl.replaceChildren();
    renderEmptyBlock(evalQuestionsEl);
    renderEmptyBlock(evalAclEl);
    return;
  }

  const results = payload.results;
  const latency = results.latency_ms || {};
  evalStatusEl.textContent = "Loaded.";
  renderMetrics(evalSummaryEl, [
    ["Recall@5", formatPercent(results.retrieval_recall_at_5)],
    ["Questions", results.sample_questions ?? 0],
    ["ACL Failures", results.unauthorized_retrieval_failures ?? 0],
    ["Avg Retrieval", formatMs(latency.avg_sample_retrieval_ms)],
    ["Max Retrieval", formatMs(latency.max_sample_retrieval_ms)],
    ["Total Eval", formatMs(latency.total_eval_ms)],
  ]);

  renderTable(
    evalQuestionsEl,
    results.question_results || [],
    [
      ["Question", (record) => record.question],
      ["Expected Source", (record) => record.expected_source],
      ["Hit", (record) => formatBoolean(record.hit_at_5 ?? record.hit)],
      ["Retrieval", (record) => formatMs(record.retrieval_ms)],
      ["Retrieved Titles", (record) => (record.retrieved_titles || []).join(", ")],
    ],
  );

  renderTable(
    evalAclEl,
    results.acl_results || [],
    [
      ["User", (record) => record.user],
      ["Query", (record) => record.query || record.blocked_title],
      ["Passed", (record) => formatAclPassed(record)],
      ["Retrieved Titles", (record) => (record.retrieved_titles || []).join(", ")],
      ["Retrieval", (record) => formatMs(record.retrieval_ms)],
    ],
  );
}

async function loadFeedbackRecords() {
  const apiUrl = normalizeApiUrl(apiUrlInput.value);
  if (!apiUrl) {
    return;
  }

  window.localStorage.setItem("chatbot_api_url", apiUrl);
  setButtonLoading(refreshFeedbackButton, true, "Refresh", "Loading...");
  feedbackStatusEl.textContent = "Loading...";
  setStatus("Loading", "busy");

  try {
    const response = await fetch(`${apiUrl}/feedback?limit=250`, {
      headers: buildGetHeaders(),
    });
    const payload = await parsePayload(response);
    if (!response.ok) {
      throw new Error(payload.detail || `Feedback failed with ${response.status}`);
    }
    renderFeedbackRecords(payload);
    setStatus("Ready", "ok");
  } catch (error) {
    feedbackStatusEl.textContent = error.message || "Feedback failed.";
    feedbackSummaryEl.replaceChildren();
    renderEmptyBlock(feedbackRecordsEl);
    setStatus("Error", "error");
  } finally {
    setButtonLoading(refreshFeedbackButton, false, "Refresh", "Loading...");
  }
}

function renderFeedbackRecords(payload) {
  const records = payload.records || [];
  const usefulCount = records.filter((record) => record.rating === "up").length;
  const notUsefulCount = records.filter((record) => record.rating === "down").length;
  feedbackArtifactEl.textContent = payload.artifact || "No artifact.";
  feedbackStatusEl.textContent = records.length ? "Loaded." : "No feedback records found.";
  renderMetrics(feedbackSummaryEl, [
    ["Total", payload.count ?? records.length],
    ["Loaded", records.length],
    ["Helpful", usefulCount],
    ["Not Helpful", notUsefulCount],
  ]);

  renderTable(
    feedbackRecordsEl,
    records,
    [
      ["Created", (record) => record.created_at],
      ["Rating", (record) => record.rating],
      ["User", (record) => record.user_id],
      ["Question", (record) => record.question],
      ["Comment", (record) => record.comment],
      ["Request", (record) => record.request_id],
    ],
  );
}

function renderMetrics(target, metrics) {
  target.replaceChildren();
  metrics.forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "metric-card";

    const valueEl = document.createElement("strong");
    valueEl.textContent = value ?? "n/a";

    const labelEl = document.createElement("span");
    labelEl.textContent = label;

    item.append(valueEl, labelEl);
    target.append(item);
  });
}

function renderTable(target, records, columns) {
  target.replaceChildren();
  target.classList.remove("empty-state");

  if (!records.length) {
    renderEmptyBlock(target);
    return;
  }

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  columns.forEach(([label]) => {
    const cell = document.createElement("th");
    cell.textContent = label;
    headerRow.append(cell);
  });
  thead.append(headerRow);

  const tbody = document.createElement("tbody");
  records.forEach((record) => {
    const row = document.createElement("tr");
    columns.forEach(([, getter]) => {
      const cell = document.createElement("td");
      const value = getter(record);
      cell.textContent = value === undefined || value === null || value === "" ? "n/a" : String(value);
      row.append(cell);
    });
    tbody.append(row);
  });

  table.append(thead, tbody);
  target.append(table);
}

function renderEmptyBlock(target) {
  target.replaceChildren();
  target.classList.add("empty-state");
  target.textContent = "No records.";
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

function formatChunkIdAsTitle(chunkId) {
  const withoutChunkIndex = String(chunkId).split("#")[0];
  const withoutHash = withoutChunkIndex.replace(/-[a-f0-9]{8}$/i, "");
  return withoutHash
    .split("-")
    .filter(Boolean)
    .map((word) => {
      const upper = word.toUpperCase();
      if (["api", "acl", "sso", "pto", "hr", "sev"].includes(word.toLowerCase())) {
        return upper;
      }
      return `${word.charAt(0).toUpperCase()}${word.slice(1)}`;
    })
    .join(" ");
}

function setView(viewName, options = {}) {
  const selectedPanel = document.querySelector(`[data-view-panel="${viewName}"]`);
  if (!selectedPanel) {
    return;
  }

  tabButtons.forEach((button) => {
    const isActive = button.dataset.view === viewName;
    button.classList.toggle("active", isActive);
    if (isActive) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });
  viewPanels.forEach((panel) => {
    panel.hidden = panel.dataset.viewPanel !== viewName;
  });

  if (options.scroll) {
    window.requestAnimationFrame(() => {
      selectedPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (viewName === "eval" && !evalSummaryEl.children.length) {
    loadEvalResults();
  }
  if (viewName === "feedback" && !feedbackSummaryEl.children.length) {
    loadFeedbackRecords();
  }
}

function setButtonLoading(button, isLoading, idleText, loadingText) {
  button.disabled = isLoading;
  button.textContent = isLoading ? loadingText : idleText;
}

function formatPercent(value) {
  if (typeof value !== "number") {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatMs(value) {
  if (typeof value !== "number") {
    return "n/a";
  }
  return `${value.toFixed(2)} ms`;
}

function formatBoolean(value) {
  if (value === true) {
    return "Yes";
  }
  if (value === false) {
    return "No";
  }
  return "n/a";
}

function formatAclPassed(record) {
  if (typeof record.passed === "boolean") {
    return formatBoolean(record.passed);
  }
  if (typeof record.failure === "boolean") {
    return formatBoolean(!record.failure);
  }
  return "n/a";
}
