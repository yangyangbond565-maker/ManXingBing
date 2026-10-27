<template>
  <div class="page">
    <div class="page-head"><div><h1>患者人群画像</h1><p>性别、年龄、省份与年龄×性别交叉分布，数据来自 ads_patient_profile</p></div>
      <el-tag type="info" effect="plain">患者 {{ nf(data?.totalPatients) }} 人</el-tag></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-3" v-loading="loading">
      <ChartPanel title="性别构成" subtitle="男 / 女患者占比"><BaseChart :option="genderOption" height="300px" :empty="!gender.length" /></ChartPanel>
      <ChartPanel title="年龄分组" subtitle="按 5 个年龄段统计"><BaseChart :option="ageOption" height="300px" :empty="!age.length" /></ChartPanel>
      <ChartPanel title="省份分布" subtitle="患者人数 TOP 10"><BaseChart :option="provinceOption" height="300px" :empty="!province.length" /></ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="年龄 × 性别交叉" subtitle="堆叠展示不同年龄段的性别结构"><BaseChart :option="ageGenderOption" height="340px" :empty="!ageGender.length" /></ChartPanel>
      <ChartPanel title="省份患者明细" subtitle="按患者人数降序，完整结果来自后端">
        <el-table :data="province" height="340" size="small" stripe>
          <el-table-column type="index" label="#" width="48" />
          <el-table-column prop="dimensionValue" label="省份" />
          <el-table-column prop="patientCount" label="患者数" align="right"><template #default="{ row }">{{ nf(row.patientCount) }}</template></el-table-column>
          <el-table-column prop="percentage" label="占比" align="right"><template #default="{ row }">{{ pct(row.percentage) }}</template></el-table-column>
          <el-table-column prop="avgAge" label="平均年龄" align="right" />
        </el-table>
      </ChartPanel>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { useAsync } from '../composables/useAsync'
import { getProfile } from '../api'
import { nf, pct, axis, grid, tooltip } from '../utils/format'
const { data, loading, error } = useAsync(getProfile)
const rows = computed(() => data.value?.rows || [])
const gender = computed(() => rows.value.filter(x => x.dimensionType === 'gender'))
const age = computed(() => rows.value.filter(x => x.dimensionType === 'age'))
const province = computed(() => rows.value.filter(x => x.dimensionType === 'province'))
const ageGender = computed(() => rows.value.filter(x => x.dimensionType === 'age_gender'))
const genderOption = computed(() => ({ tooltip: { ...tooltip, trigger: 'item', formatter: '{b}<br/>{c} 人（{d}%）' }, legend: { bottom: 0, icon: 'circle' }, series: [{ type: 'pie', radius: ['46%','70%'], center: ['50%','44%'], itemStyle: { borderColor: '#fff', borderWidth: 3 }, label: { formatter: '{b} {d}%', position: 'inside', color: '#fff', fontSize: 11 }, data: gender.value.map((x,i)=>({ name:x.dimensionValue, value:x.patientCount, itemStyle:{ color:['#2563eb','#f472b6'][i] } })) }] }))
const ageOption = computed(() => ({ tooltip, grid: { ...grid, top: 24 }, xAxis: { type:'category', data: age.value.map(x=>x.dimensionValue), ...axis, axisLabel:{ ...axis.axisLabel, interval:0, rotate: 20 } }, yAxis: { type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series: [{ type:'bar', data: age.value.map(x=>x.patientCount), barWidth: 24, itemStyle:{ borderRadius:[6,6,0,0], color:'#3b82f6' }, label:{ show:true, position:'top', fontSize:10, color:'#52657f' } }] }))
const provinceOption = computed(() => ({ tooltip, grid:{ ...grid, left:8, right:24 }, xAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, yAxis:{ type:'category', data: province.value.slice(0,10).map(x=>x.dimensionValue).reverse(), ...axis }, series:[{ type:'bar', data: province.value.slice(0,10).map(x=>x.patientCount).reverse(), barWidth:12, itemStyle:{ borderRadius:[0,6,6,0], color:'#06b6d4' }, label:{ show:true, position:'right', fontSize:10, color:'#52657f' } }] }))
const ageGenderOption = computed(() => {
  const ages = [...new Set(ageGender.value.map(x=>x.dimensionValue))]
  const male = ages.map(a => ageGender.value.find(x=>x.dimensionValue===a && x.extraValue==='男')?.patientCount || 0)
  const female = ages.map(a => ageGender.value.find(x=>x.dimensionValue===a && x.extraValue==='女')?.patientCount || 0)
  return { tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:40 }, xAxis:{ type:'category', data:ages, ...axis, axisLabel:{ ...axis.axisLabel, interval:0, rotate:20 } }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ name:'男', type:'bar', stack:'total', data:male, itemStyle:{ color:'#2563eb' } },{ name:'女', type:'bar', stack:'total', data:female, itemStyle:{ color:'#f472b6' } }] }
})
</script>