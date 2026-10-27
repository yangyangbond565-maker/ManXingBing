<template>
  <div class="page">
    <div class="page-head"><div><h1>健康评分模型</h1><p>血压 20% + 血糖 20% + BMI 15% + 血脂 15% + 心率 10% + 吸烟 8% + 饮酒 7% + 运动 5%，总分 0-100</p></div>
      <el-tag type="warning" effect="plain">高风险：评分 &lt; 50</el-tag></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="评分患者" :value="summary?.totalPatients" unit="人" hint="有最近体检与生活习惯" icon="UserFilled" />
      <StatCard label="平均评分" :value="summary?.avgScore" unit="分" hint="越高越健康" icon="Odometer" color="#10b981" tint="rgba(16,185,129,.1)" />
      <StatCard label="高风险人数" :value="summary?.highRiskCount" unit="人" hint="health_score < 50" icon="Warning" color="#ef4444" tint="rgba(239,68,68,.1)" />
      <StatCard label="评分区间" :value="scoreRange" hint="最小值 - 最大值" icon="DataLine" color="#f59e0b" tint="rgba(245,158,11,.12)" />
    </div>
    <div class="grid grid-3 mt-16">
      <ChartPanel title="健康等级构成" subtitle="五级分类"><BaseChart :option="levelPie" height="320px" :empty="!levels.length" /></ChartPanel>
      <ChartPanel title="评分分布" subtitle="每 5 分一个区间"><BaseChart :option="binBar" height="320px" :empty="!scoreBins.length" /></ChartPanel>
      <ChartPanel title="年龄组平均分" subtitle="年龄与健康评分关联"><BaseChart :option="ageBar" height="320px" :empty="!ageGroups.length" /></ChartPanel>
    </div>
    <div class="grid grid-2 mt-16">
      <ChartPanel title="性别与省份" subtitle="平均健康评分对比"><BaseChart :option="genderProvince" height="310px" :empty="!genders.length" /></ChartPanel>
      <ChartPanel title="评分公式说明" subtitle="教学模型，非临床诊断工具">
        <div class="formula">
          <div class="formula-line"><span>血压</span><b>20%</b><i style="width:20%"></i></div>
          <div class="formula-line"><span>血糖</span><b>20%</b><i style="width:20%"></i></div>
          <div class="formula-line"><span>BMI</span><b>15%</b><i style="width:15%"></i></div>
          <div class="formula-line"><span>血脂</span><b>15%</b><i style="width:15%"></i></div>
          <div class="formula-line"><span>心率</span><b>10%</b><i style="width:10%"></i></div>
          <div class="formula-line"><span>吸烟</span><b>8%</b><i style="width:8%"></i></div>
          <div class="formula-line"><span>饮酒</span><b>7%</b><i style="width:7%"></i></div>
          <div class="formula-line"><span>运动</span><b>5%</b><i style="width:5%"></i></div>
          <p class="muted small mt-10">缺失值处理：本数据集每位患者均有最近体检与生活习惯，实际覆盖率 100%；若缺失，当前实现会在连接阶段排除，后续可增加中立分兜底。</p>
        </div>
      </ChartPanel>
    </div>
    <ChartPanel title="患者评分明细" subtitle="可按等级筛选，查看每位患者的 8 个维度得分" class="mt-16">
      <div class="filter-row">
        <el-select v-model="level" placeholder="全部等级" clearable style="width: 150px" @change="loadPatients">
          <el-option v-for="x in levels" :key="x.level" :label="x.level" :value="x.level" />
        </el-select>
        <el-input v-model="keyword" placeholder="患者 ID / 省份 / 城市" clearable style="width: 240px" @keyup.enter="loadPatients" />
        <el-button type="primary" @click="loadPatients">查询</el-button>
        <span class="muted small">共 {{ patientTotal }} 人</span>
      </div>
      <el-table :data="patients" size="small" stripe v-loading="patientLoading">
        <el-table-column prop="patientId" label="患者ID" width="100" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="age" label="年龄" width="70" />
        <el-table-column prop="province" label="省份" />
        <el-table-column prop="city" label="城市" />
        <el-table-column prop="healthScore" label="健康评分" align="right" width="100" />
        <el-table-column prop="healthLevel" label="等级" width="90"><template #default="{row}"><el-tag :type="tagType(row.healthLevel)" size="small">{{ row.healthLevel }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="90" align="center"><template #default="{row}"><el-button link type="primary" @click="$router.push('/patients?keyword='+row.patientId)">详情</el-button></template></el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="size" :total="patientTotal" layout="total, prev, pager, next" @current-change="loadPatients" />
    </ChartPanel>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import StatCard from '../components/StatCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import BaseChart from '../components/BaseChart.vue'
import { getHealthOverview, getHealthPatients } from '../api'
import { nf, axis, grid, tooltip } from '../utils/format'
const data = ref(null); const loading = ref(true); const error = ref('')
const patients = ref([]); const patientTotal = ref(0); const patientLoading = ref(false)
const level = ref(''); const keyword = ref(''); const page = ref(1); const size = ref(10)
const levels = computed(() => data.value?.levels || [])
const ageGroups = computed(() => data.value?.ageGroups || [])
const genders = computed(() => data.value?.genders || [])
const provinces = computed(() => data.value?.provinces || [])
const scoreBins = computed(() => data.value?.scoreBins || [])
const summary = computed(() => data.value?.summary)
const scoreRange = computed(() => summary.value ? summary.value.minScore + ' - ' + summary.value.maxScore : '—')
const tagType = (lv) => ({ '优秀':'success','良好':'primary','一般':'warning','较差':'danger','危险':'danger' }[lv] || 'info')
const load = async () => { loading.value = true; error.value = ''; try { data.value = await getHealthOverview(); await loadPatients() } catch(e) { error.value = e.message } finally { loading.value = false } }
const loadPatients = async () => {
  patientLoading.value = true
  try { const r = await getHealthPatients({ page: page.value, size: size.value, level: level.value, keyword: keyword.value }); patients.value = r.records; patientTotal.value = r.total }
  catch(e) { error.value = e.message } finally { patientLoading.value = false }
}
onMounted(load)
const levelPie = computed(() => ({ tooltip:{ ...tooltip, trigger:'item', formatter:'{b}<br/>{c} 人（{d}%）' }, legend:{ bottom:0, icon:'circle' }, series:[{ type:'pie', radius:['44%','68%'], center:['50%','43%'], itemStyle:{ borderColor:'#fff', borderWidth:3 }, label:{ show:false }, data:levels.value.map((x,i)=>({ name:x.level, value:x.patientCount, itemStyle:{ color:['#10b981','#2563eb','#f59e0b','#fb7185','#ef4444'][i] } })) }] }))
const binBar = computed(() => ({ tooltip, grid:{ ...grid, top:24 }, xAxis:{ type:'category', data:scoreBins.value.map(x=>x.scoreBin), ...axis, name:'分' }, yAxis:{ type:'value', ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ type:'bar', data:scoreBins.value.map(x=>x.patientCount), barWidth:'70%', itemStyle:{ borderRadius:[4,4,0,0], color:'#06b6d4' } }] }))
const ageBar = computed(() => ({ tooltip, grid:{ ...grid, top:24 }, xAxis:{ type:'category', data:ageGroups.value.map(x=>x.ageGroup), ...axis, axisLabel:{ ...axis.axisLabel, interval:0, rotate:20 } }, yAxis:{ type:'value', min:0, max:100, ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ type:'bar', data:ageGroups.value.map(x=>x.avgScore), barWidth:28, itemStyle:{ borderRadius:[6,6,0,0], color:'#7c3aed' }, label:{ show:true, position:'top', fontSize:10 } }] }))
const genderProvince = computed(() => ({ tooltip, legend:{ top:0, icon:'circle' }, grid:{ ...grid, top:36 }, xAxis:{ type:'category', data:[...genders.value.map(x=>x.gender), ...provinces.value.slice(0,8).map(x=>x.province)], ...axis, axisLabel:{ ...axis.axisLabel, interval:0, rotate:30 } }, yAxis:{ type:'value', min:0, max:100, ...axis, splitLine:{ lineStyle:{ color:'#eef3f9' } } }, series:[{ name:'平均分', type:'bar', data:[...genders.value.map(x=>x.avgScore), ...provinces.value.slice(0,8).map(x=>x.avgScore)], barWidth:20, itemStyle:{ color:'#2563eb', borderRadius:[5,5,0,0] } }] }))
</script>
<style scoped>
.filter-row { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.formula-line { display: grid; grid-template-columns: 62px 44px 1fr; align-items: center; gap: 8px; margin: 9px 0; font-size: 12px; color: #52657f; }
.formula-line b { color: #0f2a4d; }
.formula-line i { height: 7px; border-radius: 6px; background: linear-gradient(90deg,#2563eb,#22d3ee); display: block; }
</style>