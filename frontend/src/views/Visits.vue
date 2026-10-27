<template>
  <div class="page">
    <div class="page-head"><div><h1>就诊行为分析</h1><p>就诊类型、费用、医保报销、科室排名与年度趋势</p></div>
      <el-tag type="info" effect="plain">{{ nf(data?.summary?.totalVisits) }} 次就诊</el-tag></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="总就诊次数" :value="data?.summary?.totalVisits" unit="次" hint="visit_record" icon="Calendar" />
      <StatCard label="就诊患者" :value="data?.summary?.totalPatients" unit="人" hint="去重患者" icon="User" color="#7c3aed" tint="rgba(124,58,237,.1)" />
      <StatCard label="次均费用" :value="money(data?.summary?.avgCost)" hint="全部就诊类型" icon="Money" color="#f59e0b" tint="rgba(245,158,11,.12)" />
      <StatCard label="平均报销比例" :value="pct(data?.summary?.avgReimbursementRate)" hint="医保支付 / 总费用" icon="Wallet" color="#10b981" tint="rgba(16,185,129,.1)" />
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="就诊类型构成" subtitle="门诊 / 急诊 / 住院">
        <BaseChart :option="typePie" height="320px" :empty="!typeRows.length" />
      </ChartPanel>
      <ChartPanel title="各类型费用对比" subtitle="次均费用与总费用">
        <BaseChart :option="costBar" height="320px" :empty="!typeRows.length" />
      </ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="科室就诊量 TOP 10" subtitle="按 visit_count 降序">
        <BaseChart :option="deptBar" height="330px" :empty="!deptRows.length" />
      </ChartPanel>
      <ChartPanel title="年度就诊趋势" subtitle="就诊次数与次均费用">
        <BaseChart :option="yearLine" height="330px" :empty="!yearRows.length" />
      </ChartPanel>
    </div>
    <ChartPanel title="就诊分析明细" subtitle="来自 ads_visit_analysis 的真实结果" class="mt-16">
      <el-table :data="data?.rows || []" size="small" stripe max-height="360">
        <el-table-column prop="analysisType" label="分析维度" width="120" />
        <el-table-column prop="dimensionValue" label="维度值" />
        <el-table-column prop="visitCount" label="就诊次数" align="right" />
        <el-table-column prop="patientCount" label="患者数" align="right" />
        <el-table-column prop="avgCost" label="次均费用" align="right"><template #default="{row}">{{ money(row.avgCost) }}</template></el-table-column>
        <el-table-column prop="totalCost" label="总费用" align="right"><template #default="{row}">{{ money(row.totalCost) }}</template></el-table-column>
        <el-table-column prop="avgReimbursementRate" label="报销率" align="right"><template #default="{row}">{{ pct(row.avgReimbursementRate) }}</template></el-table-column>
      </el-table>
    </ChartPanel>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import StatCard from '../components/StatCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { useAsync } from '../composables/useAsync'
import { getVisits } from '../api'
import { nf, pct, money, axis, grid, tooltip } from '../utils/format'
const { data, loading, error } = useAsync(() => getVisits())
const typeRows = computed(() => (data.value?.rows || []).filter(x => x.analysisType === 'type'))
const deptRows = computed(() => (data.value?.rows || []).filter(x => x.analysisType === 'department'))
const yearRows = computed(() => (data.value?.rows || []).filter(x => x.analysisType === 'year'))
const typePie = computed(() => ({ tooltip:{ ...tooltip, trigger:'item', formatter:'{b}<br/>{c} 次（{d}%）' }, legend:{ bottom:0, icon:'circle' }, series:[{ type:'pie', radius:['44%','68%'], center:['50%','43%'], itemStyle:{ borderColor:'#fff', borderWidth:3 }, label:{ formatter:'{b}\n{d}%' }, data:typeRows.value.map((x,i)=>({ name:x.dimensionValue, value:x.visitCount, itemStyle:{ color:['#2563eb','#f59e0b','#ef4444'][i%3] } })) }] }))
const costBar = computed(() => ({ tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:36 }, xAxis:{ type:'category', data:typeRows.value.map(x=>x.dimensionValue), ...axis }, yAxis:[{ type:'value', name:'元', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }], series:[{ name:'次均费用', type:'bar', data:typeRows.value.map(x=>x.avgCost), barWidth:32, itemStyle:{ borderRadius:[6,6,0,0], color:'#2563eb' } },{ name:'总费用', type:'bar', data:typeRows.value.map(x=>x.totalCost), barWidth:32, itemStyle:{ borderRadius:[6,6,0,0], color:'#22d3ee' } }] }))
const deptBar = computed(() => { const d = deptRows.value.slice().sort((a,b)=>b.visitCount-a.visitCount).slice(0,10); return { tooltip, grid:{ ...grid, left:8, right:30 }, xAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, yAxis:{ type:'category', data:d.map(x=>x.dimensionValue).reverse(), ...axis }, series:[{ type:'bar', data:d.map(x=>x.visitCount).reverse(), barWidth:13, itemStyle:{ borderRadius:[0,6,6,0], color:'#06b6d4' }, label:{ show:true, position:'right', color:'#52657f', fontSize:10 } }] } })
const yearLine = computed(() => ({ tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:36 }, xAxis:{ type:'category', data:yearRows.value.map(x=>x.dimensionValue), ...axis }, yAxis:[{ type:'value', name:'次', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } },{ type:'value', name:'元', ...axis, splitLine:{ show:false } }], series:[{ name:'就诊次数', type:'line', smooth:true, data:yearRows.value.map(x=>x.visitCount), itemStyle:{ color:'#2563eb' }, areaStyle:{ color:'rgba(37,99,235,.12)' } },{ name:'次均费用', type:'line', yAxisIndex:1, smooth:true, data:yearRows.value.map(x=>x.avgCost), itemStyle:{ color:'#f59e0b' } }] }))
</script>
