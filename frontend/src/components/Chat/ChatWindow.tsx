import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, X, Sparkles } from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'
import { queryRag } from '../../services/api'

interface Props {
    selectedDoc: string | null
}

export default function ChatWindow({ selectedDoc }: Props) {
    const { messages, addMessage, updateLastMessage } = useChatStore()
    const [input, setInput] = useState('')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async () => {
        if (!input.trim()) return

        const question = input.trim()
        setInput('')

        addMessage({
            id: Date.now().toString(),
            role: 'user',
            content: question,
        })

        const assistantId = (Date.now() + 1).toString()
        addMessage({
            id: assistantId,
            role: 'assistant',
            content: '',
            isLoading: true,
        })

        try {
            const res = await queryRag(question, 'default', selectedDoc || undefined)
            updateLastMessage(res.answer, res.sources)
        } catch (err: any) {
            updateLastMessage(`Error: ${err.message}`)
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="flex flex-col h-full bg-[#0d0d0d]">
            {/* Header - compact */}
            <div className="border-b border-gray-800 px-4 py-2.5 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                    <Sparkles size={14} className="text-blue-400" />
                    <h2 className="text-sm font-semibold text-white">Chat</h2>
                    {selectedDoc && (
                        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-blue-600/15 text-blue-400 rounded-full text-[10px] border border-blue-600/25">
                            <span className="truncate max-w-[120px]">{selectedDoc}</span>
                            <button onClick={() => window.location.reload()} className="hover:text-white">
                                <X size={8} />
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Messages - smaller empty state */}
            {/* space-y-3 */}
            <div className="flex-1 overflow-y-auto px-4 py-3 scrollbar-thin min-h-0">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <div className="w-10 h-10 rounded-xl bg-gray-800/40 flex items-center justify-center mb-2">
                            <Bot size={20} strokeWidth={1.5} className="text-gray-500" />
                        </div>
                        <p className="text-xs text-gray-600">
                            {selectedDoc ? 'Ask about the selected document' : 'Upload a document and ask questions'}
                        </p>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'assistant' && (
                            <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center shrink-0 mt-0.5">
                                <Bot size={12} className="text-gray-400" />
                            </div>
                        )}

                        <div className={`max-w-[80%] rounded-lg px-3 py-2 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800/70 text-gray-200 border border-gray-800'}`}>
                            {msg.isLoading ? (
                                <div className="flex gap-1 py-1 px-1">
                                    <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" />
                                    <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce delay-100" />
                                    <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce delay-200" />
                                </div>
                            ) : (
                                <>
                                    <p className="text-xs leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                    {msg.sources && msg.sources.length > 0 && (
                                        <div className="mt-2 pt-2 border-t border-gray-700/40">
                                            <p className="text-[10px] text-gray-500 mb-1.5 font-medium">Sources ({msg.sources.length})</p>
                                            <div className="space-y-1">
                                                {msg.sources.map((s: any, i: number) => (
                                                    <div key={i} className="text-[10px] bg-gray-900/50 rounded-md p-1.5 border border-gray-800">
                                                        <div className="flex items-center gap-1.5 mb-0.5">
                                                            <span className="text-blue-400 font-semibold">{s.score.toFixed(3)}</span>
                                                            <span className="text-gray-600">|</span>
                                                            <span className="text-gray-500 truncate">{s.metadata?.doc_id || 'unknown'}</span>
                                                        </div>
                                                        <p className="text-gray-400 line-clamp-2 leading-relaxed">{s.text}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        {msg.role === 'user' && (
                            <div className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center shrink-0 mt-0.5">
                                <User size={12} className="text-gray-300" />
                            </div>
                        )}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input - minimal & small */}
            <div className="border-t border-gray-800 px-4 py-2.5 shrink-0">
                <div className="relative max-w-2xl mx-auto">
                    <div className="flex items-center gap-2 bg-gray-900/80 border border-gray-800 rounded-xl px-3 py-1.5 focus-within:border-gray-700 transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask a question..."
                            className="flex-1 bg-transparent text-xs text-white placeholder-gray-600 focus:outline-none"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim()}
                            className="p-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg text-white transition-all"
                        >
                            <Send size={12} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}