export type ChatSource = {
  source: string;
  chunk_id: string;
  score: number;
  preview: string;
  page_number?: number | null;
  file_type?: string;
};

export type ChatRequest = {
  session_id: string;
  message: string;
};

export type ChatResponse = {
  answer: string;
  selected_tool: string;
  tool_result: Record<string, unknown> | Array<Record<string, unknown>> | string[] | null;
  sources: ChatSource[];
  session_id: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  selected_tool?: string;
  sources?: ChatSource[];
};

export type SessionsResponse = {
  sessions: string[];
};

export type UploadResponse = {
  filename?: string;
  chunks?: number;
  vector_store?: string;
  detail?: string;
};
