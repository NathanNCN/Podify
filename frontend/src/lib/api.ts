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
  console.log(`[API] Calling single extract endpoint for:`, url);
  console.log(`[API] Backend URL: ${API_BASE_URL}`);
  
  try {
    const response = await fetch(`${API_BASE_URL}/extract`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    console.log(`[API] Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error(`[API] Error response:`, error);
      throw new Error(error.detail || `Failed to extract content: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`[API] Single extraction successful:`, { url: data.url, textLength: data.text?.length });
    return data;
  } catch (error) {
    console.error(`[API] Fetch error:`, error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`);
    }
    throw error;
  }
}

/**
 * Extract content from multiple URLs (batch)
 * Returns format: {link1: text, link2: text, link3: text, total_characters: count}
 */
export async function extractBatch(urls: string[], userExtraContent?: string): Promise<{
  link1?: string;
  link2?: string;
  link3?: string;
  [key: string]: string | number | undefined; // Allow link4, link5, etc.
  total_characters: number;
}> {
  console.log(`[API] Calling batch endpoint with ${urls.length} URLs:`, urls);
  if (userExtraContent) {
    console.log(`[API] User extra content included: ${userExtraContent.length} characters`);
  }
  console.log(`[API] Backend URL: ${API_BASE_URL}`);
  
  try {
    const requestBody: { urls: string[]; user_extra_content?: string } = { urls };
    if (userExtraContent && userExtraContent.trim()) {
      requestBody.user_extra_content = userExtraContent.trim();
    }
    
    const response = await fetch(`${API_BASE_URL}/extract/batch`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    console.log(`[API] Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error(`[API] Error response:`, error);
      throw new Error(error.detail || `Failed to extract content: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`[API] Batch extraction successful:`, {
      keys: Object.keys(data),
      total_characters: data.total_characters,
    });
    
    return data;
  } catch (error) {
    console.error(`[API] Fetch error:`, error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`);
    }
    throw error;
  }
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
      console.log(`[API] Extracting from URL ${i + 1}/${urls.length}:`, url);
      const result = await extractContent(url);
      results.push(result);
      onProgress?.(i + 1, urls.length, result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      console.error(`[API] Error extracting from ${url}:`, errorMessage);
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

/**
 * Convert batch response to ExtractedContent array format
 * Takes batch response {link1: text, link2: text, ...} and converts to array
 */
export function batchResponseToExtractedContent(
  batchResponse: { [key: string]: string | number | undefined },
  originalUrls: string[]
): ExtractedContent[] {
  const results: ExtractedContent[] = [];
  
  for (let i = 0; i < originalUrls.length; i++) {
    const linkKey = `link${i + 1}`;
    const text = batchResponse[linkKey] as string || "";
    
    results.push({
      url: originalUrls[i],
      content_type: "text/plain",
      text: text,
      title: undefined,
      metadata: {},
    });
  }
  
  return results;
}

/**
 * Generate a podcast script from extracted batch content
 * Takes the batch response format {link1: text, link2: text, ...} and generates a script
 */
export async function generateScript(
  batchResponse: { [key: string]: string | number | undefined },
  userExtraContent?: string
): Promise<string> {
  console.log(`[API] Calling generate endpoint with batch response`);
  if (userExtraContent) {
    console.log(`[API] User extra content included: ${userExtraContent.length} characters`);
  }
  console.log(`[API] Backend URL: ${API_BASE_URL}`);
  
  try {
    // Filter out total_characters and only send link fields
    const requestBody: { [key: string]: string } = {};
    for (const key in batchResponse) {
      if (key.startsWith("link") && typeof batchResponse[key] === "string") {
        requestBody[key] = batchResponse[key] as string;
      }
    }
    
    // Add user extra content if provided
    if (userExtraContent && userExtraContent.trim()) {
      requestBody.user_extra_content = userExtraContent.trim();
    }
    
    console.log(`[API] Request body keys:`, Object.keys(requestBody));
    
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    console.log(`[API] Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error(`[API] Error response:`, error);
      throw new Error(error.detail || `Failed to generate script: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`[API] Script generation successful:`, {
      scriptLength: data.script?.length,
    });
    
    return data.script;
  } catch (error) {
    console.error(`[API] Fetch error:`, error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`);
    }
    throw error;
  }
}

/**
 * Convert text to speech using ElevenLabs TTS API
 * Returns the URL to the generated audio file
 */
export async function textToSpeech(
  text: string,
  voiceId?: string
): Promise<{ audio_path: string; audio_url: string }> {
  console.log(`[API] Calling TTS endpoint with text length:`, text.length);
  console.log(`[API] Backend URL: ${API_BASE_URL}`);
  
  try {
    const requestBody: { text: string; voice_id?: string } = { text };
    if (voiceId) {
      requestBody.voice_id = voiceId;
    }
    
    const response = await fetch(`${API_BASE_URL}/tts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    console.log(`[API] TTS response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error(`[API] TTS error response:`, error);
      throw new Error(error.detail || `Failed to convert text to speech: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`[API] TTS conversion successful:`, {
      audio_path: data.audio_path,
      audio_url: data.audio_url,
    });
    
    // Return full URL for audio file
    return {
      audio_path: data.audio_path,
      audio_url: `${API_BASE_URL}${data.audio_url}`,
    };
  } catch (error) {
    console.error(`[API] TTS fetch error:`, error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`);
    }
    throw error;
  }
}

/**
 * Generate a summary with notes and key takeaways from a podcast script
 * Returns the generated summary text
 */
export async function generateSummary(script: string, userLinks?: string[]): Promise<string> {
  console.log(`[API] Calling summary endpoint with script length:`, script.length);
  if (userLinks) {
    console.log(`[API] User links included: ${userLinks.length} link(s)`);
  }
  console.log(`[API] Backend URL: ${API_BASE_URL}`);
  
  try {
    const requestBody: { script: string; user_links?: string[] } = { script };
    if (userLinks && userLinks.length > 0) {
      requestBody.user_links = userLinks;
    }
    
    const response = await fetch(`${API_BASE_URL}/summary`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    console.log(`[API] Summary response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      console.error(`[API] Summary error response:`, error);
      throw new Error(error.detail || `Failed to generate summary: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`[API] Summary generation successful:`, {
      summaryLength: data.summary?.length,
    });
    
    return data.summary;
  } catch (error) {
    console.error(`[API] Summary fetch error:`, error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Is the server running?`);
    }
    throw error;
  }
}

