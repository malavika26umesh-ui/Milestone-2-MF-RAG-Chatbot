const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface Thread {
  id: string;
  created_at: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export const api = {
  async listThreads(): Promise<Thread[]> {
    const res = await fetch(`${API_BASE}/api/threads`);
    return res.json();
  },

  async createThread(): Promise<Thread> {
    const res = await fetch(`${API_BASE}/api/threads`, { method: 'POST' });
    return res.json();
  },

  async getMessages(threadId: string): Promise<Message[]> {
    const res = await fetch(`${API_BASE}/api/threads/${threadId}/messages`);
    return res.json();
  },

  async sendMessage(threadId: string, content: string): Promise<Message> {
    const res = await fetch(`${API_BASE}/api/threads/${threadId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    return res.json();
  },
};
