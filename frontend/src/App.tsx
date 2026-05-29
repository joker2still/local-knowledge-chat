import { FormEvent, useEffect, useState } from "react";

import { clearConversation, deleteConversation, listConversations, sendChat, uploadDocumentFile } from "./services/api";
import type { ChatMessage } from "./types";

function createSessionId(): string {
  return `local-chat-${Date.now()}`;
}

function App() {
  const [sessionId, setSessionId] = useState(() => createSessionId());
  const [savedSessions, setSavedSessions] = useState<string[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  const [question, setQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [conversationError, setConversationError] = useState("");

  useEffect(() => {
    void refreshSessions();
  }, []);

  async function refreshSessions() {
    setSessionsLoading(true);
    setConversationError("");
    try {
      const result = await listConversations();
      setSavedSessions(result.sessions);
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "Failed to load conversations.");
    } finally {
      setSessionsLoading(false);
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!selectedFile) {
      setUploadError("Please choose a .txt or .pdf file first.");
      return;
    }

    setUploadLoading(true);
    setUploadError("");
    setUploadMessage("");

    try {
      const result = await uploadDocumentFile(selectedFile);
      setUploadMessage(`Uploaded ${result.filename ?? selectedFile.name} (${result.chunks ?? 0} chunks).`);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleChat(event: FormEvent) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setChatError("Please enter a question.");
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatLoading(true);
    setChatError("");

    try {
      const result = await sendChat({
        session_id: sessionId,
        message: trimmedQuestion,
      });

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: result.answer,
        selected_tool: result.selected_tool,
        sources: result.sources,
      };

      setSessionId(result.session_id || sessionId);
      setMessages((current) => [...current, assistantMessage]);
      await refreshSessions();
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Chat failed.");
    } finally {
      setChatLoading(false);
    }
  }

  function handleNewChat() {
    setMessages([]);
    setQuestion("");
    setChatError("");
    setConversationError("");
    setSessionId(createSessionId());
  }

  async function handleClearCurrentChat() {
    try {
      await clearConversation(sessionId);
      setMessages([]);
      setChatError("");
      await refreshSessions();
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "Failed to clear conversation.");
    }
  }

  async function handleDeleteSession(targetSessionId: string) {
    try {
      await deleteConversation(targetSessionId);
      if (targetSessionId === sessionId) {
        setMessages([]);
        setChatError("");
      }
      await refreshSessions();
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "Failed to delete conversation.");
    }
  }

  return (
    <main style={{ maxWidth: 900, margin: "32px auto", padding: "0 16px", fontFamily: "Segoe UI, Arial, sans-serif" }}>
      <h1 style={{ marginBottom: 24 }}>Local Knowledge Chat</h1>

      <section style={{ border: "1px solid #d9d9d9", borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>Upload .txt / .pdf</h2>
        <form onSubmit={handleUpload}>
          <input
            type="file"
            accept=".txt,.pdf,text/plain,application/pdf"
            onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            disabled={uploadLoading}
          />
          <button type="submit" disabled={uploadLoading} style={{ marginLeft: 12 }}>
            {uploadLoading ? "Uploading..." : "Upload"}
          </button>
        </form>
        {uploadMessage && <p style={{ color: "#1f7a1f" }}>{uploadMessage}</p>}
        {uploadError && <p style={{ color: "#b00020" }}>{uploadError}</p>}
      </section>

      <section style={{ border: "1px solid #d9d9d9", borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h2 style={{ margin: 0 }}>Conversations</h2>
          <button type="button" onClick={refreshSessions} disabled={sessionsLoading}>
            {sessionsLoading ? "Loading..." : "Refresh"}
          </button>
        </div>

        <p style={{ color: "#666", marginTop: 0 }}>Current session: {sessionId}</p>

        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button type="button" onClick={handleClearCurrentChat} disabled={chatLoading || sessionsLoading}>
            Clear Current Chat
          </button>
          <button type="button" onClick={handleNewChat} disabled={chatLoading}>
            New Chat
          </button>
        </div>

        {conversationError && <p style={{ color: "#b00020" }}>{conversationError}</p>}

        <div style={{ border: "1px solid #e5e5e5", borderRadius: 8, padding: 12, background: "#fafafa" }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Saved Sessions</div>
          {savedSessions.length === 0 ? (
            <p style={{ margin: 0 }}>No saved sessions yet.</p>
          ) : (
            <ul style={{ paddingLeft: 20, margin: 0 }}>
              {savedSessions.map((savedSession) => (
                <li key={savedSession} style={{ marginBottom: 8 }}>
                  <span>{savedSession}</span>
                  <button
                    type="button"
                    onClick={() => void handleDeleteSession(savedSession)}
                    style={{ marginLeft: 12 }}
                    disabled={chatLoading || sessionsLoading}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section style={{ border: "1px solid #d9d9d9", borderRadius: 8, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Chat</h2>

        <div style={{ border: "1px solid #e5e5e5", borderRadius: 8, padding: 12, minHeight: 280, marginBottom: 16, background: "#fafafa" }}>
          {messages.length === 0 ? (
            <p style={{ margin: 0 }}>No messages yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    alignSelf: message.role === "user" ? "flex-end" : "stretch",
                    background: message.role === "user" ? "#e8f1ff" : "#ffffff",
                    border: "1px solid #d9d9d9",
                    borderRadius: 8,
                    padding: 12,
                  }}
                >
                  <div style={{ fontSize: 12, color: "#555", marginBottom: 6 }}>
                    {message.role === "user" ? "User" : "Assistant"}
                  </div>
                  <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>

                  {message.role === "assistant" && message.selected_tool && (
                    <div style={{ marginTop: 10, fontSize: 13, color: "#444" }}>
                      Tool: <strong>{message.selected_tool}</strong>
                    </div>
                  )}

                  {message.role === "assistant" && message.sources && message.sources.length > 0 && (
                    <div style={{ marginTop: 10 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Sources</div>
                      <ul style={{ paddingLeft: 20, margin: 0 }}>
                        {message.sources.map((item, index) => (
                          <li key={`${message.id}-${item.chunk_id}-${index}`} style={{ marginBottom: 8 }}>
                            <strong>{item.source || "unknown"}</strong> | chunk: {item.chunk_id || "-"} | score: {item.score.toFixed(4)}
                            {item.page_number ? ` | page: ${item.page_number}` : ""}
                            {item.file_type ? ` | type: ${item.file_type}` : ""}
                            <div>{item.preview}</div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <form onSubmit={handleChat} style={{ display: "flex", gap: 8 }}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question from uploaded docs..."
            disabled={chatLoading}
            style={{ flex: 1, padding: "8px 10px" }}
          />
          <button type="submit" disabled={chatLoading}>
            {chatLoading ? "Thinking..." : "Send"}
          </button>
        </form>

        {chatError && <p style={{ color: "#b00020" }}>{chatError}</p>}
      </section>
    </main>
  );
}

export default App;
