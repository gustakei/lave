/**
 * Exporta resultados para CSV
 */
export function exportToCSV(results, startDate, endDate) {
  // Cabeçalho
  const headers = ['Unidade', 'Data', 'Kg', 'Total Unidade', 'Erro']
  
  // Linhas de dados
  const rows = []
  
  results.forEach(result => {
    const unitId = result.unit_id
    const total = result.total.toFixed(2)
    const error = result.error || ''
    
    if (result.rows && result.rows.length > 0) {
      result.rows.forEach(row => {
        rows.push([
          unitId,
          new Date(row.date).toLocaleDateString('pt-BR'),
          row.kg.toFixed(2),
          total,
          error
        ])
      })
    } else {
      rows.push([unitId, '', '', total, error])
    }
  })
  
  // Monta CSV
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')
  
  // Adiciona BOM para UTF-8
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  
  // Cria link de download
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  const filename = `autolav_${startDate}_${endDate}_${new Date().getTime()}.csv`
  
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}
