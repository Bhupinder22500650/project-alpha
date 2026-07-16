import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, ShieldAlert, CheckCircle2, Info } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function DomainDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_BASE}/api/v1/domains/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) return <div className="text-slate-400 p-8 text-center animate-pulse">Loading details...</div>;
  if (!data) return <div className="text-rose-400 p-8 text-center">Failed to load domain details.</div>;

  const { domain, score, features } = data;
  const isHighRisk = score.risk_score >= 80;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-8 border-b border-slate-700 bg-slate-800/50 flex items-start justify-between">
          <div>
            <h2 className="text-3xl font-bold font-mono text-white mb-2">{domain.domain_name}</h2>
            <div className="text-slate-400 text-sm">
              Detected on {new Date(domain.created_at).toLocaleString()}
            </div>
          </div>
          
          <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${
            isHighRisk ? 'bg-rose-500/10 border-rose-500/20' : 'bg-emerald-500/10 border-emerald-500/20'
          }`}>
            <div className={`text-4xl font-black ${isHighRisk ? 'text-rose-500' : 'text-emerald-400'}`}>
              {score.risk_score !== null ? score.risk_score.toFixed(2) : 'N/A'}
            </div>
            <div className={`text-xs font-semibold mt-1 uppercase tracking-wider ${isHighRisk ? 'text-rose-400' : 'text-emerald-500'}`}>
              Risk Score
            </div>
          </div>
        </div>

        {domain.alert_id && (
          <div className="p-4 bg-slate-800/80 border-b border-slate-700 flex gap-4">
            <button onClick={async () => {
                const token = localStorage.getItem('token');
                await axios.post(`${API_BASE}/api/v1/alerts/${domain.alert_id}/review`, { status: 'confirmed_suspicious', notes: 'Confirmed by analyst' }, { headers: { Authorization: `Bearer ${token}` }});
                alert('Domain confirmed as suspicious');
              }} className="bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors">
              Confirm Suspicious
            </button>
            <button onClick={async () => {
                const token = localStorage.getItem('token');
                await axios.post(`${API_BASE}/api/v1/alerts/${domain.alert_id}/review`, { status: 'false_positive', notes: 'Dismissed by analyst' }, { headers: { Authorization: `Bearer ${token}` }});
                alert('Alert dismissed');
              }} className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-md font-medium text-sm transition-colors">
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-slate-700">
          
          {/* Explanation Panel */}
          <div className="bg-slate-800 p-8">
            <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <Info className="w-5 h-5 text-indigo-400" />
              Risk Explanation (SHAP)
            </h3>
            
            {score.top_factors && Object.keys(score.top_factors).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(score.top_factors).map(([factor, impact]) => (
                  <div key={factor} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-slate-200 capitalize">{factor.replace('_', ' ')}</span>
                      <span className={`text-sm font-mono ${impact > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {impact > 0 ? '+' : ''}{impact}
                      </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-1.5">
                      <div 
                        className={`h-1.5 rounded-full ${impact > 0 ? 'bg-rose-500' : 'bg-emerald-500'}`} 
                        style={{ width: `${Math.min(Math.abs(impact) * 2, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400">No specific risk factors flagged by the model.</p>
            )}
          </div>

          {/* Raw Features Panel */}
          <div className="bg-slate-800 p-8">
            <h3 className="text-lg font-semibold text-white mb-6">Raw Lexical Features</h3>
            <div className="grid grid-cols-2 gap-4">
              {features && Object.entries(features).map(([key, val]) => (
                <div key={key} className="bg-slate-900/30 rounded-lg p-4 border border-slate-700/30">
                  <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{key.replace('_', ' ')}</div>
                  <div className="text-lg font-mono text-slate-200">
                    {typeof val === 'boolean' ? (val ? 'Yes' : 'No') : (val !== null ? val : 'N/A')}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Enrichment Panel */}
          <div className="bg-slate-800 p-8 col-span-1 md:col-span-2 border-t border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-6">External Enrichment</h3>
            <div className="grid grid-cols-3 gap-4">
              {data.enrichment && Object.entries(data.enrichment).map(([key, val]) => (
                <div key={key} className="bg-slate-900/30 rounded-lg p-4 border border-slate-700/30">
                  <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{key.replace(/_/g, ' ')}</div>
                  <div className="text-sm font-mono text-slate-200">
                    {val !== null ? val : 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
