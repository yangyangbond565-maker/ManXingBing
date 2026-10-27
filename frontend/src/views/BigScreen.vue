<template>
  <div class="screen">
    <div class="screen-head">
      <div class="head-left"><span class="live"><i></i> LIVE</span><span class="sys">社区慢性病大数据分析平台</span></div>
      <h1>社区慢性病大数据可视化大屏</h1>
      <div class="head-right"><span>{{ clock }}</span><el-button text class="back" @click="$router.push('/home')">返回管理台</el-button></div>
    </div>
    <div class="kpis">
      <div class="kpi" v-for="k in kpis" :key="k.label">
        <div class="kpi-label">{{ k.label }}</div>
        <div class="kpi-val">{{ k.value }}<small>{{ k.unit }}</small></div>
        <div class="kpi-hint">{{ k.hint }}</div>
      </div>
    </div>
    <div class="screen-grid">
      <div class="s-panel left-top"><div class="s-title">慢性病类型分布 <span>患者数 / 人</span></div><BaseChart :option="diseaseOption" height="300px" /></div>
      <div class="s-panel center"><div class="s-title">年度确诊趋势与线性预测 <span>2018-2029</span></div><BaseChart :option="trendOption" height="300px" /></div>
      <div class="s-panel right-top"><div class="s-title">健康等级构成 <span>100,000 人</span></div><BaseChart :option="levelOption" height="300px" /></div>
      <div class="s-panel left-bottom"><div class="s-title">年龄结构 <span>患者画像</span></div><BaseChart :option="ageOption" height="260px" /></div>
      <div class="s-panel center-bottom"><div class="s-title">风险因素相关记录 <span>吸烟 / 饮酒 / 无运动 / 重口味</span></div><BaseChart :option="riskOption" height="260px" /></div>
      <div class="s-panel right-bottom"><div class="s-title">就医费用结构 <span>次均费用 / 元</span></div><BaseChart :option="visitOption" height="260px" /></div>
    </div>
    <div class="ticker"><span class="ticker-label">数据说明</span><div class="ticker-track">本大屏展示 100,000 名虚构患者、2,065,156 条业务记录的真实查询结果；健康评分与趋势预测为教学模型，不构成临床诊断。数据链路：MySQL → Spark SQL → MySQL ADS → Spring Boot → Vue3 + ECharts。</div></div>
  </div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import BaseChart from '../components/BaseChart.vue'
import { getOverview, getDisease, getTrend, getHealthOverview, getRisk, getVisits } from '../api'
import { nf, axis, tooltip } from '../utils/format'
const overview = ref(null); const disease = ref(null); const trend = ref(null); const health = ref(null); const risk = ref([]); const visits = ref(null)
const clock = ref('')
let timer, ticker
const load = async () => {
  try {
    const [o,d,t,h,r,v] = await Promise.all([getOverview(), getDisease(), getTrend('year'), getHealthOverview(), getRisk(), getVisits()])
    overview.value=o; disease.value=d; trend.value=t; health.value=h; risk.value=r; visits.value=v
  } catch(e) { console.warn(e) }
}
const kpis = computed(() => [
  { label: '管理患者', value: nf(overview.value?.totalPatients), unit: '人', hint: 'patient_info' },
  { label: '慢病记录', value: nf(overview.value?.totalDiseaseRecords), unit: '条', hint: 'disease_record' },
  { label: '平均健康评分', value: overview.value?.avgHealthScore ?? '—', unit: '分', hint: '8 维加权 0-100' },
  { label: '高危人群', value: overview.value?.highRiskRate ?? '—', unit: '%', hint: '评分 < 50' },
  { label: '累计医疗费用', value: (Number(overview.value?.totalCost || 0)/100000000).toFixed(2), unit: '亿元', hint: 'visit_record 汇总' }
])
const darkAxis = { ...axis, axisLine:{ lineStyle:{ color:'rgba(120,180,255,.25)' } }, axisLabel:{ color:'#7ea6d9', fontSize:10 } }
const darkTooltip = { ...tooltip, backgroundColor:'rgba(4,15,30,.95)', borderColor:'rgba(34,211,238,.35)', textStyle:{ color:'#dff6ff', fontSize:11 } }
const diseaseOption = computed(() => { const d=(disease.value?.diseaseTypes||[]).slice(0,8).reverse(); return { tooltip:darkTooltip, grid:{ left:8,right:24,top:12,bottom:8,containLabel:true }, xAxis:{ type:'value', ...darkAxis, splitLine:{ lineStyle:{ color:'rgba(120,180,255,.1)' } } }, yAxis:{ type:'category', data:d.map(x=>x.diseaseType), ...darkAxis }, series:[{ type:'bar', data:d.map(x=>x.patientCount), barWidth:11, itemStyle:{ borderRadius:[0,6,6,0], color:{type:'linear',x:0,y:0,x2:1,y2:0,colorStops:[{offset:0,color:'#1d4ed8'},{offset:1,color:'#22d3ee'}]} }, label:{show:true,position:'right',color:'#9bd8ff',fontSize:9} }] } })
const trendOption = computed(() => { const rows=(trend.value?.rows||[]).filter(x=>x.grain==='year'&&x.diseaseType==='全部'); const actualRows=rows.filter(x=>Number(x.isForecast)===0); const years=[...new Set(rows.map(x=>x.period))].sort(); const a=Object.fromEntries(actualRows.map(x=>[x.period,x.cases])); const p=Object.fromEntries(rows.map(x=>[x.period,x.predictedCases])); return { tooltip:darkTooltip, legend:{ top:0, textStyle:{color:'#8fb6e3'}, icon:'circle' }, grid:{ left:18,right:18,top:30,bottom:8,containLabel:true }, xAxis:{ type:'category', data:years, ...darkAxis, boundaryGap:false }, yAxis:{ type:'value', ...darkAxis, splitLine:{ lineStyle:{ color:'rgba(120,180,255,.1)' } } }, series:[{name:'实际',type:'line',smooth:true,data:years.map(y=>a[y]??null),symbolSize:5,lineStyle:{width:2,color:'#22d3ee'},itemStyle:{color:'#22d3ee'},areaStyle:{color:'rgba(34,211,238,.12)'}},{name:'拟合/预测',type:'line',smooth:true,data:years.map(y=>p[y]??null),symbolSize:4,lineStyle:{width:1.5,type:'dashed',color:'#fbbf24'},itemStyle:{color:'#fbbf24'}}] } })
const levelOption = computed(() => ({ tooltip:{...darkTooltip, trigger:'item', formatter:'{b}<br/>{c} 人（{d}%）'}, legend:{ bottom:0, textStyle:{color:'#8fb6e3'}, icon:'circle' }, series:[{ type:'pie', radius:['42%','66%'], center:['50%','44%'], label:{ show:false }, itemStyle:{ borderColor:'#071a2f', borderWidth:3 }, data:(health.value?.levels||[]).map((x,i)=>({name:x.level,value:x.patientCount,itemStyle:{color:['#10b981','#38bdf8','#f59e0b','#fb7185','#ef4444'][i]}})) }] }))
const ageOption = computed(() => { const d=health.value?.ageGroups||[]; return { tooltip:darkTooltip, grid:{left:8,right:16,top:10,bottom:8,containLabel:true}, xAxis:{type:'category',data:d.map(x=>x.ageGroup),...darkAxis,axisLabel:{...darkAxis.axisLabel,interval:0,rotate:25}}, yAxis:{type:'value',...darkAxis,splitLine:{lineStyle:{color:'rgba(120,180,255,.1)'}}}, series:[{type:'bar',data:d.map(x=>x.patientCount),barWidth:18,itemStyle:{borderRadius:[5,5,0,0],color:'#7c3aed'},label:{show:true,position:'top',color:'#c4b5fd',fontSize:9,formatter:p=>Number(p.value).toLocaleString()}}] } })
const riskOption = computed(() => { const types=['smoking','drinking','exercise','diet']; const labels={smoking:'吸烟',drinking:'饮酒',exercise:'无运动',diet:'重口味'}; const vals=types.map(t=>{ const rs=risk.value.filter(x=>x.factorType===t); if(t==='exercise') return rs.find(x=>x.factorValue==='无')?.patientCount||0; if(t==='diet') return rs.find(x=>x.factorValue==='重口味')?.patientCount||0; return rs.reduce((s,x)=>s+x.patientCount,0) }); return { tooltip:darkTooltip, grid:{left:8,right:16,top:10,bottom:8,containLabel:true}, xAxis:{type:'category',data:types.map(t=>labels[t]),...darkAxis}, yAxis:{type:'value',...darkAxis,splitLine:{lineStyle:{color:'rgba(120,180,255,.1)'}}}, series:[{type:'bar',data:vals,barWidth:30,itemStyle:{borderRadius:[6,6,0,0],color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'#f59e0b'},{offset:1,color:'#ef4444'}]}},label:{show:true,position:'top',color:'#ffd28a',fontSize:9}}] } })
const visitOption = computed(() => { const d=(visits.value?.rows||[]).filter(x=>x.analysisType==='type'); return { tooltip:darkTooltip, grid:{left:12,right:16,top:10,bottom:8,containLabel:true}, xAxis:{type:'category',data:d.map(x=>x.dimensionValue),...darkAxis}, yAxis:{type:'value',...darkAxis,splitLine:{lineStyle:{color:'rgba(120,180,255,.1)'}}}, series:[{type:'bar',data:d.map(x=>x.avgCost),barWidth:26,itemStyle:{borderRadius:[6,6,0,0],color:'#22d3ee'},label:{show:true,position:'top',color:'#9bd8ff',fontSize:9,formatter:p=>'¥'+Number(p.value).toFixed(0)}}] } })
onMounted(() => {
  load(); timer = setInterval(load, 300000); ticker = setInterval(() => { clock.value = new Date().toLocaleString('zh-CN', { hour12: false }) }, 1000)
  clock.value = new Date().toLocaleString('zh-CN', { hour12: false })
})
onBeforeUnmount(() => { clearInterval(timer); clearInterval(ticker) })
</script>
<style scoped>
.screen { min-height:100vh; background: radial-gradient(1200px 600px at 50% -10%, #0b3b66 0%, #06172b 45%, #030c18 100%); color:#dff6ff; padding:18px 22px 8px; overflow:hidden; }
.screen-head { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:18px; border-bottom:1px solid rgba(34,211,238,.25); padding-bottom:12px; }
.screen-head h1 { margin:0; font-size:26px; letter-spacing:3px; background:linear-gradient(90deg,#7dd3fc,#fff,#67e8f9); -webkit-background-clip:text; color:transparent; white-space:nowrap; }
.head-left,.head-right { display:flex; align-items:center; gap:12px; font-size:12px; color:#7ea6d9; }
.head-right { justify-content:flex-end; }
.live { color:#22d3ee; border:1px solid rgba(34,211,238,.4); border-radius:20px; padding:3px 9px; font-size:10px; letter-spacing:1px; }
.live i { display:inline-block; width:6px; height:6px; border-radius:50%; background:#22d3ee; margin-right:5px; box-shadow:0 0 8px #22d3ee; }
.back { color:#8fb6e3; }
.kpis { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:14px 0; }
.kpi { background:linear-gradient(180deg,rgba(13,45,78,.9),rgba(6,23,43,.7)); border:1px solid rgba(34,211,238,.22); border-radius:10px; padding:10px 14px; position:relative; overflow:hidden; }
.kpi:before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:linear-gradient(#22d3ee,#2563eb); }
.kpi-label { font-size:11px; color:#7ea6d9; }
.kpi-val { font-size:26px; font-weight:800; color:#fff; margin-top:3px; text-shadow:0 0 18px rgba(34,211,238,.3); }
.kpi-val small { font-size:11px; color:#7ea6d9; margin-left:4px; font-weight:400; }
.kpi-hint { font-size:10px; color:#52799f; margin-top:2px; }
.screen-grid { display:grid; grid-template-columns:1.05fr 1.55fr 1.05fr; grid-template-rows:auto auto; gap:12px; }
.s-panel { background:linear-gradient(180deg,rgba(10,33,58,.82),rgba(5,18,34,.68)); border:1px solid rgba(34,211,238,.18); border-radius:10px; padding:8px 12px 4px; }
.s-title { font-size:12px; color:#b9e6ff; letter-spacing:1px; display:flex; justify-content:space-between; border-left:3px solid #22d3ee; padding-left:8px; }
.s-title span { color:#52799f; font-size:10px; letter-spacing:0; }
.ticker { margin-top:10px; display:flex; align-items:center; gap:12px; border-top:1px solid rgba(34,211,238,.18); padding-top:8px; font-size:10px; color:#6f97bc; overflow:hidden; }
.ticker-label { color:#22d3ee; border:1px solid rgba(34,211,238,.35); border-radius:3px; padding:2px 6px; flex:0 0 auto; }
.ticker-track { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
@media(max-width:1200px){ .kpis{grid-template-columns:repeat(3,1fr)} .screen-grid{grid-template-columns:1fr 1fr} .screen-head h1{font-size:18px} }
</style>