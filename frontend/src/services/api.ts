import type { ChatRequest, ChatResponse, ChatSource, SessionsResponse, UploadResponse } from "../types";

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

export async function uploadDocumentFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(readErrorMessage(data, "Upload failed"));
  }

  return data as UploadResponse;
}

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(readErrorMessage(data, "Chat request failed"));
  }

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
  const data = await response.json();
  if (!response.ok) {
    throw new Error(readErrorMessage(data, "Failed to load conversations"));
  }
  return {
    sessions: Array.isArray(data?.sessions) ? data.sessions.map((item: unknown) => String(item)) : [],
  };
}

export async function clearConversation(sessionId: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/conversations/${encodeURIComponent(sessionId)}/clear`, {
    method: "POST",
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(readErrorMessage(data, "Failed to clear conversation"));
  }
}

export async function deleteConversation(sessionId: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/conversations/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(readErrorMessage(data, "Failed to delete conversation"));
  }
}
