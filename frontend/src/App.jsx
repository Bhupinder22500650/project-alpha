import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import DomainDetail from './components/DomainDetail'
import Login from './components/Login'

function App() {
  const token = localStorage.getItem('token')

  return (
    <Router>
      <div className="min-h-screen bg-slate-900 flex flex-col">
        <header className="bg-slate-800 border-b border-slate-700 py-4 px-6 shadow-md">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Link to="/" className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <span className="text-indigo-400">AI</span> Phishing Detector
            </Link>
            
            <nav className="flex gap-4">
              {token ? (
                <button 
                  onClick={() => { localStorage.removeItem('token'); window.location.href='/login'; }}
                  className="text-sm text-slate-300 hover:text-white"
                >
                  Logout
                </button>
              ) : (
                <Link to="/login" className="text-sm text-slate-300 hover:text-white">Login</Link>
              )}
            </nav>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          <Routes>
            <Route path="/" element={token ? <Dashboard /> : <Login />} />
            <Route path="/login" element={<Login />} />
            <Route path="/domain/:id" element={<DomainDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
