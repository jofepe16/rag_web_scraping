const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const question = document.querySelector("#question");
const send = document.querySelector("#send");
const sessionLabel = document.querySelector("#session-id");

function createSession() {
  const id = `web_${crypto.randomUUID().replaceAll("-", "").slice(0, 16)}`;
  localStorage.setItem("rag_session_id", id);
  sessionLabel.textContent = id;
  return id;
}

let sessionId = localStorage.getItem("rag_session_id") || createSession();
sessionLabel.textContent = sessionId;

function appendMessage(role, content, sources = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const body = document.createElement("div");
  body.textContent = content;
  article.appendChild(body);
  if (sources.length) {
    const list = document.createElement("ul");
    list.className = "sources";
    sources.forEach((source) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = source.url; link.target = "_blank"; link.rel = "noopener noreferrer";
      link.textContent = source.title || source.url;
      item.appendChild(link); list.appendChild(item);
    });
    article.appendChild(list);
  }
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) return;
  appendMessage("user", value); question.value = ""; send.disabled = true;
  const pending = appendMessage("assistant", "Consultando las fuentes...");
  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({session_id: sessionId, question: value}),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "No fue posible obtener una respuesta.");
    pending.remove(); appendMessage("assistant", payload.answer, payload.sources);
  } catch (error) {
    pending.remove(); appendMessage("error", error.message);
  } finally { send.disabled = false; question.focus(); }
});

question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!send.disabled) form.requestSubmit();
  }
});

document.querySelector("#new-session").addEventListener("click", () => {
  sessionId = createSession();
  messages.innerHTML = "";
  appendMessage("assistant", "Nueva conversación iniciada. ¿Qué deseas consultar?");
});
