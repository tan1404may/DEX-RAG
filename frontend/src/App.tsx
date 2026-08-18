import { useState } from 'react'
import { PanelLeft } from 'lucide-react'
import Sidebar from './components/Sidebar/Sidebar'
import ChatWindow from './components/Chat/ChatWindow'
import './index.css'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)

  return (
    <div className="flex h-screen bg-[#0d0d0d] text-gray-200 font-sans text-sm overflow-hidden">
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed top-3 left-3 z-50 p-1.5 bg-gray-800 rounded-md hover:bg-gray-700 transition-colors"
        >
          <PanelLeft size={16} />
        </button>
      )}

      {sidebarOpen && (
        <Sidebar
          selectedDoc={selectedDoc}
          onSelectDoc={setSelectedDoc}
          onClose={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex-1 min-w-0 overflow-hidden">
        <ChatWindow selectedDoc={selectedDoc} />
      </div>
    </div>
  )
}

export default App