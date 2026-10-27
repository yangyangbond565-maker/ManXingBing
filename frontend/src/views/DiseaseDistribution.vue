<template>
  <div class="page">
    <div class="page-head"><div><h1>慢性病类型分布</h1><p>疾病占比、严重程度与共病数量；严重度按原始业务口径分为轻度/中度/重度</p></div>
      <el-tag effect="plain" type="success">10 类慢性病</el-tag></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="诊断记录" :value="data?.summary?.totalRecords" unit="条" hint="disease_record" icon="Document" />
      <StatCard label="患病人数" :value="data?.summary?.totalPatients" unit="人" hint="去重患者" icon="UserFilled" color="#7c3aed" tint="rgba(124,58,237,.1)" />
      <StatCard label="疾病类型" :value="data?.summary?.diseaseTypes" unit="类" hint="高血压、糖尿病等" icon="FirstAidKit" color="#10b981" tint="rgba(16,185,129,.1)" />
      <StatCard label="平均共病数" :value="avgComorb" unit="种" hint="按患者去重统计" icon="DataLine" color="#f59e0b" tint="rgba(245,158,11,.12)" />
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="疾病患者数" subtitle="按患者人数降序" class="span-1"><BaseChart :option="diseaseOption" height="350px" :empty="!types.length" /></ChartPanel>
      <ChartPanel title="严重程度构成" subtitle="每种疾病内部轻/中/重度占比"><BaseChart :option="severityOption" height="350px" :empty="!severity.length" /></ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="共病数量分布" subtitle="同一患者被诊断的慢性病种类数"><BaseChart :option="comorbOption" height="300px" :empty="!comorb.length" /></ChartPanel>
      <ChartPanel title="疾病明细" subtitle="患者数、记录数、重度占比">
        <el-table :data="types" height="300" size="small" stripe>
          <el-table-column prop="diseaseType" label="疾病类型" />
          <el-table-column prop="patientCount" label="患者数" align="right"><template #default="{row}">{{ nf(row.patientCount) }}</template></el-table-column>
          <el-table-column prop="recordCount" label="记录数" align="right"><template #default="{row}">{{ nf(row.recordCount) }}</template></el-table-column>
          <el-table-column prop="severeRate" label="重度占比" align="right"><template #default="{row}">{{ pct(row.severeRate) }}</template></el-table-column>
        </el-table>
      </ChartPanel>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import StatCard from '../components/StatCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { useAsync } from '../composables/useAsync'
import { getDisease } from '../api'
import { nf, pct, axis, grid, tooltip } from '../utils/format'
const { data, loading, error } = useAsync(getDisease)
const types = computed(() => data.value?.diseaseTypes || [])
const severity = computed(() => data.value?.severity || [])
const comorb = computed(() => data.value?.comorbidity || [])
const avgComorb = computed(() => { const t = comorb.value.reduce((s,x)=>s+x.patientCount,0); if(!t) return '—'; return (comorb.value.reduce((s,x)=>s+x.diseaseCount*x.patientCount,0)/t).toFixed(2) })
const diseaseOption = computed(() => ({ tooltip, grid:{ ...grid, left:10, right:30 }, xAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, yAxis:{ type:'category', data: types.value.map(x=>x.diseaseType).reverse(), ...axis }, series:[{ type:'bar', data: types.value.map(x=>x.patientCount).reverse(), barWidth:13, itemStyle:{ borderRadius:[0,6,6,0], color:{ type:'linear', x:0,y:0,x2:1,y2:0, colorStops:[{offset:0,color:'#7c3aed'},{offset:1,color:'#22d3ee'}] } }, label:{ show:true, position:'right', fontSize:10, color:'#52657f' } }] }))
const severityOption = computed(() => {
  const names = [...new Set(severity.value.map(x=>x.diseaseType))]
  const levels = ['轻度','中度','重度']
  return { tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:38 }, xAxis:{ type:'category', data:names, ...axis, axisLabel:{ ...axis.axisLabel, interval:0, rotate:30 } }, yAxis:{ type:'value', ...axis, splitLabel:{ color:'#7b8ca4' }, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series: levels.map((lv,i)=>({ name:lv, type:'bar', stack:'s', data:names.map(n=>severity.value.find(x=>x.diseaseType===n&&x.severity===lv)?.recordCount||0), itemStyle:{ color:['#10b981','#f59e0b','#ef4444'][i] } })) }
})
const comorbOption = computed(() => ({ tooltip, grid:{ ...grid, top:24 }, xAxis:{ type:'category', data: comorb.value.map(x=>x.diseaseCount+' 种'), ...axis }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ type:'bar', data: comorb.value.map(x=>x.patientCount), barWidth:44, itemStyle:{ borderRadius:[7,7,0,0], color:'#06b6d4' }, label:{ show:true, position:'top', color:'#52657f', fontSize:11 } }] }))
</script>
