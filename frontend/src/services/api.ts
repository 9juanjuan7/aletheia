const API_URL = "http://localhost:5000";

export interface AnalysisProgress {
  message: string;
  submessage?: string;
}

export interface AnalysisResult {
  complete: boolean;
  result?: any;
  error?: string;
}

/**
 * Stream analysis from backend with progress updates
 */
export async function streamAnalysis(
  url: string,
  title: string,
  sessionId: string,
  onProgress: (progress: AnalysisProgress) => void
): Promise<any> {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await fetch(`${API_URL}/analyze-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url,
          title,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Response body is not readable");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Keep the last incomplete line in buffer
        buffer = lines[lines.length - 1];

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6);
            try {
              const data = JSON.parse(jsonStr);

              if (data.error) {
                reject(new Error(data.error));
                return;
              }

              if (data.complete && data.result) {
                resolve(data.result);
                return;
              }

              if (data.message) {
                onProgress(data as AnalysisProgress);
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", jsonStr, e);
            }
          }
        }
      }

      // Handle remaining buffer
      if (buffer.trim().startsWith("data: ")) {
        const jsonStr = buffer.trim().slice(6);
        try {
          const data = JSON.parse(jsonStr);
          if (data.complete && data.result) {
            resolve(data.result);
          } else if (data.error) {
            reject(new Error(data.error));
          }
        } catch (e) {
          console.error("Failed to parse final SSE data:", jsonStr, e);
        }
      }
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Fallback: Get analysis result directly (non-streaming)
 */
export async function analyzeArticle(
  url: string,
  title: string
): Promise<any> {
  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url,
      title,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
