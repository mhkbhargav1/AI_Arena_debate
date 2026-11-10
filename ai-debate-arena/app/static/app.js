const $ = (id) => document.getElementById(id);
const promptBox = $("prompt");
const runBtn = $("run");
let historyCache = [];

function showError(message) {
  $("error").textContent = message;
  $("error").classList.remove("hidden");
}
function hideError() { $("error").classList.add("hidden"); }
function setLoading(on, title = "The arena is working…", detail = "Getting independent answers from both models.") {
  $("loading").classList.toggle("hidden", !on);
  runBtn.disabled = on;
  runBtn.innerHTML = on ? "Debating…" : 'Start debate <span>→</span>';
  $("loadingTitle").textContent = title;
  $("loadingText").textContent = detail;
}
function safeText(id, value) { $(id).textContent = value || "No response returned."; }

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) throw new Error("Could not load history");
    historyCache = await res.json();
    const host = $("history");
    host.innerHTML = "";
    if (!historyCache.length) {
      host.innerHTML = '<p class="muted">No debates yet.</p>';
      return;
    }
    historyCache.forEach(item => {
      const btn = document.createElement("button");
      btn.textContent = item.prompt;
      btn.title = item.prompt;
      btn.addEventListener("click", () => openHistory(item.id));
      host.appendChild(btn);
    });
  } catch (_) {
    $("history").innerHTML = '<p class="muted">History unavailable.</p>';
  }
}

async function openHistory(id) {
  hideError();
  try {
    const res = await fetch(`/api/history/${id}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Could not open debate");
    renderResult(data);
  } catch (err) { showError(err.message); }
}

function renderResult(data) {
  $("welcome").classList.add("hidden");
  $("loading").classList.add("hidden");
  $("result").classList.remove("hidden");
  $("task").textContent = data.prompt;
  safeText("openaiAnswer", data.openai_answer);
  safeText("geminiAnswer", data.gemini_answer);
  safeText("openaiReview", data.openai_review || "Quick comparison mode: cross-review was skipped.");
  safeText("geminiReview", data.gemini_review || "Quick comparison mode: cross-review was skipped.");
  safeText("verdict", data.verdict);
  $("reviews").classList.toggle("hidden", !data.openai_review && !data.gemini_review);
  $("status").textContent = data.status || "Completed";
  $("result").scrollIntoView({behavior:"smooth", block:"start"});
}

async function startDebate() {
  const prompt = promptBox.value.trim();
  if (prompt.length < 3) { showError("Enter a task or question first."); promptBox.focus(); return; }
  hideError();
  $("result").classList.add("hidden");
  $("welcome").classList.add("hidden");
  setLoading(true);
  try {
    const res = await fetch("/api/debate", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({prompt, mode:$("mode").value})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "The debate failed.");
    renderResult(data);
    promptBox.value = "";
    await loadHistory();
  } catch (err) {
    showError(err.message || "Something went wrong.");
    $("welcome").classList.remove("hidden");
  } finally {
    setLoading(false);
  }
}

$("run").addEventListener("click", startDebate);
promptBox.addEventListener("keydown", e => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) startDebate();
});
$("newDebate").addEventListener("click", () => {
  $("result").classList.add("hidden");
  $("welcome").classList.remove("hidden");
  promptBox.focus();
  hideError();
});
loadHistory();
