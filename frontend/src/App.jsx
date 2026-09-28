import { useEffect, useMemo, useRef, useState } from "react";

const DEMO_PROMPTS = [
  "Tell me about Project Apollo.",
  "The Payment Service had an incident recently. What was affected, who owns the dependency, and what does the relevant runbook recommend?",
  "Who owns Identity Service, and which customers depend on it?",
];

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.headers.get("content-type")?.includes("text/event-stream")) {
    return response;
  }
  return response.json();
}

function parseSseChunk(buffer, onEvent) {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() || "";
  for (const part of parts) {
    const event = (part.match(/^event: (.+)$/m) || [])[1];
    const data = (part.match(/^data: (.+)$/m) || [])[1];
    if (event && data) {
      onEvent(event, JSON.parse(data));
    }
  }
  return rest;
}

export default function App() {
  const [users, setUsers] = useState([]);
  const [userId, setUserId] = useState("sameer.kulkarni");
  const [sessions, setSessions] = useState([]);
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [memories, setMemories] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [trace, setTrace] = useState([]);
  const [error, setError] = useState("");
  const endRef = useRef(null);

  const currentUser = useMemo(
    () => users.find((user) => user.user_id === userId),
    [users, userId]
  );

  async function refresh(nextUser = userId, nextSession = sessionId) {
    const [userPayload, sessionPayload, memoryPayload] = await Promise.all([
      api("/api/users"),
      api(`/api/sessions?user_id=${nextUser}`),
      api(`/api/memory?user_id=${nextUser}`),
    ]);
    setUsers(userPayload.users);
    setSessions(sessionPayload.sessions);
    setMemories(memoryPayload.memories);
    let active = nextSession;
    if (!active || !sessionPayload.sessions.some((row) => row.id === active)) {
      const created = await api("/api/sessions", {
        method: "POST",
        body: JSON.stringify({ user_id: nextUser, title: "New conversation" }),
      });
      active = created.id;
      const refreshed = await api(`/api/sessions?user_id=${nextUser}`);
      setSessions(refreshed.sessions);
    }
    setSessionId(active);
    const history = await api(`/api/sessions/${active}/messages?user_id=${nextUser}`);
    setMessages(history.messages);
  }

  useEffect(() => {
    refresh(userId, "").catch((err) => setError(err.message));
  }, [userId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(text) {
    const message = (text || input).trim();
    if (!message || !sessionId || busy) return;
    setInput("");
    setBusy(true);
    setError("");
    setTrace([]);
    setMessages((prev) => [...prev, { role: "user", content: message, citations: [] }]);
    let assistant = { role: "assistant", content: "", citations: [], tool_trace: [] };
    setMessages((prev) => [...prev, assistant]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
      });
      if (!response.ok || !response.body) {
        throw new Error(await response.text());
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer = parseSseChunk(buffer + decoder.decode(value, { stream: true }), (event, data) => {
          if (event === "token") {
            assistant = { ...assistant, content: assistant.content + data.text };
            setMessages((prev) => [...prev.slice(0, -1), assistant]);
          }
          if (event === "tool_start" || event === "tool_result") {
            setTrace((prev) => [...prev, { event, ...data }]);
          }
          if (event === "done") {
            assistant = {
              ...assistant,
              citations: data.citations || [],
              tool_trace: data.tool_trace || [],
            };
            setMessages((prev) => [...prev.slice(0, -1), assistant]);
          }
          if (event === "error") {
            setError(data.error);
          }
        });
      }
      const memoryPayload = await api(`/api/memory?user_id=${userId}`);
      setMemories(memoryPayload.memories);
      const sessionPayload = await api(`/api/sessions?user_id=${userId}`);
      setSessions(sessionPayload.sessions);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Nexora Assistant</h1>
        <div className="sub">Internal operations copilot</div>
        <label htmlFor="user">Signed in as</label>
        <select id="user" value={userId} onChange={(event) => setUserId(event.target.value)}>
          {users.map((user) => (
            <option key={user.user_id} value={user.user_id}>
              {user.name} — {user.role}
            </option>
          ))}
        </select>
        <button
          className="secondary"
          onClick={() =>
            api("/api/sessions", {
              method: "POST",
              body: JSON.stringify({ user_id: userId, title: "New conversation" }),
            }).then((created) => refresh(userId, created.id))
          }
        >
          New session
        </button>
        <h2>Sessions</h2>
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session ${session.id === sessionId ? "active" : ""}`}
            onClick={() => refresh(userId, session.id)}
          >
            {session.title}
            <small>{session.updated_at}</small>
          </div>
        ))}
        <h2>Remembered about you</h2>
        {memories.length === 0 && <div className="empty">No memories yet.</div>}
        {memories.map((memory) => (
          <div className="mem" key={memory.key}>
            <b>{memory.key}</b>: {memory.value}
          </div>
        ))}
      </aside>

      <main className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <div className="bubble">
              <div className="who">Nexora Assistant</div>
              Ask about projects, ownership, incidents, dependencies, and runbooks.
              {currentUser ? ` You are ${currentUser.name}.` : ""}
              <div className="citations">
                {DEMO_PROMPTS.map((prompt) => (
                  <div key={prompt}>
                    <a href="#" onClick={(event) => { event.preventDefault(); send(prompt); }}>
                      {prompt}
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
              <div className="who">{message.role === "user" ? currentUser?.name || "You" : "Nexora Assistant"}</div>
              {message.content}
              {message.citations?.length > 0 && (
                <div className="citations">
                  {message.citations.map((citation) => (
                    <div key={citation.path}>Source: {citation.path}{citation.heading ? ` — ${citation.heading}` : ""}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {error && <div className="bubble">{error}</div>}
          <div ref={endRef} />
        </div>
        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            send();
          }}
        >
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask a follow-up. Example: Who owns it?"
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send();
              }
            }}
          />
          <button type="submit" disabled={busy}>{busy ? "Working" : "Send"}</button>
        </form>
      </main>

      <aside className="trace">
        <h2>Tool trace</h2>
        {trace.length === 0 && <div className="empty">Tool calls will appear here.</div>}
        {trace.map((item, index) => (
          <div className="tool" key={`${item.name}-${index}`}>
            <b>{item.name}</b>
            {item.input && <pre>{JSON.stringify(item.input, null, 2)}</pre>}
            {item.result && <pre>{JSON.stringify(item.result, null, 2)}</pre>}
          </div>
        ))}
      </aside>
    </div>
  );
}
