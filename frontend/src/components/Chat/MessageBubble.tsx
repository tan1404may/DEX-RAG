import { Bot, User, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { Message } from '../../stores/chatStore'

interface Props {
    message: Message
}

export default function MessageBubble({ message }: Props) {
    const [showSources, setShowSources] = useState(false)
    const isUser = message.role === 'user'

    return (
        <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                    <Bot size={16} className="text-white" />
                </div>
            )}

            <div className={`max-w-[70%] rounded-2xl px-4 py-3 ${isUser ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-100'
                }`}>
                {message.isLoading ? (
                    <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                    </div>
                ) : (
                    <>
                        <p className="whitespace-pre-wrap">{message.content}</p>

                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-700">
                                <button
                                    onClick={() => setShowSources(!showSources)}
                                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-white"
                                >
                                    {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                    Sources ({message.sources.length})
                                </button>

                                {showSources && (
                                    <div className="mt-2 space-y-2">
                                        {message.sources.map((s: any, i: number) => (
                                            <div key={i} className="text-xs bg-gray-900 rounded p-2">
                                                <div className="flex justify-between text-gray-500 mb-1">
                                                    <span>Score: {s.score.toFixed(3)}</span>
                                                </div>
                                                <p className="text-gray-300 line-clamp-3">{s.text}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>

            {isUser && (
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center shrink-0">
                    <User size={16} className="text-white" />
                </div>
            )}
        </div>
    )
}