import { useState, useRef } from 'react'
import { Upload, File, Check, Loader } from 'lucide-react'
import { ingestDocument } from '../../services/api'

export default function FileUploader() {
    const [isUploading, setIsUploading] = useState(false)
    const [lastFile, setLastFile] = useState<string | null>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setIsUploading(true)
        try {
            const res = await ingestDocument(file)
            setLastFile(res.doc_id)
        } catch (err: any) {
            alert(`Upload failed: ${err.message}`)
        } finally {
            setIsUploading(false)
            if (inputRef.current) inputRef.current.value = ''
        }
    }

    return (
        <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase">Documents</h3>

            <input
                ref={inputRef}
                type="file"
                onChange={handleFile}
                accept=".pdf,.docx,.html,.md,.txt,.csv,.py,.js,.ts"
                className="hidden"
            />

            <button
                onClick={() => inputRef.current?.click()}
                disabled={isUploading}
                className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-gray-700 rounded-lg p-4 hover:border-blue-500 hover:bg-gray-900 transition-colors disabled:opacity-50"
            >
                {isUploading ? (
                    <>
                        <Loader size={18} className="animate-spin" />
                        <span className="text-sm">Uploading...</span>
                    </>
                ) : (
                    <>
                        <Upload size={18} />
                        <span className="text-sm">Upload Document</span>
                    </>
                )}
            </button>

            {lastFile && (
                <div className="flex items-center gap-2 text-xs text-green-400 bg-green-900/20 rounded p-2">
                    <Check size={14} />
                    <span className="truncate">{lastFile}</span>
                </div>
            )}
        </div>
    )
}