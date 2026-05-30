import { FormEvent, useEffect, useState } from "react";
import type { CSSProperties } from "react";

import {
  clearConversation,
  deleteConversation,
  deleteDocument,
  getDocumentChunks,
  listConversations,
  listDocuments,
  sendChat,
  summarizeDocument,
  uploadDocumentFile,
} from "./services/api";
import type { ChatMessage, DocumentChunk, DocumentItem } from "./types";

function createSessionId(): string {
  return `local-chat-${Date.now()}`;
}

function formatPreview(text: string): string {
  return text.length > 180 ? `${text.slice(0, 180)}...` : text;
}

export default function App() {
  const [sessionId, setSessionId] = useState<string>(() => createSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const [savedSessions, setSavedSessions] = useState<string[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [conversationError, setConversationError] = useState("");

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState("");
  const [documentChunks, setDocumentChunks] = useState<Record<string, DocumentChunk[]>>({});
  const [documentSummaries, setDocumentSummaries] = useState<Record<string, string>>({});
  const [expandedDocuments, setExpandedDocuments] = useState<Record<string, boolean>>({});
  const [documentActionLoading, setDocumentActionLoading] = useState<Record<string, string>>({});

  async function refreshSessions(): Promise<void> {
    setSessionsLoading(true);
    setConversationError("");
    try {
      const data = await listConversations();
      setSavedSessions(data.sessions);
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "Failed to load conversations");
    } finally {
      setSessionsLoading(false);
    }
  }

  async function refreshDocuments(): Promise<void> {
    setDocumentsLoading(true);
    setDocumentsError("");
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to load documents");
    } finally {
      setDocumentsLoading(false);
    }
  }

  useEffect(() => {
    void refreshSessions();
    void refreshDocuments();
  }, []);

  async function handleUpload(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = formData.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setUploadError("Please choose a .txt or .pdf file.");
      setUploadMessage("");
      return;
    }

    setUploadLoading(true);
    setUploadError("");
    setUploadMessage("");

    try {
      const data = await uploadDocumentFile(file);
      setUploadMessage(`Uploaded ${data.filename ?? file.name} with ${data.chunks ?? 0} chunks.`);
      form.reset();
      await refreshDocuments();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleSendMessage(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatLoading(true);
    setChatError("");

    try {
      const response = await sendChat({
        session_id: sessionId,
        message: trimmedQuestion,
      });

      const assistantMessage: ChatMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: response.answer,
        selected_tool: response.selected_tool,
        sources: response.sources,
      };

      setSessionId(response.session_id || sessionId);
      setMessages((current) => [...current, assistantMessage]);
      await refreshSessions();
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Chat request failed");
    } finally {
      setChatLoading(false);
    }
  }

  async function handleClearCurrentChat(): Promise<void> {
    setConversationError("");
    try {
      await clearConversation(sessionId);
      setMessages([]);
      await refreshSessions();
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "Failed to clear current chat");
    }
  }

  async function handleDeleteSession(targetSessionId: string): Promise<void> {
    setConversationError("");
    try {
      await deleteConversation(targetSessionId);
      if (targetSessionId === sessionId) {
        setMessages([]);
      }
      await refreshSessions();
    } catch (error) {
      setConversationError(error instanceof Error ? error.message : "Failed to delete session");
    }
  }

  function handleNewChat(): void {
    setSessionId(createSessionId());
    setMessages([]);
    setChatError("");
  }

  async function handleViewChunks(docId: string): Promise<void> {
    const isExpanded = expandedDocuments[docId];
    if (isExpanded) {
      setExpandedDocuments((current) => ({ ...current, [docId]: false }));
      return;
    }

    if (documentChunks[docId]) {
      setExpandedDocuments((current) => ({ ...current, [docId]: true }));
      return;
    }

    setDocumentActionLoading((current) => ({ ...current, [docId]: "chunks" }));
    setDocumentsError("");

    try {
      const data = await getDocumentChunks(docId);
      setDocumentChunks((current) => ({ ...current, [docId]: data.chunks }));
      setExpandedDocuments((current) => ({ ...current, [docId]: true }));
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to load chunks");
    } finally {
      setDocumentActionLoading((current) => ({ ...current, [docId]: "" }));
    }
  }

  async function handleSummarizeDocument(docId: string): Promise<void> {
    setDocumentActionLoading((current) => ({ ...current, [docId]: "summary" }));
    setDocumentsError("");

    try {
      const data = await summarizeDocument(docId);
      setDocumentSummaries((current) => ({ ...current, [docId]: data.summary }));
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to summarize document");
    } finally {
      setDocumentActionLoading((current) => ({ ...current, [docId]: "" }));
    }
  }

  async function handleDeleteDocument(docId: string): Promise<void> {
    const confirmed = window.confirm(`Delete document "${docId}"?`);
    if (!confirmed) {
      return;
    }

    setDocumentActionLoading((current) => ({ ...current, [docId]: "delete" }));
    setDocumentsError("");

    try {
      await deleteDocument(docId);
      setDocumentChunks((current) => {
        const next = { ...current };
        delete next[docId];
        return next;
      });
      setDocumentSummaries((current) => {
        const next = { ...current };
        delete next[docId];
        return next;
      });
      setExpandedDocuments((current) => {
        const next = { ...current };
        delete next[docId];
        return next;
      });
      await refreshDocuments();
    } catch (error) {
      setDocumentsError(error instanceof Error ? error.message : "Failed to delete document");
    } finally {
      setDocumentActionLoading((current) => ({ ...current, [docId]: "" }));
    }
  }

  return (
    <main
      style={{
        maxWidth: 960,
        margin: "32px auto",
        padding: "0 16px 40px",
        fontFamily: "Segoe UI, Arial, sans-serif",
        color: "#1f2937",
      }}
    >
      <h1 style={{ marginBottom: 8 }}>Local Knowledge Chat</h1>
      <p style={{ marginTop: 0, color: "#4b5563" }}>Upload documents, manage indexed files, and chat against your local knowledge base.</p>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Upload</h2>
        <form onSubmit={handleUpload} style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <input type="file" name="file" accept=".txt,.pdf" />
          <button type="submit" disabled={uploadLoading} style={buttonStyle}>
            {uploadLoading ? "Uploading..." : "Upload"}
          </button>
        </form>
        {uploadMessage ? <p style={successTextStyle}>{uploadMessage}</p> : null}
        {uploadError ? <p style={errorTextStyle}>{uploadError}</p> : null}
      </section>

      <section style={sectionStyle}>
        <div style={sectionHeaderRowStyle}>
          <div>
            <h2 style={sectionTitleStyle}>Conversations</h2>
            <p style={{ margin: "4px 0 0", color: "#4b5563" }}>Current session: {sessionId}</p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" onClick={() => void refreshSessions()} disabled={sessionsLoading} style={buttonStyle}>
              {sessionsLoading ? "Refreshing..." : "Refresh Sessions"}
            </button>
            <button type="button" onClick={() => void handleClearCurrentChat()} style={buttonStyle}>
              Clear Current Chat
            </button>
            <button type="button" onClick={handleNewChat} style={buttonStyle}>
              New Chat
            </button>
          </div>
        </div>
        {conversationError ? <p style={errorTextStyle}>{conversationError}</p> : null}
        <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
          {savedSessions.length === 0 ? (
            <p style={mutedTextStyle}>No saved sessions.</p>
          ) : (
            savedSessions.map((savedSession) => (
              <div key={savedSession} style={cardRowStyle}>
                <span style={{ wordBreak: "break-all" }}>{savedSession}</span>
                <button type="button" onClick={() => void handleDeleteSession(savedSession)} style={secondaryButtonStyle}>
                  Delete
                </button>
              </div>
            ))
          )}
        </div>
      </section>

      <section style={sectionStyle}>
        <div style={sectionHeaderRowStyle}>
          <div>
            <h2 style={sectionTitleStyle}>Documents</h2>
            <p style={{ margin: "4px 0 0", color: "#4b5563" }}>
              {documents.length} files, {documents.reduce((total, item) => total + item.chunks, 0)} chunks
            </p>
          </div>
          <button type="button" onClick={() => void refreshDocuments()} disabled={documentsLoading} style={buttonStyle}>
            {documentsLoading ? "Refreshing..." : "Refresh Documents"}
          </button>
        </div>
        {documentsError ? <p style={errorTextStyle}>{documentsError}</p> : null}
        <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
          {documents.length === 0 ? (
            <p style={mutedTextStyle}>No uploaded documents yet.</p>
          ) : (
            documents.map((document) => {
              const loadingState = documentActionLoading[document.filename] ?? "";
              const chunks = documentChunks[document.filename] ?? [];
              const summary = documentSummaries[document.filename];
              const isExpanded = expandedDocuments[document.filename] ?? false;

              return (
                <article key={document.filename} style={documentCardStyle}>
                  <div style={sectionHeaderRowStyle}>
                    <div>
                      <h3 style={{ margin: 0 }}>{document.filename}</h3>
                      <p style={{ margin: "6px 0 0", color: "#4b5563" }}>
                        Type: {document.file_type || "unknown"} | Chunks: {document.chunks}
                        {document.page_count ? ` | Pages: ${document.page_count}` : ""}
                      </p>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button type="button" onClick={() => void handleViewChunks(document.filename)} disabled={loadingState === "chunks"} style={buttonStyle}>
                        {loadingState === "chunks" ? "Loading..." : isExpanded ? "Hide Chunks" : "View Chunks"}
                      </button>
                      <button type="button" onClick={() => void handleSummarizeDocument(document.filename)} disabled={loadingState === "summary"} style={buttonStyle}>
                        {loadingState === "summary" ? "Summarizing..." : "Summarize"}
                      </button>
                      <button type="button" onClick={() => void handleDeleteDocument(document.filename)} disabled={loadingState === "delete"} style={dangerButtonStyle}>
                        {loadingState === "delete" ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>

                  {summary ? (
                    <div style={{ marginTop: 12 }}>
                      <strong>Summary</strong>
                      <p style={{ margin: "8px 0 0", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{summary}</p>
                    </div>
                  ) : null}

                  {isExpanded ? (
                    <div style={{ marginTop: 12 }}>
                      <strong>Chunks</strong>
                      <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                        {chunks.length === 0 ? (
                          <p style={mutedTextStyle}>No chunks found.</p>
                        ) : (
                          chunks.map((chunk) => (
                            <div key={chunk.chunk_id} style={chunkCardStyle}>
                              <div style={{ fontSize: 14, color: "#4b5563", marginBottom: 6 }}>
                                {chunk.chunk_id}
                                {chunk.page_number ? ` | Page ${chunk.page_number}` : ""}
                                {chunk.file_type ? ` | ${chunk.file_type}` : ""}
                              </div>
                              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{chunk.preview || formatPreview(chunk.text)}</div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  ) : null}
                </article>
              );
            })
          )}
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Chat</h2>
        <div style={chatListStyle}>
          {messages.length === 0 ? (
            <p style={mutedTextStyle}>No messages yet.</p>
          ) : (
            messages.map((message) => (
              <article
                key={message.id}
                style={{
                  ...messageCardStyle,
                  backgroundColor: message.role === "user" ? "#eff6ff" : "#f9fafb",
                  borderColor: message.role === "user" ? "#bfdbfe" : "#e5e7eb",
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 8 }}>{message.role === "user" ? "User" : "Assistant"}</div>
                <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{message.content}</div>
                {message.role === "assistant" && message.selected_tool ? (
                  <p style={{ margin: "10px 0 0", color: "#4b5563" }}>Selected tool: {message.selected_tool}</p>
                ) : null}
                {message.role === "assistant" && message.sources && message.sources.length > 0 ? (
                  <div style={{ marginTop: 12 }}>
                    <strong>Sources</strong>
                    <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                      {message.sources.map((source, index) => (
                        <div key={`${message.id}-${source.chunk_id}-${index}`} style={chunkCardStyle}>
                          <div style={{ fontSize: 14, color: "#4b5563", marginBottom: 6 }}>
                            {source.source} | {source.chunk_id} | score {source.score.toFixed(3)}
                            {source.page_number ? ` | Page ${source.page_number}` : ""}
                            {source.file_type ? ` | ${source.file_type}` : ""}
                          </div>
                          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{source.preview}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </article>
            ))
          )}
        </div>
        <form onSubmit={handleSendMessage} style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <input
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question about your documents"
            style={inputStyle}
          />
          <button type="submit" disabled={chatLoading} style={buttonStyle}>
            {chatLoading ? "Sending..." : "Send"}
          </button>
        </form>
        {chatError ? <p style={errorTextStyle}>{chatError}</p> : null}
      </section>
    </main>
  );
}

const sectionStyle: CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 20,
  marginTop: 20,
  backgroundColor: "#ffffff",
  boxShadow: "0 2px 10px rgba(15, 23, 42, 0.04)",
};

const sectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: 20,
};

const sectionHeaderRowStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  flexWrap: "wrap",
  alignItems: "center",
};

const buttonStyle: CSSProperties = {
  border: "1px solid #d1d5db",
  borderRadius: 8,
  padding: "8px 14px",
  backgroundColor: "#111827",
  color: "#ffffff",
  cursor: "pointer",
};

const secondaryButtonStyle: CSSProperties = {
  ...buttonStyle,
  backgroundColor: "#ffffff",
  color: "#111827",
};

const dangerButtonStyle: CSSProperties = {
  ...buttonStyle,
  backgroundColor: "#b91c1c",
  borderColor: "#b91c1c",
};

const inputStyle: CSSProperties = {
  flex: 1,
  border: "1px solid #d1d5db",
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 16,
};

const mutedTextStyle: CSSProperties = {
  margin: 0,
  color: "#6b7280",
};

const errorTextStyle: CSSProperties = {
  marginBottom: 0,
  color: "#b91c1c",
};

const successTextStyle: CSSProperties = {
  marginBottom: 0,
  color: "#047857",
};

const cardRowStyle: CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 10,
  padding: "12px 14px",
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "center",
  backgroundColor: "#f9fafb",
};

const documentCardStyle: CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
  backgroundColor: "#f9fafb",
};

const chunkCardStyle: CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 10,
  padding: 12,
  backgroundColor: "#ffffff",
};

const chatListStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  maxHeight: 520,
  overflowY: "auto",
  paddingRight: 4,
};

const messageCardStyle: CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
};
