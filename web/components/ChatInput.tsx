'use client';

import { SendHorizontal, Loader2 } from 'lucide-react';
import { useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled: boolean;
}

export default function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <div className="p-6 border-t border-white/10 bg-slate-950/80 backdrop-blur-md">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative group">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={disabled ? "Select a chat to start..." : "Ask about fund performance, ratios, or documents..."}
          disabled={disabled || isLoading}
          className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 pr-16 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading || disabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all disabled:bg-slate-800 disabled:text-slate-600 shadow-lg shadow-blue-900/20"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <SendHorizontal className="w-5 h-5" />
          )}
        </button>
      </form>
    </div>
  );
}
