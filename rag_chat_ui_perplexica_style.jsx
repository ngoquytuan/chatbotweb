/*
RAG Chat UI - Perplexica-style (React + Tailwind)

- Single-file React component (Next.js / Vite compatible)
- Default-export component named `RagChatUI` so you can drop into a page.
- Uses Tailwind for styling (assumes Tailwind is configured).
- Communicates with backend via:
    - SSE: /api/query/stream  (EventSource streaming JSON messages)
    - REST: POST /api/chat (fallback or non-streaming)
    - POST /api/upload (file upload for indexing)
- Features included:
    - Chat input + streaming token rendering
    - Focus Mode (dropdown filters)
    - Conversation list (sessions)
    - Sources / citations panel
    - File upload panel (admin)
    - Health & simple metrics panel (poll /api/health and /api/metrics)

How to use:
- Drop this file into your frontend project (e.g. app/components/RagChatUI.tsx)
- Import into a page and render: <RagChatUI />
- Ensure backend endpoints exist or mock them for testing.

Note: This implementation is an original scaffold inspired by Perplexica UX patterns
and intentionally written to be modular and easy to extend.
*/

import React, { useEffect, useRef, useState } from "react";

type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  createdAt: number;
  sources?: Array<{ doc_id: string; section?: string; score?: number }>; 
};

export default function RagChatUI() {
  // conversation state (simple in-memory store)
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [focusMode, setFocusMode] = useState<string>("all");
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessions, setSessions] = useState<Array<{ id: string; title: string }>>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [sources, setSources] = useState<Message["sources"] | null>(null);
  const [health, setHealth] = useState<{ ok: boolean; text?: string }>({ ok: false });
  const [metrics, setMetrics] = useState<Record<string, any> | null>(null);

  const messagesRef = useRef<Message[]>(messages);
  useEffect(() => { messagesRef.current = messages; }, [messages]);

  const outputRef = useRef<HTMLDivElement | null>(null);

  // basic helper to add message
  function pushMessage(msg: Message) {
    setMessages(prev => [...prev, msg]);
  }

  // polling health & metrics
  useEffect(() => {
    let t: any;
    async function poll() {
      try {
        const r = await fetch(`/api/health`);
        const j = await r.json();
        setHealth({ ok: j.ok ?? true, text: j.message ?? undefined });
      } catch (e) {
        setHealth({ ok: false, text: "unreachable" });
      }

      try {
        const m = await fetch(`/api/metrics`).then(r=>r.json()).catch(()=>null);
        setMetrics(m);
      } catch {}

      t = setTimeout(poll, 5000);
    }
    poll();
    return () => clearTimeout(t);
  }, []);

  // create a new session
  function newSession() {
    const id = `sess-${Date.now()}`;
    setSessions(s => [{ id, title: "New conversation" }, ...s]);
    setActiveSession(id);
    setMessages([]);
  }

  // send query using SSE streaming
  async function sendQueryStreaming(question: string) {
    if (!question.trim()) return;
    const msgId = `u-${Date.now()}`;
    const userMsg: Message = { id: msgId, role: "user", text: question, createdAt: Date.now() };
    pushMessage(userMsg);
    setInput("");

    // assistant placeholder
    const assistantId = `a-${Date.now()}`;
    pushMessage({ id: assistantId, role: "assistant", text: "", createdAt: Date.now(), sources: [] });
    setIsStreaming(true);

    // build url with query params for focus mode
    const url = `/api/query/stream`;

    const sse = new EventSourcePolyfill(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: question, filters: { category: focusMode === "all" ? undefined : focusMode }, top_k: 6 })
    });

    // accumulate assistant text
    let buffer = "";

    sse.onmessage = (ev: MessageEvent) => {
      try {
        const payload = JSON.parse(ev.data);
        if (payload.type === "token") {
          buffer += payload.text;
          // update last assistant
          setMessages(prev => {
            const copy = [...prev];
            const idx = copy.findIndex(m => m.id === assistantId);
            if (idx >= 0) {
              copy[idx] = { ...copy[idx], text: buffer };
            }
            return copy;
          });
        } else if (payload.type === "sources") {
          // show sources panel
          setSources(payload.items || []);
        } else if (payload.type === "done") {
          setIsStreaming(false);
          sse.close();
        }
      } catch (e) {
        console.warn("Malformed event payload", e);
      }
    };

    sse.onerror = (ev) => {
      console.error("SSE error", ev);
      setIsStreaming(false);
      try { sse.close(); } catch (e) {}
    };
  }

  // fallback to non-streaming POST
  async function sendQueryOnce(question: string) {
    if (!question.trim()) return;
    const msgId = `u-${Date.now()}`;
    const userMsg: Message = { id: msgId, role: "user", text: question, createdAt: Date.now() };
    pushMessage(userMsg);
    setInput("");
    const assistantId = `a-${Date.now()}`;
    pushMessage({ id: assistantId, role: "assistant", text: "(thinking...)", createdAt: Date.now() });

    try {
      const r = await fetch(`/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q: question, filters: { category: focusMode === "all" ? undefined : focusMode } })
      });
      const j = await r.json();
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, text: j.answer ?? "(no answer)", sources: j.sources ?? [] } : m));
    } catch (e) {
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, text: "(error)" } : m));
    }
  }

  // submit handler decides streaming vs batch
  function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!input.trim()) return;
    // prefer streaming if endpoint available
    sendQueryStreaming(input).catch(()=>sendQueryOnce(input));
  }

  // file upload helper
  async function handleUpload(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("meta", JSON.stringify({ category: "huong_dan" }));
    try {
      const r = await fetch(`/api/upload`, { method: "POST", body: fd });
      const j = await r.json();
      alert("Upload queued: " + (j.ingest_id || "ok"));
    } catch (e) {
      alert("Upload failed");
    }
  }

  // small helper to scroll to bottom on messages change
  useEffect(() => {
    const el = outputRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  // lightweight EventSource polyfill using fetch + ReadableStream for browsers that don't allow POST with EventSource
  function EventSourcePolyfill(url: string, opts: { method: string; headers?: Record<string,string>; body?: string }) {
    // returns an object with onmessage, onerror, close()
    // For simplicity we use Fetch + streaming text; backend should send newline-delimited JSON lines (`\n`).
    let controller = new AbortController();
    const emitter: any = {};
    (async () => {
      try {
        const res = await fetch(url, { signal: controller.signal, method: opts.method as any, headers: opts.headers, body: opts.body });
        if (!res.body) {
          emitter.onerror && emitter.onerror(new Error("No body"));
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          let lines = buf.split(/\n/);
          buf = lines.pop() || "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            try { emitter.onmessage && emitter.onmessage({ data: trimmed }); } catch(e){ console.error(e);} 
          }
        }
        emitter.onmessage && emitter.onmessage({ data: JSON.stringify({ type: 'done' }) });
      } catch (e:any) {
        if (e.name === 'AbortError') return;
        emitter.onerror && emitter.onerror(e);
      }
    })();
    emitter.close = () => controller.abort();
    return emitter;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-80 bg-white border-r p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">RAG Local</h2>
          <button onClick={newSession} className="text-sm px-2 py-1 bg-indigo-600 text-white rounded">New</button>
        </div>

        <div className="mb-3">
          <label className="block text-xs text-gray-500">Focus Mode</label>
          <select value={focusMode} onChange={e=>setFocusMode(e.target.value)} className="w-full mt-1 border rounded p-2">
            <option value="all">All</option>
            <option value="quy_dinh">Quy định</option>
            <option value="quy_che">Quy chế</option>
            <option value="huong_dan">Hướng dẫn</option>
            <option value="san_pham">Sản phẩm</option>
          </select>
        </div>

        <div className="mb-3 flex-1 overflow-auto">
          <h3 className="text-xs text-gray-500 mb-2">Sessions</h3>
          <ul className="space-y-2">
            {sessions.length === 0 && <li className="text-sm text-gray-400">No sessions yet</li>}
            {sessions.map(s => (
              <li key={s.id} className={`p-2 rounded cursor-pointer ${activeSession===s.id? 'bg-indigo-50':''}`} onClick={()=>setActiveSession(s.id)}>
                <div className="text-sm font-medium">{s.title}</div>
                <div className="text-xs text-gray-400">{new Date(Number(s.id.split('-')[1])).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-auto">
          <div className="text-xs text-gray-500 mb-2">Health</div>
          <div className="flex items-center gap-2">
            <div className={`h-3 w-3 rounded-full ${health.ok ? 'bg-green-400':'bg-red-400'}`}></div>
            <div className="text-sm">{health.ok ? 'OK' : 'DOWN'}</div>
          </div>
          <div className="mt-2 text-xs text-gray-400">Metrics: {metrics ? JSON.stringify(metrics).slice(0,80)+'...' : 'n/a'}</div>
        </div>
      </aside>

      {/* Main chat */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1 p-6 overflow-auto" ref={outputRef}>
          <div className="max-w-3xl mx-auto">
            {messages.map(m => (
              <div key={m.id} className={`mb-4 ${m.role==='user' ? 'text-right' : 'text-left'}`}>
                <div className={`inline-block p-3 rounded-lg ${m.role==='user' ? 'bg-indigo-600 text-white' : 'bg-white border'}`}>
                  <div className="whitespace-pre-wrap">{m.text}</div>
                </div>
                {m.sources && m.sources.length>0 && (
                  <div className="mt-1 text-xs text-gray-500">Sources: {m.sources.map(s=>s.doc_id).join(', ')}</div>
                )}
              </div>
            ))}

            {isStreaming && (
              <div className="text-sm text-gray-500">Streaming response…</div>
            )}

            {(!messages || messages.length===0) && (
              <div className="text-center text-gray-400 mt-20">Start a new conversation — choose focus mode and ask a question.</div>
            )}
          </div>
        </div>

        {/* Input bar */}
        <form onSubmit={handleSubmit} className="border-t p-4 bg-white">
          <div className="max-w-3xl mx-auto flex items-end gap-2">
            <textarea value={input} onChange={e=>setInput(e.target.value)} rows={2} className="flex-1 border rounded p-2" placeholder="Ask a question... (Shift+Enter for newline)" />
            <input id="file-upload" type="file" onChange={e=>e.target.files && handleUpload(e.target.files[0])} className="hidden" />
            <label htmlFor="file-upload" className="text-sm px-3 py-2 bg-gray-100 rounded cursor-pointer">Upload</label>
            <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Send</button>
          </div>
        </form>
      </main>

      {/* Right panel: sources / tools */}
      <aside className="w-96 bg-white border-l p-4">
        <h3 className="font-semibold mb-2">Sources & Tools</h3>
        <div className="mb-4">
          <div className="text-xs text-gray-500">Highlighted sources for last answer</div>
          {!sources && <div className="text-sm text-gray-400 mt-2">No sources yet</div>}
          {sources && (
            <ul className="mt-2 space-y-2">
              {sources.map((s:any, idx:number) => (
                <li key={idx} className="p-2 border rounded">
                  <div className="text-sm font-medium">{s.doc_id}</div>
                  <div className="text-xs text-gray-500">section: {s.section ?? 'n/a'} • score: {s.score?.toFixed?.(2) ?? s.score}</div>
                  <div className="text-xs text-gray-600 mt-2">{s.excerpt ? s.excerpt.slice(0,200) : ''}</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-6">
          <h4 className="text-sm font-medium mb-1">Tools</h4>
          <button className="w-full text-left p-2 border rounded mb-2">Export chat</button>
          <button className="w-full text-left p-2 border rounded">Clear conversation</button>
        </div>
      </aside>
    </div>
  );
}
