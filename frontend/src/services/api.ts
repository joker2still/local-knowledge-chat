import type { ChatResponse, ChatSource, UploadResponse } from "../types";

const BASE_URL = "http://127.0.0.1:8000";

function normalizeSource(raw: any): ChatSource {
  return {
    source: String(raw?.source ?? raw?.filename ?? ""),
    chunk_id: String(raw?.chunk_id ?? ""),
    score: Number(raw?.score ?? raw?.similarity ?? 0),
    preview: String(raw?.preview ?? raw?.text_preview ?? ""),
  };
}

export async function uploadTxtFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(String(data?.detail ?? "Upload failed"));
  }

  return data as UploadResponse;
}

export async function sendChat(prompt: string): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(String(data?.detail ?? "Chat request failed"));
  }

  const sources = Array.isArray(data?.sources)
    ? data.sources.map((item: any) => normalizeSource(item))
    : [];

  return {
    answer: String(data?.answer ?? ""),
    sources,
  };
}
