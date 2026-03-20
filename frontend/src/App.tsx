import { FormEvent, useState } from "react";

import { sendChat, uploadTxtFile } from "./services/api";
import type { ChatSource } from "./types";

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  const [question, setQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<ChatSource[]>([]);
  const [chatError, setChatError] = useState("");

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!selectedFile) {
      setUploadError("Please choose a .txt file first.");
      return;
    }

    setUploadLoading(true);
    setUploadError("");
    setUploadMessage("");

    try {
      const result = await uploadTxtFile(selectedFile);
      setUploadMessage(`Uploaded ${result.filename ?? selectedFile.name} (${result.chunks ?? 0} chunks).`);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleChat(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) {
      setChatError("Please enter a question.");
      return;
    }

    setChatLoading(true);
    setChatError("");

    try {
      const result = await sendChat(question.trim());
      setAnswer(result.answer);
      setSources(result.sources);
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Chat failed.");
      setAnswer("");
      setSources([]);
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 820, margin: "32px auto", padding: "0 16px", fontFamily: "Segoe UI, Arial, sans-serif" }}>
      <h1 style={{ marginBottom: 24 }}>Local Knowledge Chat</h1>

      <section style={{ border: "1px solid #d9d9d9", borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>Upload .txt</h2>
        <form onSubmit={handleUpload}>
          <input
            type="file"
            accept=".txt,text/plain"
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

      <section style={{ border: "1px solid #d9d9d9", borderRadius: 8, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Chat</h2>
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

        <div style={{ marginTop: 16 }}>
          <h3 style={{ marginBottom: 8 }}>Answer</h3>
          <div style={{ minHeight: 40, whiteSpace: "pre-wrap" }}>{answer || "No answer yet."}</div>
        </div>

        <div style={{ marginTop: 16 }}>
          <h3 style={{ marginBottom: 8 }}>Sources</h3>
          {sources.length === 0 ? (
            <p>No sources yet.</p>
          ) : (
            <ul style={{ paddingLeft: 20 }}>
              {sources.map((item, index) => (
                <li key={`${item.chunk_id}-${index}`} style={{ marginBottom: 8 }}>
                  <strong>{item.source || "unknown"}</strong> | chunk: {item.chunk_id || "-"} | score: {item.score.toFixed(4)}
                  <div>{item.preview}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;
