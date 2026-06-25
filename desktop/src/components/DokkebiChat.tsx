import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { checkHealth, postGoal } from "../lib/api";
import "./DokkebiChat.css";

type Message = { role: "user" | "assistant"; text: string };

export function DokkebiChat() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);
  const [debateMode, setDebateMode] = useState(false);

  useEffect(() => {
    checkHealth().then(setOnline);
    const id = window.setInterval(() => {
      checkHealth().then(setOnline);
    }, 15000);
    return () => window.clearInterval(id);
  }, []);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);
    try {
      const result = await postGoal(text, { debate: debateMode });
      setMessages((prev) => [...prev, { role: "assistant", text: result.response }]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [...prev, { role: "assistant", text: msg }]);
    } finally {
      setLoading(false);
    }
  }, [debateMode, input, loading]);

  return (
    <section className="dokkebi-chat">
      <header className="dokkebi-chat__status">
        <span
          className={
            online === null
              ? "dot dot--unknown"
              : online
                ? "dot dot--ok"
                : "dot dot--err"
          }
        />
        {online ? t("chat.backend_ok") : t("chat.backend_down")}
      </header>

      <div className="dokkebi-chat__messages">
        {messages.length === 0 && (
          <p className="dokkebi-chat__empty">{t("chat.empty")}</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble bubble--${m.role}`}>
            <pre>{m.text}</pre>
          </div>
        ))}
        {loading && <p className="dokkebi-chat__loading">{t("chat.thinking")}</p>}
      </div>

      <footer className="dokkebi-chat__composer">
        <label className="debate-toggle">
          <input
            type="checkbox"
            checked={debateMode}
            onChange={(e) => setDebateMode(e.target.checked)}
          />
          {t("chat.debate")}
        </label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("chat.placeholder")}
          rows={3}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <button type="button" onClick={() => void send()} disabled={loading}>
          {t("chat.send")}
        </button>
      </footer>
    </section>
  );
}
