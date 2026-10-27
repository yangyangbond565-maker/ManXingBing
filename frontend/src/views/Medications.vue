<template>
  <div class="page">
    <div class="page-head"><div><h1>用药分析</h1><p>常用药物、类别、有效率、联合用药与疾病常用药 TOP3</p></div>
      <el-tag type="success" effect="plain">{{ nf(data?.summary?.drugCount) }} 种药品</el-tag></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="用药记录" :value="data?.summary?.totalMedications" unit="条" hint="medication_record" icon="Sugar" />
      <StatCard label="用药患者" :value="data?.summary?.totalPatients" unit="人" hint="去重患者" icon="User" color="#7c3aed" tint="rgba(124,58,237,.1)" />
      <StatCard label="药品品种" :value="data?.summary?.drugCount" unit="种" hint="按 drug_name 去重" icon="FirstAidKit" color="#06b6d4" tint="rgba(6,182,212,.1)" />
      <StatCard label="总体有效率" :value="pct(data?.summary?.effectiveRate)" hint="is_effective='是'" icon="CircleCheck" color="#10b981" tint="rgba(16,185,129,.1)" />
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="常用药物 TOP 12" subtitle="按用药记录数排序">
        <BaseChart :option="topBar" height="350px" :empty="!topRows.length" />
      </ChartPanel>
      <ChartPanel title="药物类别构成" subtitle="按记录数占比">
        <BaseChart :option="typePie" height="350px" :empty="!typeRows.length" />
      </ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="联合用药分布" subtitle="每位患者使用的药品种类数">
        <BaseChart :option="comboBar" height="300px" :empty="!comboRows.length" />
      </ChartPanel>
      <ChartPanel title="各疾病常用药 TOP3" subtitle="疾病与药品的关联来自真实处方记录">
        <el-table :data="data?.byDisease || []" height="300" size="small" stripe>
          <el-table-column prop="diseaseType" label="疾病" />
          <el-table-column prop="drugName" label="药品" />
          <el-table-column prop="usageCount" label="使用次数" align="right" />
          <el-table-column prop="rankNo" label="排名" width="70" align="center" />
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
import { getMedications } from '../api'
import { nf, pct, axis, grid, tooltip } from '../utils/format'
const { data, loading, error } = useAsync(() => getMedications())
const rows = computed(() => data.value?.rows || [])
const topRows = computed(() => rows.value.filter(x => x.analysisType === 'top').sort((a,b)=>a.rankNo-b.rankNo).slice(0,12))
const typeRows = computed(() => rows.value.filter(x => x.analysisType === 'type').sort((a,b)=>b.usageCount-a.usageCount))
const comboRows = computed(() => rows.value.filter(x => x.analysisType === 'combo'))
const topBar = computed(() => ({ tooltip, grid:{ ...grid, left:8, right:30 }, xAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, yAxis:{ type:'category', data:topRows.value.map(x=>x.dimensionValue).reverse(), ...axis }, series:[{ type:'bar', data:topRows.value.map(x=>x.usageCount).reverse(), barWidth:13, itemStyle:{ borderRadius:[0,6,6,0], color:'#10b981' }, label:{ show:true, position:'right', color:'#52657f', fontSize:10 } }] }))
const typePie = computed(() => ({ tooltip:{ ...tooltip, trigger:'item', formatter:'{b}<br/>{c} 条（{d}%）' }, legend:{ type:'scroll', bottom:0, icon:'circle' }, series:[{ type:'pie', radius:['40%','66%'], center:['50%','42%'], itemStyle:{ borderColor:'#fff', borderWidth:2 }, label:{ show:false }, data:typeRows.value.map((x,i)=>({ name:x.dimensionValue, value:x.usageCount, itemStyle:{ color:['#2563eb','#10b981','#f59e0b','#7c3aed','#06b6d4','#ef4444','#84cc16'][i%7] } })) }] }))
const comboBar = computed(() => ({ tooltip, grid:{ ...grid, top:24 }, xAxis:{ type:'category', data:comboRows.value.map(x=>x.dimensionValue+' 类'), ...axis }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ type:'bar', data:comboRows.value.map(x=>x.patientCount), barWidth:40, itemStyle:{ borderRadius:[7,7,0,0], color:'#06b6d4' }, label:{ show:true, position:'top', color:'#52657f', fontSize:11 } }] }))
</script>
