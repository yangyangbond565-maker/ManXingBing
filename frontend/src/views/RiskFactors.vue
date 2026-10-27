<template>
  <div class="page">
    <div class="page-head"><div><h1>风险因素关联分析</h1><p>吸烟、饮酒、BMI、运动、饮食与慢性病及体检指标的关联；关联不等于因果关系</p></div></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <el-tabs v-model="factor" @tab-change="load" class="risk-tabs">
      <el-tab-pane label="吸烟" name="smoking" />
      <el-tab-pane label="饮酒" name="drinking" />
      <el-tab-pane label="BMI" name="bmi" />
      <el-tab-pane label="运动" name="exercise" />
      <el-tab-pane label="饮食" name="diet" />
    </el-tabs>
    <div class="grid grid-2" v-loading="loading">
      <ChartPanel title="因素暴露与疾病患者数" :subtitle="'当前因素：' + factorLabel">
        <BaseChart :option="barOption" height="360px" :empty="!rows.length" />
      </ChartPanel>
      <ChartPanel title="因素内部构成" subtitle="同一疾病患者中该因素各水平的占比">
        <BaseChart :option="donutOption" height="360px" :empty="!rows.length" />
      </ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="指标对比" subtitle="BMI / 运动 / 饮食因素的体检均值">
        <BaseChart :option="metricOption" height="300px" :empty="!metricRows.length" />
      </ChartPanel>
      <ChartPanel title="明细数据" subtitle="后端 ads_risk_factor 原始结果">
        <el-table :data="rows" height="300" size="small" stripe>
          <el-table-column prop="factorValue" label="因素水平" />
          <el-table-column prop="diseaseType" label="疾病" />
          <el-table-column prop="patientCount" label="患者数" align="right"><template #default="{row}">{{ nf(row.patientCount) }}</template></el-table-column>
          <el-table-column prop="exposureRate" label="占比" align="right"><template #default="{row}">{{ pct(row.exposureRate) }}</template></el-table-column>
        </el-table>
      </ChartPanel>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { getRisk } from '../api'
import { nf, pct, axis, grid, tooltip } from '../utils/format'
const factor = ref('smoking')
const rows = ref([])
const loading = ref(true)
const error = ref('')
const labels = { smoking:'吸烟', drinking:'饮酒', bmi:'BMI', exercise:'运动', diet:'饮食' }
const factorLabel = computed(() => labels[factor.value])
const metricRows = computed(() => rows.value.filter(x => x.factorType !== 'smoking' && x.factorType !== 'drinking'))
const load = async () => { loading.value = true; error.value = ''; try { rows.value = await getRisk(factor.value) } catch(e) { error.value = e.message } finally { loading.value = false } }
onMounted(load)
const barOption = computed(() => { const data = rows.value.slice().sort((a,b)=>b.patientCount-a.patientCount).slice(0,10); return { tooltip, grid:{ ...grid, top:24 }, xAxis:{ type:'category', data:data.map(x=>x.diseaseType + '·' + x.factorValue), ...axis, axisLabel:{ ...axis.axisLabel, interval:0, rotate:30 } }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ type:'bar', data:data.map(x=>x.patientCount), barWidth:24, itemStyle:{ borderRadius:[6,6,0,0], color:'#f59e0b' } }] } })
const donutOption = computed(() => { const by = {}; rows.value.forEach(x => by[x.factorValue] = (by[x.factorValue]||0)+x.patientCount); return { tooltip:{ ...tooltip, trigger:'item', formatter:'{b}<br/>{c} 人次（{d}%）' }, legend:{ bottom:0, icon:'circle' }, series:[{ type:'pie', radius:['42%','68%'], center:['50%','43%'], itemStyle:{ borderColor:'#fff', borderWidth:3 }, label:{ formatter:'{b}\n{d}%' }, data:Object.entries(by).map(([name,value],i)=>({name,value,itemStyle:{color:['#f59e0b','#2563eb','#10b981','#ef4444','#7c3aed'][i%5]}})) }] } })
const metricOption = computed(() => { const data = metricRows.value.slice(0,8); return { tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:40 }, xAxis:{ type:'category', data:data.map(x=>x.factorValue), ...axis }, yAxis:[{ type:'value', name:'mmHg', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } },{ type:'value', name:'mmol/L', ...axis, splitLine:{ show:false } }], series:[{ name:'平均收缩压', type:'bar', data:data.map(x=>x.avgSbp), barWidth:22, itemStyle:{ borderRadius:[5,5,0,0], color:'#2563eb' } },{ name:'平均血糖', type:'line', yAxisIndex:1, data:data.map(x=>x.avgGlucose), smooth:true, itemStyle:{ color:'#ef4444' } }] } })
</script>
<style scoped>.risk-tabs { margin-bottom: 10px; }</style>
