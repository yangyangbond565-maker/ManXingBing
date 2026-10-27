export const nf = (v) => (v === null || v === undefined || v === '' ? '—' : Number(v).toLocaleString('zh-CN'))
export const money = (v) => (v === null || v === undefined ? '—' : '¥' + Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 0 }))
export const pct = (v) => (v === null || v === undefined ? '—' : Number(v).toFixed(2) + '%')
export const axis = { axisLine: { lineStyle: { color: '#dbe5f1' } }, axisTick: { show: false }, axisLabel: { color: '#7b8ca4', fontSize: 11 } }
export const grid = { left: 12, right: 18, top: 30, bottom: 10, containLabel: true }
export const tooltip = { trigger: 'axis', backgroundColor: 'rgba(10,28,51,.92)', borderWidth: 0, textStyle: { color: '#fff', fontSize: 12 } }
