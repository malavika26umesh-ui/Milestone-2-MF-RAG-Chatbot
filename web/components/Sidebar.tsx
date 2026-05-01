'use client';

import { Plus, MessageSquare, Shield, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Thread } from '@/lib/api';

interface SidebarProps {
  threads: Thread[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onCreateThread: () => void;
}

export default function Sidebar({ threads, activeThreadId, onSelectThread, onCreateThread }: SidebarProps) {
  return (
    <aside className="w-72 bg-slate-950 border-r border-white/10 flex flex-col h-screen">
      <div className="p-6">
        <h2 className="text-xl font-semibold text-blue-500 flex items-center gap-2 mb-6">
          <Shield className="w-6 h-6" />
          MF Assistant
        </h2>
        <button
          onClick={onCreateThread}
          className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-900/20"
        >
          <Plus className="w-5 h-5" />
          New Conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
        <p className="text-xs font-semibold text-slate-500 px-2 mb-2 uppercase tracking-wider">Recent Chats</p>
        {threads.map((thread) => (
          <button
            key={thread.id}
            onClick={() => onSelectThread(thread.id)}
            className={cn(
              "w-full p-3 rounded-xl text-left text-sm transition-all flex items-center gap-3 group",
              activeThreadId === thread.id
                ? "bg-white/10 text-white border border-white/10"
                : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
            )}
          >
            <MessageSquare className={cn(
              "w-4 h-4",
              activeThreadId === thread.id ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300"
            )} />
            <span className="truncate">Chat {thread.id.substring(0, 8)}</span>
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-white/10 bg-slate-900/50">
        <div className="flex items-center gap-3 px-2 py-2 text-slate-400 text-xs">
          <Info className="w-4 h-4" />
          <span>Facts-only. No advice.</span>
        </div>
      </div>
    </aside>
  );
}
