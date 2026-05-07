export type Priority = "P1" | "P2" | "P3";

export type Email = {
  id: number;
  email_id: string;
  subject: string;
  sender: string;
  body: string;
  priority: Priority;
  intent: string;
  needs_reply: boolean;
  summary: string | null;
  risk_score: number | null;
  created_at: string;
};

export type Commitment = {
  id: string;
  email_id: string;
  task: string;
  raw_text: string | null;
  who: string | null;
  deadline: string | null;
  deadline_text: string | null;
  status: string;
  confidence: number | null;
  priority: Priority;
};

export type Alert = {
  id: number;
  email_id: string | null;
  commitment_id: string | null;
  task: string | null;
  message: string;
  alert_type: string;
  is_read: boolean;
};

export type DraftReply = {
  id: string;
  email_id: string;
  subject: string;
  to_address: string;
  draft_body: string;
  created_at: string;
};
