import ChatWindow from './components/Chat/ChatWindow'
import FileUploader from './components/Upload/FileUploader'
import './index.css'

function App() {
  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <div className="w-64 border-r border-gray-800 p-4 flex flex-col">
        <h1 className="text-xl font-bold text-white mb-6">DEX-RAG</h1>
        <FileUploader />
      </div>

      {/* Main Chat */}
      <div className="flex-1">
        <ChatWindow />
      </div>
    </div>
  )
}

export default App