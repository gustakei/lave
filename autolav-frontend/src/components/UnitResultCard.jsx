import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Copy, Check, AlertCircle, CheckCircle } from 'lucide-react'

export default function UnitResultCard({ result }) {
  const [copied, setCopied] = useState(false)

  const handleCopyTotal = () => {
    navigator.clipboard.writeText(result.total.toString())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const hasError = !!result.error
  const hasData = result.rows && result.rows.length > 0

  return (
    <div className="result-card">
      {/* Header */}
      <div className={`p-4 border-b ${hasError ? 'bg-red-50 border-red-200' : 'bg-gradient-to-r from-slate-50 to-blue-50 border-blue-100'}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">
            Unidade {result.unit_id}
          </h3>
          {hasError ? (
            <span className="badge-error">
              <AlertCircle className="w-3 h-3" />
              Erro
            </span>
          ) : (
            <span className="badge-success">
              <CheckCircle className="w-3 h-3" />
              Sucesso
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {hasError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-red-900 mb-1">Erro ao processar</div>
                <div className="text-sm text-red-700">{result.error}</div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Total */}
            <div className="total-highlight mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm opacity-90 mb-1 font-medium">Total Coletado</div>
                  <div className="text-3xl font-bold">
                    {result.total.toFixed(2)}
                    <span className="text-base font-normal ml-2 opacity-90">kg</span>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-white hover:bg-white/20 h-10 w-10 p-0"
                  onClick={handleCopyTotal}
                >
                  {copied ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <Copy className="w-5 h-5" />
                  )}
                </Button>
              </div>
            </div>

            {/* Tabela */}
            {hasData ? (
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Data</th>
                        <th className="text-right">Kg</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.rows.map((row, idx) => (
                        <tr key={idx}>
                          <td className="font-medium">
                            {new Date(row.date).toLocaleDateString('pt-BR')}
                          </td>
                          <td className="text-right">
                            <span className="font-semibold text-blue-600">
                              {row.kg.toFixed(2)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="text-slate-400 mb-2 text-2xl">📊</div>
                <div className="text-sm text-slate-600">
                  Nenhum dado encontrado para o período
                </div>
              </div>
            )}

            {/* Contagem */}
            {hasData && (
              <div className="mt-4 text-center">
                <span className="inline-block bg-blue-50 text-blue-700 px-4 py-2 rounded-lg text-sm font-semibold">
                  {result.rows.length} {result.rows.length === 1 ? 'dia' : 'dias'} com dados
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
