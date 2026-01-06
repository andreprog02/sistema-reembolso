import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LayoutDashboard, UploadCloud, FileText, CheckCircle, 
  AlertCircle, DollarSign, Calendar, TrendingUp, Plus, Loader2, X, Save,
  Pencil, Trash2, Eye
} from 'lucide-react';

const API_URL = "http://localhost:8000";

function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); 
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [metrics, setMetrics] = useState({ total: 0, count: 0, avg: 0, byCategory: {} });

  // ESTADOS DO MODAL E EDIÇÃO
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false); // Define se é criação ou edição
  const [currentId, setCurrentId] = useState(null); // ID do item sendo editado
  
  // Dados do formulário
  const [formData, setFormData] = useState({
    numero_nota: '', estabelecimento: '', valor: 0, 
    data_emissao: '', centro_custo: 'Alimentação', arquivo_nome: '', comprovante_base64: null
  });

  useEffect(() => { fetchHistory(); }, []);

  // Recalcula métricas
  useEffect(() => {
    if (history.length > 0) {
      const total = history.reduce((acc, item) => acc + (item.valor || 0), 0);
      const count = history.length;
      const categories = {};
      history.forEach(item => {
        const cat = item.centro_custo || 'Outros';
        categories[cat] = (categories[cat] || 0) + item.valor;
      });
      setMetrics({ total, count, avg: total / count, byCategory: categories });
    }
  }, [history]);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/reembolsos/`);
      setHistory(response.data);
    } catch (error) { console.error(error); }
  };

  // --- FUNÇÃO AUXILIAR: Converte Arquivo para Base64 ---
  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  // 1. FLUXO DE UPLOAD E ANÁLISE
  const handleAnalyze = async () => {
    if (!file) return alert("Selecione um arquivo!");
    setLoading(true);
    
    try {
      // Converte a imagem para Base64 agora para guardar na memória
      const base64 = await convertToBase64(file);

      const data = new FormData();
      data.append('file', file);

      // Envia para IA
      const response = await axios.post(`${API_URL}/analisar/`, data);
      
      // Prepara dados para o Modal (Modo CRIAÇÃO)
      setFormData({
        ...response.data,
        centro_custo: 'Alimentação',
        comprovante_base64: base64 // Guarda a imagem para salvar depois
      });
      
      setIsEditing(false); // É um novo item
      setShowModal(true);
    } catch (error) {
      alert("Erro na análise: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 2. ABRIR MODAL PARA EDIÇÃO
  const handleEditClick = (item) => {
    setFormData({
      numero_nota: item.numero_nota,
      estabelecimento: item.estabelecimento,
      valor: item.valor,
      data_emissao: item.data_emissao,
      centro_custo: item.centro_custo,
      arquivo_nome: item.arquivo_nome,
      comprovante_base64: item.comprovante_base64 // Mantém a imagem antiga
    });
    setCurrentId(item.id);
    setIsEditing(true); // Modo EDIÇÃO
    setShowModal(true);
  };

  // 3. EXCLUIR ITEM
  const handleDeleteClick = async (id) => {
    if (window.confirm("Tem certeza que deseja apagar este reembolso permanentemente?")) {
      try {
        await axios.delete(`${API_URL}/reembolsos/${id}`);
        alert("🗑️ Item apagado.");
        fetchHistory();
      } catch (error) {
        alert("Erro ao apagar: " + error.message);
      }
    }
  };

  // 4. SALVAR (Criar ou Atualizar)
  const handleSave = async () => {
    try {
      if (isEditing) {
        // Rota PUT (Atualizar)
        await axios.put(`${API_URL}/reembolsos/${currentId}`, formData);
        alert("✅ Reembolso atualizado!");
      } else {
        // Rota POST (Criar Novo)
        await axios.post(`${API_URL}/salvar/`, formData);
        alert("✅ Novo reembolso salvo!");
      }
      
      setShowModal(false);
      setFile(null);
      fetchHistory();
      if (!isEditing) setActiveTab('history'); // Se criou novo, vai pro histórico
    } catch (error) {
      alert("Erro ao salvar: " + (error.response?.data?.detail || error.message));
    }
  };

  // 5. VISUALIZAR COMPROVANTE
  const handleViewReceipt = (base64) => {
    if (!base64) return alert("Nenhum comprovante salvo para este item.");
    
    // Abre uma nova aba com a imagem/PDF
    const newTab = window.open();
    newTab.document.write(
      `<iframe src="${base64}" frameborder="0" style="border:0; top:0px; left:0px; bottom:0px; right:0px; width:100%; height:100%;" allowfullscreen></iframe>`
    );
  };

  return (
    <div className="flex min-h-screen font-sans bg-dark-900 text-slate-200">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-dark-800 border-r border-dark-700 flex flex-col fixed h-full z-10">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded flex items-center justify-center">R</div>
            Reembolso<span className="text-brand-500">.ai</span>
          </h1>
        </div>
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <SidebarItem icon={<LayoutDashboard size={20}/>} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')}/>
          <SidebarItem icon={<UploadCloud size={20}/>} label="Novo Lançamento" active={activeTab === 'upload'} onClick={() => setActiveTab('upload')}/>
          <SidebarItem icon={<FileText size={20}/>} label="Histórico" active={activeTab === 'history'} onClick={() => setActiveTab('history')}/>
        </nav>
      </aside>

      {/* CONTEÚDO */}
      <main className="flex-1 ml-64 p-8 relative">
        
        {/* DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="max-w-6xl mx-auto animate-fade-in">
             <header className="flex justify-between items-end mb-8">
              <h2 className="text-3xl font-bold text-white">Dashboard</h2>
              <button onClick={() => setActiveTab('upload')} className="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium transition-colors">
                <Plus size={18} /> Novo
              </button>
            </header>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <MetricCard title="Total" value={`R$ ${metrics.total.toFixed(2)}`} icon={<DollarSign/>} />
              <MetricCard title="Notas" value={metrics.count} icon={<FileText/>} />
              <MetricCard title="Ticket Médio" value={`R$ ${metrics.avg.toFixed(2)}`} icon={<TrendingUp/>} />
            </div>
          </div>
        )}

        {/* UPLOAD */}
        {activeTab === 'upload' && (
          <div className="max-w-2xl mx-auto mt-10 animate-fade-in">
            <h2 className="text-3xl font-bold text-white mb-2">Lançar Despesa</h2>
            <div className="bg-dark-800 rounded-xl border border-dark-700 p-8 shadow-xl mt-6">
              <div className="border-2 border-dashed border-dark-700 rounded-lg p-12 text-center hover:border-brand-500 transition-colors relative">
                <input type="file" onChange={(e) => setFile(e.target.files[0])} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" accept=".jpg,.jpeg,.png,.pdf" />
                <div className="flex flex-col items-center">
                  <UploadCloud size={48} className="text-slate-500 mb-4" />
                  <p className="text-lg text-slate-200">{file ? file.name : "Clique para selecionar"}</p>
                </div>
              </div>
              
              {file && (
                <button onClick={handleAnalyze} disabled={loading} className="w-full mt-6 bg-brand-600 hover:bg-brand-500 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 transition-all">
                  {loading ? <Loader2 className="animate-spin" /> : <FileText />}
                  {loading ? "Estamos analisando..." : "Analisar Documento"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* HISTÓRICO COM AÇÕES */}
        {activeTab === 'history' && (
          <div className="max-w-6xl mx-auto animate-fade-in">
            <h2 className="text-2xl font-bold text-white mb-6">Histórico Completo</h2>
            <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-dark-900 text-slate-400 text-xs uppercase">
                  <tr>
                    <th className="p-4">Data</th>
                    <th className="p-4">Loja</th>
                    <th className="p-4">Valor</th>
                    <th className="p-4">Categoria</th>
                    <th className="p-4 text-center">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-700 text-slate-300">
                  {history.map(item => (
                    <tr key={item.id} className="hover:bg-dark-700/50 group">
                      <td className="p-4 text-sm">{item.data_emissao}</td>
                      <td className="p-4 text-white font-medium">{item.estabelecimento}</td>
                      <td className="p-4 font-mono text-emerald-400">R$ {item.valor.toFixed(2)}</td>
                      <td className="p-4 text-xs">{item.centro_custo}</td>
                      <td className="p-4">
                        <div className="flex items-center justify-center gap-2">
                          {/* BOTÃO VER COMPROVANTE */}
                          <button 
                             onClick={() => handleViewReceipt(item.comprovante_base64)}
                             title="Ver Comprovante"
                             className="p-2 hover:bg-dark-600 rounded text-blue-400"
                          >
                            <Eye size={16} />
                          </button>
                          
                          {/* BOTÃO EDITAR */}
                          <button 
                            onClick={() => handleEditClick(item)}
                            title="Editar"
                            className="p-2 hover:bg-dark-600 rounded text-yellow-500"
                          >
                            <Pencil size={16} />
                          </button>
                          
                          {/* BOTÃO EXCLUIR */}
                          <button 
                            onClick={() => handleDeleteClick(item.id)}
                            title="Excluir"
                            className="p-2 hover:bg-dark-600 rounded text-red-500"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* --- MODAL DE CRIAÇÃO / EDIÇÃO --- */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-dark-800 rounded-xl border border-dark-700 shadow-2xl w-full max-w-lg p-6 relative">
            
            <button onClick={() => setShowModal(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white">
              <X size={24} />
            </button>

            <h3 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
              {isEditing ? <Pencil className="text-yellow-500"/> : <CheckCircle className="text-brand-500" />} 
              {isEditing ? "Editar Reembolso" : "Revisar Dados da IA"}
            </h3>
            <p className="text-slate-400 text-sm mb-6">
              {isEditing ? "Altere os dados abaixo e salve." : "A IA leu estes dados. Edite se necessário."}
            </p>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 uppercase font-bold">Data</label>
                  <input 
                    type="date" 
                    value={formData.data_emissao} 
                    onChange={e => setFormData({...formData, data_emissao: e.target.value})}
                    className="w-full bg-dark-900 border border-dark-700 rounded p-2 text-white mt-1 focus:border-brand-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 uppercase font-bold">Valor (R$)</label>
                  <input 
                    type="number" 
                    step="0.01"
                    value={formData.valor} 
                    onChange={e => setFormData({...formData, valor: parseFloat(e.target.value)})}
                    className="w-full bg-dark-900 border border-dark-700 rounded p-2 text-white mt-1 focus:border-brand-500 outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 uppercase font-bold">Estabelecimento</label>
                <input 
                  type="text" 
                  value={formData.estabelecimento} 
                  onChange={e => setFormData({...formData, estabelecimento: e.target.value})}
                  className="w-full bg-dark-900 border border-dark-700 rounded p-2 text-white mt-1 focus:border-brand-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 uppercase font-bold">Nº Nota</label>
                  <input 
                    type="text" 
                    value={formData.numero_nota} 
                    onChange={e => setFormData({...formData, numero_nota: e.target.value})}
                    className="w-full bg-dark-900 border border-dark-700 rounded p-2 text-white mt-1 focus:border-brand-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 uppercase font-bold">Categoria</label>
                  <select 
                    value={formData.centro_custo}
                    onChange={e => setFormData({...formData, centro_custo: e.target.value})}
                    className="w-full bg-dark-900 border border-dark-700 rounded p-2 text-white mt-1 focus:border-brand-500 outline-none"
                  >
                    <option>Alimentação</option>
                    <option>Transporte</option>
                    <option>Hospedagem</option>
                    <option>Equipamentos</option>
                    <option>Outros</option>
                  </select>
                </div>
              </div>

               {/* Pré-visualização do anexo (se houver) */}
               {formData.comprovante_base64 && (
                <div className="mt-2 p-2 bg-dark-900 rounded border border-dark-700 text-xs text-slate-400 flex items-center justify-between">
                  <span>📄 {formData.arquivo_nome || "Comprovante anexado"}</span>
                  <button onClick={() => handleViewReceipt(formData.comprovante_base64)} className="text-brand-500 hover:underline">Ver</button>
                </div>
              )}

            </div>

            <div className="mt-8 flex gap-3">
              <button 
                onClick={() => setShowModal(false)}
                className="flex-1 py-3 rounded-lg border border-dark-700 text-slate-300 hover:bg-dark-700 transition-colors font-medium"
              >
                Cancelar
              </button>
              <button 
                onClick={handleSave}
                className="flex-1 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-colors shadow-lg flex justify-center items-center gap-2"
              >
                <Save size={18} /> {isEditing ? "Salvar Alterações" : "Confirmar Lançamento"}
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}

function SidebarItem({ icon, label, active, onClick }) {
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-3 px-4 py-3 rounded transition-all ${active ? 'bg-dark-700 text-white' : 'text-slate-400 hover:text-white'}`}>
      {icon} <span className="font-medium text-sm">{label}</span>
    </button>
  );
}

function MetricCard({ title, value, icon }) {
  return (
    <div className="bg-dark-800 p-6 rounded-xl border border-dark-700">
      <div className="flex justify-between items-start">
        <div><p className="text-slate-400 text-sm mb-1">{title}</p><h3 className="text-2xl font-bold text-white">{value}</h3></div>
        <div className="p-3 bg-dark-900 rounded-lg text-brand-500">{icon}</div>
      </div>
    </div>
  );
}

export default App;