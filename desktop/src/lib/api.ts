const DEFAULT_API = "http://127.0.0.1:8765";

export function apiBase(): string {
  return (import.meta.env.VITE_DOKKEBI_API as string | undefined)?.trim() || DEFAULT_API;
}

export type GoalResult = {
  response: string;
  model: string;
  memory_hits: number;
  web_hits: number;
  elapsed_seconds: number;
};

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${apiBase()}/healthz`, { method: "GET" });
    if (!res.ok) return false;
    const data = (await res.json()) as { status?: string };
    return data.status === "ok";
  } catch {
    return false;
  }
}

export async function postGoal(
  userInput: string,
  options?: { debate?: boolean; token?: string },
): Promise<GoalResult> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = options?.token?.trim();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${apiBase()}/goal`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      user_input: userInput,
      router_intent: options?.debate ? "debate" : "default",
      thread_id: "tauri-desktop",
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
  }

  return (await res.json()) as GoalResult;
}
