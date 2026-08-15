import { useState } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'
import { queryRag } from '../../services/api'
import MessageBubble from './MessageBubble'
import InputBox from './InputBox'

export default function ChatWindow() {
    const { messages, addMessage, updateLastMessage } = useChatStore()
    const [input, setInput] = useState('')

    const handleSend = async () => {
        if (!input.trim()) return

        // Add user message
        addMessage({ id: Date.now().toString(), role: 'user', content: input })

        // Add loading assistant message
        const assistantId = (Date.now() + 1).toString()
        addMessage({ id: assistantId, role: 'assistant', content: '', isLoading: true })

        try {
            const res = await queryRag(input)
            updateLastMessage(res.answer, res.sources)
        } catch (err: any) {
            updateLastMessage(`Error: ${err.message}`)
        }

        setInput('')
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="border-b border-gray-800 p-4">
                <h2 className="text-lg font-semibold text-white">Chat</h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <Bot size={48} className="mb-4" />
                        <p>Upload a document and ask questions</p>
                    </div>
                )}
                {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}
            </div>

            {/* Input */}
            <InputBox input={input} setInput={setInput} onSend={handleSend} />
        </div>
    )
}