import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { aiCoachApi } from '@/api/client';
import type { ChatMessage, ChatResponse } from '@/types';
import {
  PaperAirplaneIcon,
  SparklesIcon,
  UserIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

interface AIChatProps {
  className?: string;
}

export function AIChat({ className = '' }: AIChatProps) {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch quick questions
  const { data: quickQuestions } = useQuery({
    queryKey: ['ai-coach-quick-questions'],
    queryFn: () => aiCoachApi.getQuickQuestions(),
  });

  // Check service status
  const { data: status } = useQuery({
    queryKey: ['ai-coach-status'],
    queryFn: () => aiCoachApi.getStatus(),
  });

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      return aiCoachApi.chat(message, messages);
    },
    onSuccess: (response: ChatResponse) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
        },
      ]);
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (message: string) => {
    if (!message.trim() || chatMutation.isPending) return;

    // Add user message to history
    setMessages((prev) => [...prev, { role: 'user', content: message }]);
    setInputValue('');

    // Send to API
    chatMutation.mutate(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  const isServiceAvailable = status?.available ?? true;

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg">
            <SparklesIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {t('aiCoach.chatTitle', 'AI Trading Coach')}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {status?.provider
                ? `${status.provider} - ${status.model}`
                : t('aiCoach.chatSubtitle', 'Ask me anything about your trading')}
            </p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClearChat}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title={t('aiCoach.clearChat', 'Clear chat')}
          >
            <ArrowPathIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Service Status Warning */}
      {!isServiceAvailable && (
        <div className="mx-4 mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-start gap-2">
          <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-yellow-800 dark:text-yellow-200 font-medium">
              {t('aiCoach.serviceUnavailable', 'AI Service Unavailable')}
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-0.5">
              {status?.message}
            </p>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[500px]">
        {messages.length === 0 ? (
          // Empty state with quick questions
          <div className="h-full flex flex-col items-center justify-center text-center">
            <SparklesIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {t('aiCoach.startConversation', 'Start a conversation or pick a quick question')}
            </p>
            {quickQuestions && quickQuestions.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center max-w-md">
                {quickQuestions.slice(0, 4).map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    disabled={chatMutation.isPending}
                    className="px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 hover:text-purple-700 dark:hover:text-purple-300 transition-colors disabled:opacity-50"
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          // Chat messages
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                    <SparklesIcon className="w-4 h-4 text-white" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                    message.role === 'user'
                      ? 'bg-purple-600 text-white rounded-br-md'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-bl-md'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center flex-shrink-0">
                    <UserIcon className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {chatMutation.isPending && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                  <SparklesIcon className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            {/* Error message */}
            {chatMutation.isError && (
              <div className="flex justify-center">
                <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm px-4 py-2 rounded-lg">
                  {t('aiCoach.chatError', 'Failed to get response. Please try again.')}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Quick Questions (when in chat mode) */}
      {messages.length > 0 && quickQuestions && quickQuestions.length > 0 && (
        <div className="px-4 pb-2">
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {quickQuestions.slice(0, 4).map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuickQuestion(question)}
                disabled={chatMutation.isPending}
                className="flex-shrink-0 px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/30 hover:text-purple-700 dark:hover:text-purple-300 transition-colors disabled:opacity-50"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-gray-100 dark:border-gray-700">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={chatMutation.isPending || !isServiceAvailable}
            placeholder={
              isServiceAvailable
                ? t('aiCoach.inputPlaceholder', 'Ask about your trading performance...')
                : t('aiCoach.serviceDisabled', 'Service unavailable')
            }
            className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 border-0 rounded-full text-sm text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          />
          <button
            onClick={() => handleSendMessage(inputValue)}
            disabled={!inputValue.trim() || chatMutation.isPending || !isServiceAvailable}
            className="p-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
