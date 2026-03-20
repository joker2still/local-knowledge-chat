export type ChatSource = {
  source: string;
  chunk_id: string;
  score: number;
  preview: string;
};

export type ChatResponse = {
  answer: string;
  sources: ChatSource[];
};

export type UploadResponse = {
  filename?: string;
  chunks?: number;
  vector_store?: string;
  detail?: string;
};
