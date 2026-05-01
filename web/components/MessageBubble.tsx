'use client';

import { cn } from '@/lib/utils';
import { Message } from '@/lib/api';
import { User, Bot, ExternalLink, Calendar } from 'lucide-react';

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  
  // Simple logic to extract URL and Footer
  const parts = message.content.split('\n\n');
  const body = parts[0];
  const metadata = parts.slice(1).join('\n\n');
  
  const hasUrl = metadata.includes('https://');
  const urlMatch = metadata.match(/https?:\/\/[^\s]+/);
  const footerMatch = metadata.match(/Last updated from sources: (.*)/);

  return (
    <div className={cn(
      "flex w-full gap-4 max-w-4xl mx-auto mb-8 animate-in fade-in slide-in-from-bottom-4 duration-300",
      isUser ? "flex-row-reverse" : "flex-row"
    )}>
      <div className={cn(
        "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg",
        isUser ? "bg-slate-700 text-slate-200" : "bg-blue-600 text-white"
      )}>
        {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
      </div>

      <div className={cn(
        "flex flex-col gap-3 max-w-[85%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "px-5 py-4 rounded-2xl text-[15px] leading-relaxed shadow-sm border",
          isUser 
            ? "bg-slate-800 border-slate-700 text-slate-100 rounded-tr-none" 
            : "bg-slate-900 border-white/10 text-slate-100 rounded-tl-none"
        )}>
          {body}
        </div>

        {!isUser && (hasUrl || footerMatch) && (
          <div className="flex flex-col gap-2 w-full px-1">
            {urlMatch && (
              <a 
                href={urlMatch[0]} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors bg-blue-400/10 px-3 py-2 rounded-lg border border-blue-400/20 w-fit"
              >
                <ExternalLink className="w-3 h-3" />
                View Source Document
              </a>
            )}
            {footerMatch && (
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-500 font-semibold">
                <Calendar className="w-3 h-3" />
                Last updated: {footerMatch[1]}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
