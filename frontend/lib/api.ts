import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

export async function explainEmail(payload: { email_id: string; body: string; summary?: string | null }) {
  const { data } = await api.post("/explain", payload);
  return String(data.reasons ?? data.explanation ?? data.message ?? "");
}
