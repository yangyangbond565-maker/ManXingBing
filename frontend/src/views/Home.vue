<template>
  <div class="page">
    <div class="page-head">
      <div><h1>社区慢性病数据总览</h1><p>七张业务表 · 八个分析模块 · 数据来自真实 MySQL / Spark 分析结果</p></div>
      <el-button type="primary" @click="$router.push('/screen')"><el-icon><Monitor /></el-icon> 打开可视化大屏</el-button>
    </div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="管理患者" :value="overview?.totalPatients" unit="人" hint="patient_info 实测记录" icon="UserFilled" color="#2563eb" />
      <StatCard label="慢病记录" :value="overview?.totalDiseaseRecords" unit="条" hint="165,087 条诊断记录" icon="FirstAidKit" color="#7c3aed" tint="rgba(124,58,237,.1)" />
      <StatCard label="平均健康评分" :value="overview?.avgHealthScore" unit="分" hint="0-100 分，越高越健康" icon="Odometer" color="#10b981" tint="rgba(16,185,129,.1)" />
      <StatCard label="高危人群占比" :value="overview?.highRiskRate" unit="%" hint="health_score < 50" icon="Warning" color="#ef4444" tint="rgba(239,68,68,.1)" />
    </div>

    <div class="grid grid-3 mt-16">
      <ChartPanel title="慢性病类型分布" subtitle="按患者人数排序（TOP 8）" class="span-2">
        <BaseChart :option="diseaseOption" height="330px" :loading="loading" :empty="!disease?.diseaseTypes?.length" />
      </ChartPanel>
      <ChartPanel title="健康等级构成" subtitle="优秀 / 良好 / 一般 / 较差 / 危险">
        <BaseChart :option="levelOption" height="330px" :loading="loading" :empty="!health?.levels?.length" />
      </ChartPanel>
    </div>

    <div class="grid grid-3 mt-16">
      <ChartPanel title="年度确诊趋势" subtitle="真实病例数；预测结果见趋势预测页" class="span-2">
        <BaseChart :option="trendOption" height="300px" :loading="loading" :empty="!trendRows.length" />
      </ChartPanel>
      <ChartPanel title="分析链路状态" subtitle="MySQL → Spark SQL → MySQL ADS → API">
        <div class="chain">
          <div class="chain-item" v-for="(x, i) in chain" :key="x.name">
            <span class="chain-index">{{ i + 1 }}</span>
            <div><b>{{ x.name }}</b><small>{{ x.desc }}</small></div>
            <el-icon class="chain-ok"><CircleCheckFilled /></el-icon>
          </div>
        </div>
        <div class="quality-mini" v-if="quality?.summary">
          <span>数据质量</span><b>{{ quality.summary.passedTables }}/7 表通过</b>
          <span>问题 {{ quality.summary.totalIssues }} 项</span>
        </div>
      </ChartPanel>
    </div>

    <div class="grid grid-4 mt-16">
      <div class="panel module-card" v-for="m in modules" :key="m.path" @click="$router.push(m.path)">
        <div class="module-ico" :style="{ background: m.tint, color: m.color }"><el-icon :size="20"><component :is="m.icon" /></el-icon></div>
        <div><b>{{ m.name }}</b><small>{{ m.desc }}</small></div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import StatCard from '../components/StatCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { useAsync } from '../composables/useAsync'
import { getOverview, getDisease, getTrend, getHealthOverview, getDataQuality } from '../api'
import { nf, axis, grid, tooltip } from '../utils/format'

const { data: overview, loading, error } = useAsync(getOverview)
const { data: disease } = useAsync(getDisease)
const { data: trend } = useAsync(() => getTrend('year'))
const { data: health } = useAsync(getHealthOverview)
const { data: quality } = useAsync(getDataQuality)

const trendRows = computed(() => (trend.value?.rows || []).filter(r => Number(r.isForecast) === 0).filter(r => r.diseaseType === '全部'))
const diseaseOption = computed(() => ({
  tooltip: { ...tooltip, formatter: p => p.map(x => x.name + '：' + nf(x.value) + ' 人').join('<br/>') },
  grid: { ...grid, left: 8, right: 24 },
  xAxis: { type: 'value', ...axis, splitLine: { lineStyle: { color: '#eef3f9' } } },
  yAxis: { type: 'category', data: (disease.value?.diseaseTypes || []).slice(0, 8).map(x => x.diseaseType).reverse(), ...axis },
  series: [{ type: 'bar', data: (disease.value?.diseaseTypes || []).slice(0, 8).map(x => x.patientCount).reverse(), barWidth: 14, itemStyle: { borderRadius: [0, 7, 7, 0], color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#2563eb' }, { offset: 1, color: '#22d3ee' }] } }, label: { show: true, position: 'right', color: '#52657f', fontSize: 11 } }]
}))
const levelOption = computed(() => ({
  tooltip: { ...tooltip, trigger: 'item', formatter: '{b}<br/>{c} 人（{d}%）' },
  legend: { bottom: 0, icon: 'circle', textStyle: { color: '#64748b', fontSize: 11 } },
  series: [{ type: 'pie', radius: ['45%', '68%'], center: ['50%', '45%'], avoidLabelOverlap: true, itemStyle: { borderColor: '#fff', borderWidth: 3, borderRadius: 5 }, label: { show: false }, data: (health.value?.levels || []).map((x, i) => ({ name: x.level, value: x.patientCount, itemStyle: { color: ['#10b981', '#2563eb', '#f59e0b', '#fb7185', '#ef4444'][i] } })) }]
}))
const trendOption = computed(() => ({
  tooltip: { ...tooltip, formatter: p => p[0].axisValue + ' 年<br/>确诊 ' + nf(p[0].value) + ' 例' },
  grid: { ...grid, left: 18, right: 20 },
  xAxis: { type: 'category', data: trendRows.value.map(x => x.period), ...axis, boundaryGap: false },
  yAxis: { type: 'value', ...axis, splitLine: { lineStyle: { color: '#eef3f9' } } },
  series: [{ type: 'line', smooth: true, symbolSize: 7, data: trendRows.value.map(x => x.cases), lineStyle: { width: 3, color: '#2563eb' }, itemStyle: { color: '#2563eb' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(37,99,235,.25)' }, { offset: 1, color: 'rgba(37,99,235,0)' }] } } }]
}))
const chain = [
  { name: 'MySQL 业务库', desc: '7 张表 · 2,065,156 行' },
  { name: 'Spark SQL', desc: '8 个模块 · 清洗、画像、预测、评分' },
  { name: 'MySQL ADS', desc: '分析结果落库 · 15 张结果表' },
  { name: 'Spring Boot + Vue3', desc: 'REST API · 实时查询与可视化' }
]
const modules = [
  { name: '患者画像', desc: '性别 / 年龄 / 地域', path: '/profile', icon: 'User', color: '#2563eb', tint: 'rgba(37,99,235,.1)' },
  { name: '疾病分布', desc: '类型 / 严重度 / 共病', path: '/disease', icon: 'FirstAidKit', color: '#7c3aed', tint: 'rgba(124,58,237,.1)' },
  { name: '风险因素', desc: '吸烟 / 饮酒 / BMI', path: '/risk', icon: 'Warning', color: '#f59e0b', tint: 'rgba(245,158,11,.12)' },
  { name: '就诊行为', desc: '费用 / 医保 / 科室', path: '/visits', icon: 'Calendar', color: '#06b6d4', tint: 'rgba(6,182,212,.1)' },
  { name: '用药分析', desc: 'TOP 药物 / 有效率', path: '/medications', icon: 'Sugar', color: '#10b981', tint: 'rgba(16,185,129,.1)' },
  { name: '趋势预测', desc: '线性回归 2026-2029', path: '/trend', icon: 'TrendCharts', color: '#ef4444', tint: 'rgba(239,68,68,.1)' },
  { name: '健康评分', desc: '8 维加权 0-100 分', path: '/health', icon: 'Odometer', color: '#0ea5e9', tint: 'rgba(14,165,233,.1)' },
  { name: '数据质量', desc: '7 表完整性与约束', path: '/data-quality', icon: 'CircleCheck', color: '#64748b', tint: 'rgba(100,116,139,.12)' }
]
</script>
<style scoped>
.mb { margin-bottom: 14px; }
.span-2 { grid-column: span 2; }
.module-card { display: flex; align-items: center; gap: 12px; padding: 15px; cursor: pointer; transition: transform .15s ease, box-shadow .15s ease; }
.module-card:hover { transform: translateY(-2px); box-shadow: 0 14px 34px rgba(15,40,80,.11); }
.module-ico { width: 38px; height: 38px; border-radius: 10px; display: grid; place-items: center; flex: 0 0 auto; }
.module-card b { display: block; font-size: 13px; }
.module-card small { display: block; color: var(--muted); font-size: 11px; margin-top: 3px; }
.arrow { margin-left: auto; color: #b7c4d6; }
.chain { display: flex; flex-direction: column; gap: 12px; }
.chain-item { display: flex; align-items: center; gap: 10px; padding: 9px 0; border-bottom: 1px dashed #e8eef7; }
.chain-index { width: 24px; height: 24px; border-radius: 50%; background: #eef5ff; color: #2563eb; display: grid; place-items: center; font-size: 11px; font-weight: 700; }
.chain-item b { display: block; font-size: 12px; }
.chain-item small { display: block; color: var(--muted); font-size: 10px; margin-top: 2px; }
.chain-ok { margin-left: auto; color: #10b981; }
.quality-mini { margin-top: 14px; background: #f7fbff; border: 1px solid #e4eefb; border-radius: 9px; padding: 10px; display: flex; gap: 12px; align-items: center; font-size: 11px; color: #64748b; }
.quality-mini b { color: #0f2a4d; }
@media (max-width: 1200px) { .span-2 { grid-column: span 1; } }
</style>
