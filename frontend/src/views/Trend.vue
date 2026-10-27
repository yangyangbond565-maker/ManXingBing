<template>
  <div class="page">
    <div class="page-head"><div><h1>疾病发展趋势预测</h1><p>年度/月度趋势、最小二乘线性回归、2026-2029 年预测与 R² 评价</p></div>
      <el-radio-group v-model="grain" size="small" @change="load"><el-radio-button label="year">年度</el-radio-button><el-radio-button label="month">月度</el-radio-button></el-radio-group></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="回归斜率" :value="metrics?.slope" hint="每年新增病例变化" icon="TrendCharts" color="#2563eb" />
      <StatCard label="截距" :value="metrics?.intercept" hint="线性方程常数项" icon="DataLine" color="#7c3aed" tint="rgba(124,58,237,.1)" />
      <StatCard label="决定系数 R²" :value="metrics?.r2" hint="拟合优度，越接近 1 越好" icon="Aim" color="#10b981" tint="rgba(16,185,129,.1)" />
      <StatCard label="趋势方向" :value="metrics?.trend || '—'" hint="2026-2029 预测区间" icon="TopRight" color="#f59e0b" tint="rgba(245,158,11,.12)" />
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="年度实际与预测" subtitle="实线为真实病例，虚线为线性回归预测" class="span-1">
        <BaseChart :option="yearOption" height="360px" :empty="!yearActual.length && !forecast.length" />
      </ChartPanel>
      <ChartPanel title="月度确诊趋势" subtitle="2018-2025 月度病例数">
        <BaseChart :option="monthOption" height="360px" :empty="!monthRows.length" />
      </ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="预测结果表" subtitle="模型输出，不代表临床预测">
        <el-table :data="forecast" size="small" stripe height="280">
          <el-table-column prop="period" label="年份" />
          <el-table-column prop="predictedCases" label="预测病例数" align="right" />
          <el-table-column prop="slope" label="斜率" align="right" />
          <el-table-column prop="r2" label="R²" align="right" />
          <el-table-column prop="trend" label="趋势" align="center"><template #default="{row}"><el-tag :type="row.trend==='上升'?'danger':'success'" size="small">{{ row.trend }}</el-tag></template></el-table-column>
        </el-table>
      </ChartPanel>
      <ChartPanel title="算法说明与局限" subtitle="教学实训口径">
        <div class="note">
          <p><b>模型：</b>一元线性回归 y = slope × year + intercept，使用 2018-2025 年年度确诊数训练，预测 2026-2029 年。</p>
          <p><b>评价：</b>R² = 1 - SS_res / SS_tot；R² 只反映历史拟合程度，样本仅 8 个年度点，不能据此宣称临床准确率。</p>
          <p><b>数据：</b>模拟数据按年度递增权重生成，因此趋势方向可解释，但不代表真实疾病流行趋势。</p>
          <p><b>用途：</b>本科实训演示，不作为诊断、公共卫生决策或临床预测工具。</p>
        </div>
      </ChartPanel>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import StatCard from '../components/StatCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { getTrend } from '../api'
import { nf, axis, grid, tooltip } from '../utils/format'
const grain = ref('year')
const data = ref(null)
const loading = ref(true)
const error = ref('')
const load = async () => { loading.value = true; error.value = ''; try { data.value = await getTrend(grain.value) } catch(e) { error.value = e.message } finally { loading.value = false } }
onMounted(load)
const rows = computed(() => data.value?.rows || [])
const forecast = computed(() => rows.value.filter(x => Number(x.isForecast) === 1))
const yearActual = computed(() => rows.value.filter(x => x.grain === 'year' && Number(x.isForecast) === 0 && x.diseaseType === '全部'))
const monthRows = computed(() => rows.value.filter(x => x.grain === 'month'))
const metrics = computed(() => data.value?.metrics)
const yearOption = computed(() => {
  const years = [...new Set([...yearActual.value.map(x=>x.period), ...forecast.value.map(x=>x.period)])].sort()
  const actualMap = Object.fromEntries(yearActual.value.map(x=>[x.period, x.cases]))
  const predMap = Object.fromEntries([...yearActual.value, ...forecast.value].map(x=>[x.period, x.predictedCases]))
  return { tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:38 }, xAxis:{ type:'category', data:years, ...axis, boundaryGap:false }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ name:'实际病例', type:'line', smooth:true, data:years.map(y=>actualMap[y] ?? null), symbolSize:7, itemStyle:{ color:'#2563eb' }, lineStyle:{ width:3 } },{ name:'回归拟合/预测', type:'line', smooth:true, data:years.map(y=>predMap[y] ?? null), symbolSize:5, itemStyle:{ color:'#f59e0b' }, lineStyle:{ width:2, type:'dashed' } }] }
})
const monthOption = computed(() => ({ tooltip, grid:{ ...grid, top:24 }, xAxis:{ type:'category', data:monthRows.value.map(x=>x.period), ...axis, axisLabel:{ ...axis.axisLabel, rotate:45, interval: Math.max(0, Math.floor(monthRows.value.length/12)-1) } }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ type:'line', smooth:true, showSymbol:false, data:monthRows.value.map(x=>x.cases), lineStyle:{ width:2, color:'#06b6d4' }, areaStyle:{ color:'rgba(6,182,212,.12)' } }] }))
</script>
<style scoped>.note p { margin: 0 0 10px; color: #52657f; font-size: 12.5px; line-height: 1.8; }.note b { color: #0f2a4d; }</style>
