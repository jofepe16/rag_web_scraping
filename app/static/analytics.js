const labels = {
  total_sessions: "Sesiones", total_messages: "Mensajes", total_questions: "Preguntas",
  average_response_latency_ms: "Latencia promedio (ms)", active_days: "Días activos",
  average_questions_per_session: "Preguntas por sesión",
};

Promise.all([fetch("/api/v1/analytics"), fetch("/api/v1/conversations?limit=50")])
  .then(async ([metricsResponse, sessionsResponse]) => {
    if (!metricsResponse.ok || !sessionsResponse.ok) throw new Error("No se pudieron cargar los datos.");
    const metrics = await metricsResponse.json(); const sessions = await sessionsResponse.json();
    document.querySelector("#metrics").innerHTML = Object.entries(metrics).map(([key, value]) =>
      `<article class="metric"><span>${labels[key] || key}</span><strong>${value}</strong></article>`).join("");
    document.querySelector("#sessions").innerHTML = sessions.items.map((session) =>
      `<tr><td><code>${session.session_id}</code></td><td>${session.message_count}</td><td>${new Date(session.updated_at).toLocaleString("es-CO")}</td></tr>`).join("");
  }).catch((error) => { document.querySelector("#metrics").textContent = error.message; });

