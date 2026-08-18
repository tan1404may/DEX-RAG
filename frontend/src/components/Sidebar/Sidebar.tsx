import { useEffect, useState } from 'react'
import { FileText, Trash2, ChevronDown, ChevronUp, PanelLeftClose, Upload } from 'lucide-react'
import { listDocuments, deleteDocument, ingestFile } from '../../services/api'

interface Props {
    selectedDoc: string | null
    onSelectDoc: (docId: string | null) => void
    onClose: () => void
}

interface DocItem {
    doc_id: string
    title: string
    created_at: string
}

export default function Sidebar({ selectedDoc, onSelectDoc, onClose }: Props) {
    const [docs, setDocs] = useState<DocItem[]>([])
    const [filesOpen, setFilesOpen] = useState(true)
    const [isUploading, setIsUploading] = useState(false)

    const loadDocs = async () => {
        try {
            const res = await listDocuments()
            setDocs(res.documents || [])
        } catch (e) {
            console.error(e)
        }
    }

    useEffect(() => {
        loadDocs()
        const interval = setInterval(loadDocs, 5000)
        return () => clearInterval(interval)
    }, [])

    const handleDelete = async (e: React.MouseEvent, docId: string) => {
        e.stopPropagation()
        await deleteDocument(docId)
        loadDocs()
        if (selectedDoc === docId) onSelectDoc(null)
    }

    const handleUpload = async () => {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.pdf,.docx,.html,.md,.txt,.csv,.py,.js,.ts'
        input.onchange = async (e) => {
            const file = (e.target as HTMLInputElement).files?.[0]
            if (!file) return
            setIsUploading(true)
            try {
                await ingestFile(file)
                loadDocs()
            } finally {
                setIsUploading(false)
            }
        }
        input.click()
    }

    return (
        <div className="w-60 border-r border-gray-800 flex flex-col bg-[#111111] shrink-0">
            {/* Header */}
            <div className="p-3.5 border-b border-gray-800 flex items-center justify-between">
                <div>
                    <h1 className="text-base font-bold text-white">DEX-RAG</h1>
                    <p className="text-[11px] text-gray-500 mt-0.5">Ask your documents</p>
                </div>
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-gray-800 rounded transition-colors text-gray-400 hover:text-white"
                >
                    <PanelLeftClose size={14} />
                </button>
            </div>

            {/* Upload - smaller */}
            <div className="px-3 pt-3 pb-2">
                <button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="w-full flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md py-1.5 text-xs font-medium transition-colors"
                >
                    <Upload size={12} />
                    {isUploading ? 'Uploading...' : 'Upload Document'}
                </button>
            </div>

            {/* Collapsible Files */}
            <div className="flex-1 overflow-hidden flex flex-col">
                <button
                    onClick={() => setFilesOpen(!filesOpen)}
                    className="flex items-center justify-between px-3 py-1.5 hover:bg-gray-800/50 transition-colors"
                >
                    <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                        Documents ({docs.length})
                    </span>
                    {filesOpen ? <ChevronUp size={12} className="text-gray-500" /> : <ChevronDown size={12} className="text-gray-500" />}
                </button>

                {filesOpen && (
                    <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
                        {docs.map((doc) => (
                            <div
                                key={doc.doc_id}
                                onClick={() => onSelectDoc(doc.doc_id === selectedDoc ? null : doc.doc_id)}
                                className={`group flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer transition-all ${selectedDoc === doc.doc_id
                                    ? 'bg-blue-600/15 text-blue-400 border border-blue-600/25'
                                    : 'hover:bg-gray-800/60 text-gray-300'
                                    }`}
                            >
                                <FileText size={12} className="shrink-0 opacity-60" />
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs truncate">{doc.title || doc.doc_id}</p>
                                </div>
                                <button
                                    onClick={(e) => handleDelete(e, doc.doc_id)}
                                    className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-red-600/20 hover:text-red-400 rounded transition-all"
                                >
                                    <Trash2 size={10} />
                                </button>
                            </div>
                        ))}

                        {docs.length === 0 && (
                            <div className="text-center py-4 text-gray-600 text-xs">
                                No documents yet
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}