import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { AlertCircle, ShieldCheck, Clock, ArrowRight, Search, Loader2 } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inputDomain, setInputDomain] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchDomains();
    const interval = setInterval(fetchDomains, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDomains = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/domains?limit=50`);
      setDomains(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch domains", err);
      setLoading(false);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!inputDomain.trim()) return;
    
    setAnalyzing(true);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/domains/analyze`, {
        domain_name: inputDomain
      });
      // Prepend to domains list if it's new, or update if it exists
      setDomains(prev => {
        const filtered = prev.filter(d => d.id !== res.data.id);
        return [res.data, ...filtered];
      });
      setInputDomain('');
    } catch (err) {
      console.error("Failed to analyze domain", err);
      alert("Failed to analyze domain. Please check console.");
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 80) return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
    if (score >= 50) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  };

  if (loading) return <div className="text-slate-400 p-8 text-center animate-pulse">Loading live feed...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-400" />
          Live Domain Feed
        </h2>
        
        <form onSubmit={handleAnalyze} className="relative w-full md:w-96">
          <div className="relative flex items-center">
            <Search className="absolute left-3 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={inputDomain}
              onChange={(e) => setInputDomain(e.target.value)}
              placeholder="Analyze a specific domain (e.g. apple-verify.com)"
              className="w-full bg-slate-800/50 border border-slate-700 rounded-lg py-2 pl-9 pr-24 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              disabled={analyzing}
            />
            <button
              type="submit"
              disabled={analyzing || !inputDomain.trim()}
              className="absolute right-1 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white text-xs font-medium rounded-md transition-colors flex items-center gap-1"
            >
              {analyzing ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Track'}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden shadow-xl backdrop-blur-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-800/80">
              <th className="py-4 px-6 font-medium text-slate-300">Domain Name</th>
              <th className="py-4 px-6 font-medium text-slate-300">Risk Score</th>
              <th className="py-4 px-6 font-medium text-slate-300 hidden md:table-cell">Source</th>
              <th className="py-4 px-6 font-medium text-slate-300 hidden sm:table-cell">Scored At</th>
              <th className="py-4 px-6 font-medium text-slate-300 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {domains.length === 0 ? (
              <tr>
                <td colSpan="5" className="py-8 text-center text-slate-400">
                  No domains processed yet. Waiting for ingestion pipeline...
                </td>
              </tr>
            ) : (
              domains.map((d) => (
                <tr key={d.id} className="hover:bg-slate-700/30 transition-colors group">
                  <td className="py-4 px-6">
                    <span className="font-mono text-slate-200">{d.domain_name}</span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${getRiskColor(d.risk_score)}`}>
                      {d.risk_score >= 80 ? <AlertCircle className="w-3.5 h-3.5" /> : <ShieldCheck className="w-3.5 h-3.5" />}
                      {d.risk_score}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-slate-400 text-sm hidden md:table-cell">{d.source}</td>
                  <td className="py-4 px-6 text-slate-400 text-sm hidden sm:table-cell">
                    {new Date(d.created_at).toLocaleTimeString()}
                  </td>
                  <td className="py-4 px-6 text-right">
                    <Link 
                      to={`/domain/${d.id}`} 
                      className="inline-flex items-center justify-center p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-600 transition-all opacity-0 group-hover:opacity-100"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
