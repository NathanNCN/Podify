/**
 * API service for communicating with the Podify backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ExtractedContent {
  url: string;
  content_type: string;
  text: string;
  title?: string;
  metadata?: Record<string, any>;
}

export interface ExtractResponse {
  url: string;
  content_type: string;
  text: string;
  title?: string;
  metadata?: Record<string, any>;
}

/**
 * Extract content from a single URL
 */
export async function extractContent(url: string): Promise<ExtractResponse> {
  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Failed to extract content: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Extract content from multiple URLs (batch)
 */
export async function extractBatch(urls: string[]): Promise<{
  results: ExtractResponse[];
  errors: Array<{ url: string; error: string }>;
}> {
  const response = await fetch(`${API_BASE_URL}/extract/batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ urls }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Failed to extract content: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Extract content from URLs one by one (sequential processing)
 * Returns progress updates via callback
 */
export async function extractSequential(
  urls: string[],
  onProgress?: (current: number, total: number, result?: ExtractResponse, error?: string) => void
): Promise<ExtractedContent[]> {
  const results: ExtractedContent[] = [];

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i];
    try {
      onProgress?.(i + 1, urls.length);
      const result = await extractContent(url);
      results.push(result);
      onProgress?.(i + 1, urls.length, result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      onProgress?.(i + 1, urls.length, undefined, errorMessage);
      // Continue processing other URLs even if one fails
      results.push({
        url,
        content_type: "unknown",
        text: "",
        title: "Error",
        metadata: { error: errorMessage },
      });
    }
  }

  return results;
}

