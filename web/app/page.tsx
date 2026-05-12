'use client';

import { useState, useEffect, useRef } from 'react';
import Sidebar from '@/components/Sidebar';
import MessageBubble from '@/components/MessageBubble';
import ChatInput from '@/components/ChatInput';
import { api, Thread, Message } from '@/lib/api';
import { Bot } from 'lucide-react';

export default function Home() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  const handleCreateThread = async () => {
    try {
      const thread = await api.createThread();
      setThreads([thread, ...threads]);
      setActiveThreadId(thread.id);
    } catch (e) {
      console.error('Failed to create thread', e);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!activeThreadId) return;
    
    // Add user message locally
    const userMsg: Message = { role: 'user', content, timestamp: '' };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const assistantMsg = await api.sendMessage(activeThreadId, content);
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Error: Failed to get response from server.', 
        timestamp: '' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function startFetching() {
      try {
        const data = await api.listThreads();
        if (!ignore) setThreads(data);
      } catch (e) {
        console.error('Failed to load threads', e);
      }
    }
    startFetching();
    return () => { ignore = true; };
  }, []);

  useEffect(() => {
    if (!activeThreadId) return;
    let ignore = false;
    async function startFetching() {
      try {
        const data = await api.getMessages(activeThreadId as string);
        if (!ignore) setMessages(data);
      } catch (e) {
        console.error('Failed to load messages', e);
      }
    }
    startFetching();
    return () => { ignore = true; };
  }, [activeThreadId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      <Sidebar 
        threads={threads} 
        activeThreadId={activeThreadId} 
        onSelectThread={setActiveThreadId}
        onCreateThread={handleCreateThread}
      />

      <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
        <header className="h-16 border-b border-white/5 flex items-center px-8 bg-slate-950/50 backdrop-blur-sm z-10 shrink-0">
          <div className="flex flex-col">
            <h1 className="text-sm font-semibold text-slate-300">
              {activeThreadId ? `Conversation ${activeThreadId.substring(0, 8)}` : 'Select a thread'}
            </h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] text-slate-500 font-medium uppercase tracking-tighter">System Active</span>
            </div>
          </div>
        </header>

        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-8 scroll-smooth"
        >
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center gap-4 text-center animate-in fade-in zoom-in duration-500">
              <div className="w-16 h-16 rounded-3xl bg-blue-600/10 flex items-center justify-center border border-blue-500/20 mb-2">
                <Bot className="w-8 h-8 text-blue-500" />
              </div>
              <h3 className="text-2xl font-bold text-slate-100">MF FAQ Assistant</h3>
              <p className="text-slate-400 max-w-sm text-sm leading-relaxed">
                Your secure, facts-only assistant for mutual fund inquiries. Ask about NAVs, expense ratios, or fund documents.
              </p>
              <div className="grid grid-cols-2 gap-3 mt-4 w-full max-w-md">
                {['What is the NAV?', 'Expense Ratio?', 'Risk Level?', 'Exit Load?'].map(q => (
                  <button 
                    key={q} 
                    onClick={() => handleSendMessage(q)}
                    className="p-3 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-400 hover:bg-white/10 hover:text-slate-200 transition-all text-left"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))
          )}
          {isLoading && (
            <div className="flex gap-4 max-w-4xl mx-auto items-start">
               <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center shrink-0 shadow-lg">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-slate-900 border border-white/10 px-5 py-4 rounded-2xl rounded-tl-none animate-pulse text-slate-500 text-sm italic">
                Assistant is verifying records...
              </div>
            </div>
          )}
        </div>

        <ChatInput onSend={handleSendMessage} isLoading={isLoading} disabled={!activeThreadId} />
      </main>
    </div>
  );
}
