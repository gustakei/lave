import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Loader2, Download, Trash2, Settings, Play, Search, BarChart3, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import './App.css'
import LoginDialog from './components/LoginDialog'
import UnitResultCard from './components/UnitResultCard'
import { exportToCSV } from './utils/export'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_TOKEN = import.meta.env.VITE_API_TOKEN || ''

function App() {
  const [units, setUnits] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 0 })
  const [loginDialogOpen, setLoginDialogOpen] = useState(false)
  const [hasCredentials, setHasCredentials] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('autolav_config')
    if (saved) {
      try {
        const config = JSON.parse(saved)
        if (config.units) setUnits(config.units)
        if (config.startDate) setStartDate(config.startDate)
        if (config.endDate) setEndDate(config.endDate)
      } catch (e) {
        console.error('Erro ao carregar configurações:', e)
      }
    }
    checkCredentials()
  }, [])

  const checkCredentials = async () => {
    try {
      const response = await fetch(`${API_URL}/api/login`, {
        headers: { 'x-api-token': API_TOKEN }
      })
      const data = await response.json()
      setHasCredentials(data.has_credentials)
    } catch (e) {
      console.error('Erro ao verificar credenciais:', e)
    }
  }

  const handleSaveConfig = () => {
    const config = { units, startDate, endDate }
    localStorage.setItem('autolav_config', JSON.stringify(config))
    alert('Configurações salvas!')
  }

  const handleClearConfig = () => {
    setUnits('')
    setStartDate('')
    setEndDate('')
    setResults([])
    localStorage.removeItem('autolav_config')
  }

  const handleDiscoverUnits = async () => {
    if (!hasCredentials) {
      alert('Configure as credenciais de login primeiro!')
      setLoginDialogOpen(true)
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/discover_units`, {
        method: 'POST',
        headers: { 'x-api-token': API_TOKEN }
      })

      if (!response.ok) throw new Error('Erro ao descobrir unidades')

      const data = await response.json()
      const unitIds = data.units.map(u => u.unit_id).join(',')
      setUnits(unitIds)
      
      alert(`${data.total} unidades descobertas!`)
    } catch (error) {
      console.error('Erro:', error)
      alert('Erro ao descobrir unidades: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleScrape = async () => {
    if (!units.trim()) {
      alert('Informe pelo menos uma unidade!')
      return
    }

    if (!startDate || !endDate) {
      alert('Informe o período (data início e fim)!')
      return
    }

    if (!hasCredentials) {
      alert('Configure as credenciais de login primeiro!')
      setLoginDialogOpen(true)
      return
    }

    setLoading(true)
    setResults([])
    
    const unitList = units.split(/[,;\n]/).map(u => u.trim()).filter(Boolean)
    setProgress({ current: 0, total: unitList.length })

    try {
      const response = await fetch(`${API_URL}/api/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-token': API_TOKEN
        },
        body: JSON.stringify({
          units: unitList,
          start_date: startDate,
          end_date: endDate
        })
      })

      if (!response.ok) {
        const error = await response.text()
        throw new Error(error)
      }

      const data = await response.json()
      
      for (let i = 0; i < data.results.length; i++) {
        setProgress({ current: i + 1, total: data.results.length })
        setResults(prev => [...prev, data.results[i]])
        await new Promise(resolve => setTimeout(resolve, 100))
      }

    } catch (error) {
      console.error('Erro:', error)
      alert('Erro ao executar scraping: ' + error.message)
    } finally {
      setLoading(false)
      setProgress({ current: 0, total: 0 })
    }
  }

  const handleExportCSV = () => {
    if (results.length === 0) {
      alert('Nenhum resultado para exportar!')
      return
    }
    exportToCSV(results, startDate, endDate)
  }

  const totalKg = results.reduce((sum, r) => sum + (r.total || 0), 0)
  const successCount = results.filter(r => !r.error).length
  const errorCount = results.filter(r => r.error).length

  return (
    <div className="min-h-screen animate-gradient p-6">
      <main className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="glass rounded-2xl p-8 flex items-center justify-between fade-in">
          <div>
            <h1 className="text-5xl font-extrabold title-gradient">
              AutoLav
            </h1>
            <p className="text-sm text-slate-600 mt-2">
              Sistema de Automação de Coleta de Dados de Lavanderia
            </p>
          </div>
          <div className="text-right flex items-center gap-4">
            {hasCredentials && (
              <span className="badge-success">
                <CheckCircle className="w-3 h-3" />
                Conectado
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLoginDialogOpen(true)}
              className="bg-white hover:bg-slate-50"
            >
              <Settings className="w-4 h-4 mr-2" />
              {hasCredentials ? 'Atualizar Login' : 'Configurar Login'}
            </Button>
          </div>
        </header>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Formulário principal */}
          <div className="lg:col-span-2">
            <div className="gradient-border h-full fade-in">
              <div className="p-8">
                <div className="space-y-6">
                  {/* Unidades */}
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Unidades
                    </label>
                    <Textarea
                      placeholder="Digite os IDs das unidades separados por vírgula ou um por linha&#10;Exemplo: 101, 102, 103"
                      value={units}
                      onChange={(e) => setUnits(e.target.value)}
                      rows={4}
                      className="w-full p-3.5 rounded-lg border border-slate-200 input-focus font-mono transition duration-200"
                    />
                    <div className="mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDiscoverUnits}
                        disabled={loading}
                        className="bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100"
                      >
                        <Search className="w-4 h-4 mr-2" />
                        Detectar todas as unidades automaticamente
                      </Button>
                    </div>
                  </div>

                  {/* Datas */}
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Data início
                      </label>
                      <Input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full p-3.5 rounded-lg border border-slate-200 input-focus transition duration-200"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Data fim
                      </label>
                      <Input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full p-3.5 rounded-lg border border-slate-200 input-focus transition duration-200"
                      />
                    </div>
                  </div>

                  {/* Botões de ação */}
                  <div className="flex items-center gap-4 pt-4">
                    <Button
                      onClick={handleScrape}
                      disabled={loading}
                      className="flex-1 py-4 px-8 btn-primary font-semibold"
                      size="lg"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Processando...
                        </>
                      ) : (
                        <>
                          <Play className="w-5 h-5 mr-2" />
                          Executar para todas as unidades
                        </>
                      )}
                    </Button>

                    <Button
                      variant="outline"
                      onClick={handleSaveConfig}
                      className="py-4 px-6 bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 font-medium"
                    >
                      Salvar
                    </Button>

                    <Button
                      variant="outline"
                      onClick={handleClearConfig}
                      className="py-4 px-6 bg-white border-slate-200 hover:bg-slate-50 font-medium"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Limpar
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar com resumo */}
          <aside className="gradient-border fade-in">
            <div className="p-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">Resumo Rápido</h3>
                  <div className="text-sm text-slate-500 mt-1">
                    {loading ? `${progress.current}/${progress.total}` : 'Pronto'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-slate-600">Total geral</div>
                  <div className="text-3xl font-extrabold title-gradient">
                    {results.length > 0 ? `${totalKg.toFixed(2)} kg` : '— kg'}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <Button
                  onClick={handleExportCSV}
                  disabled={results.length === 0}
                  className="w-full py-4 btn-primary font-semibold"
                >
                  <Download className="w-5 h-5 mr-2" />
                  Exportar CSV (tudo)
                </Button>

                <div className="warning-box">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <p className="text-sm">
                      Configure as credenciais de login antes de executar a coleta de dados.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* Progresso */}
        {loading && progress.total > 0 && (
          <div className="glass rounded-2xl p-6 fade-in">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                <span className="text-sm font-medium text-slate-700">
                  Processando unidades...
                </span>
              </div>
              <span className="text-sm font-semibold text-blue-600">
                {progress.current} / {progress.total}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Resumo de estatísticas */}
        {results.length > 0 && (
          <div className="grid md:grid-cols-4 gap-6 fade-in">
            <div className="stats-card stats-card-blue">
              <div className="text-sm text-slate-600 mb-1 font-medium">Total de Unidades</div>
              <div className="text-3xl font-bold text-slate-900">{results.length}</div>
            </div>
            <div className="stats-card stats-card-green">
              <div className="flex items-center gap-2 text-sm text-slate-600 mb-1 font-medium">
                <CheckCircle className="w-4 h-4 text-green-600" />
                Sucesso
              </div>
              <div className="text-3xl font-bold text-green-600">{successCount}</div>
            </div>
            <div className="stats-card stats-card-red">
              <div className="flex items-center gap-2 text-sm text-slate-600 mb-1 font-medium">
                <XCircle className="w-4 h-4 text-red-600" />
                Erros
              </div>
              <div className="text-3xl font-bold text-red-600">{errorCount}</div>
            </div>
            <div className="stats-card stats-card-purple">
              <div className="text-sm text-slate-600 mb-1 font-medium">Total Geral</div>
              <div className="text-3xl font-bold text-purple-600">{totalKg.toFixed(2)} kg</div>
            </div>
          </div>
        )}

        {/* Resultados */}
        {results.length > 0 && (
          <div className="fade-in">
            <h2 className="text-2xl font-bold text-white mb-6 drop-shadow-lg">
              Resultados por Unidade
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.map((result, index) => (
                <UnitResultCard key={index} result={result} />
              ))}
            </div>
          </div>
        )}

        {/* Estado vazio */}
        {!loading && results.length === 0 && (
          <div className="glass rounded-2xl p-12 text-center fade-in">
            <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl flex items-center justify-center">
              <BarChart3 className="w-10 h-10 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              Nenhum resultado ainda
            </h3>
            <p className="text-slate-600 max-w-md mx-auto">
              Configure as unidades e o período, depois clique em "Executar" para iniciar a coleta
            </p>
          </div>
        )}
      </main>

      <LoginDialog
        open={loginDialogOpen}
        onOpenChange={setLoginDialogOpen}
        onSuccess={() => {
          setHasCredentials(true)
          setLoginDialogOpen(false)
        }}
        apiUrl={API_URL}
        apiToken={API_TOKEN}
      />
    </div>
  )
}

export default App
