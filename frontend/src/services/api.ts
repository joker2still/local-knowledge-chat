import type {
  ChatRequest,
  ChatResponse,
  ChatSource,
  DocumentChunksResponse,
  DocumentListResponse,
  DocumentSummaryResponse,
  SessionsResponse,
  UploadResponse,
} from "../types";

const BASE_URL = "http://127.0.0.1:8000";

function readErrorMessage(data: any, fallback: string): string {
  return String(data?.detail ?? data?.error?.message ?? fallback);
}

function normalizeSource(raw: any): ChatSource {
  return {
    source: String(raw?.source ?? raw?.filename ?? ""),
    chunk_id: String(raw?.chunk_id ?? ""),
    score: Number(raw?.score ?? raw?.similarity ?? 0),
    preview: String(raw?.preview ?? raw?.text_preview ?? ""),
    page_number: raw?.page_number ?? null,
    file_type: String(raw?.file_type ?? ""),
  };
}

async function readJson(response: Response, fallbackMessage: string): Promise<any> {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(readErrorMessage(data, fallbackMessage));
  }
  return data;
}

export async function uploadDocumentFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  return readJson(response, "Upload failed");
}

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await readJson(response, "Chat request failed");
  const sources = Array.isArray(data?.sources)
    ? data.sources.map((item: any) => normalizeSource(item))
    : [];

  return {
    answer: String(data?.answer ?? ""),
    selected_tool: String(data?.selected_tool ?? ""),
    tool_result: data?.tool_result ?? null,
    sources,
    session_id: String(data?.session_id ?? payload.session_id),
  };
}

export async function listConversations(): Promise<SessionsResponse> {
  const response = await fetch(`${BASE_URL}/conversations`);
  const data = await readJson(response, "Failed to load conversations");
  return {
    sessions: Array.isArray(data?.sessions) ? data.sessions.map((item: unknown) => String(item)) : [],
  };
}

export async function clearConversation(sessionId: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/conversations/${encodeURIComponent(sessionId)}/clear`, {
    method: "POST",
  });
  await readJson(response, "Failed to clear conversation");
}

export async function deleteConversation(sessionId: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/conversations/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  await readJson(response, "Failed to delete conversation");
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await fetch(`${BASE_URL}/documents`);
  const data = await readJson(response, "Failed to load documents");
  return {
    documents: Array.isArray(data?.documents) ? data.documents : [],
    total_files: Number(data?.total_files ?? 0),
    total_chunks: Number(data?.total_chunks ?? 0),
  };
}

export async function getDocumentChunks(docId: string): Promise<DocumentChunksResponse> {
  const response = await fetch(`${BASE_URL}/documents/${encodeURIComponent(docId)}/chunks`);
  const data = await readJson(response, "Failed to load document chunks");
  return {
    doc_id: String(data?.doc_id ?? docId),
    chunk_count: Number(data?.chunk_count ?? 0),
    chunks: Array.isArray(data?.chunks) ? data.chunks : [],
  };
}

export async function summarizeDocument(docId: string): Promise<DocumentSummaryResponse> {
  const response = await fetch(`${BASE_URL}/documents/${encodeURIComponent(docId)}/summary`, {
    method: "POST",
  });
  const data = await readJson(response, "Failed to summarize document");
  const sources = Array.isArray(data?.sources)
    ? data.sources.map((item: any) => normalizeSource(item))
    : [];

  return {
    doc_id: String(data?.doc_id ?? docId),
    summary: String(data?.summary ?? ""),
    sources,
  };
}

export async function deleteDocument(docId: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/documents/${encodeURIComponent(docId)}`, {
    method: "DELETE",
  });
  await readJson(response, "Failed to delete document");
}
