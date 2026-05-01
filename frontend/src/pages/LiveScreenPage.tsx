import { useEffect, useMemo, useRef, useState } from "react";

export default function LiveScreenPage() {
  const [sessionId, setSessionId] = useState("sample-session");
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  const statusText = useMemo(() => (connected ? "Connected" : "Disconnected"), [connected]);

  const connect = () => {
    socketRef.current?.close();
    const socket = new WebSocket(`${window.location.origin.replace("http", "ws")}/ws/live/${sessionId}/`);
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => setMessages((current) => [...current.slice(-12), event.data]);
    socketRef.current = socket;
  };

  const sendPing = () => {
    socketRef.current?.send(JSON.stringify({ type: "ping", at: new Date().toISOString() }));
  };

  return (
    <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
      <article className="rounded-2xl bg-white shadow border border-slate-200 p-5 space-y-4">
        <div>
          <h2 className="text-xl font-bold">Live QA Screen Viewer</h2>
          <p className="text-sm text-slate-600">Super Admin only. WebRTC signaling runs over Django Channels and Redis.</p>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <input className="rounded-lg border border-slate-300 px-3 py-2" value={sessionId} onChange={(e) => setSessionId(e.target.value)} placeholder="Session ID" />
          <button className="rounded-lg bg-steel px-4 py-2 text-white" onClick={connect}>Connect</button>
          <button className="rounded-lg bg-copper px-4 py-2 text-white" onClick={sendPing} disabled={!connected}>Signal Ping</button>
        </div>

        <div className="rounded-xl bg-slate-950 text-slate-100 p-4 min-h-64">
          <div className="mb-3 flex items-center justify-between text-sm text-slate-300">
            <span>Status</span>
            <span>{statusText}</span>
          </div>
          <div className="aspect-video rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center text-sm text-slate-400">
            Video render area for incoming WebRTC stream
          </div>
        </div>
      </article>

      <aside className="rounded-2xl bg-white shadow border border-slate-200 p-5">
        <h3 className="text-lg font-semibold mb-3">Signaling Events</h3>
        <div className="space-y-2 text-sm">
          {messages.length === 0 ? <p className="text-slate-500">No events yet.</p> : messages.map((message, index) => (
            <div key={`${index}-${message}`} className="rounded-lg bg-slate-50 p-3 border border-slate-200 break-words">{message}</div>
          ))}
        </div>
      </aside>
    </section>
  );
}
