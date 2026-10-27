<template>
  <div class="page">
    <div class="page-head"><div><h1>患者查询</h1><p>按患者 ID、性别、健康等级筛选，查看七张业务表中的完整档案</p></div></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="panel filter-panel">
      <el-input v-model="filters.keyword" placeholder="患者 ID / 省份 / 城市" clearable style="width: 260px" @keyup.enter="search" />
      <el-select v-model="filters.gender" placeholder="性别" clearable style="width: 110px"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select>
      <el-select v-model="filters.level" placeholder="健康等级" clearable style="width: 130px"><el-option v-for="x in ['优秀','良好','一般','较差','危险']" :key="x" :label="x" :value="x" /></el-select>
      <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
      <el-button @click="reset">重置</el-button>
      <span class="muted small" style="margin-left:auto">共 {{ total }} 人</span>
    </div>
    <div class="panel mt-16">
      <el-table :data="rows" v-loading="loading" stripe size="small" @row-click="openDetail">
        <el-table-column prop="patientId" label="患者ID" width="100" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="age" label="年龄" width="70" />
        <el-table-column prop="province" label="省份" />
        <el-table-column prop="city" label="城市" />
        <el-table-column prop="healthScore" label="健康评分" align="right" width="100" />
        <el-table-column prop="healthLevel" label="等级" width="90"><template #default="{row}"><el-tag :type="tagType(row.healthLevel)" size="small">{{ row.healthLevel }}</el-tag></template></el-table-column>
        <el-table-column prop="createTime" label="建档时间" width="170" />
        <el-table-column label="操作" width="90" align="center"><template #default="{row}"><el-button link type="primary" @click.stop="openDetail(row)">查看档案</el-button></template></el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="size" :total="total" layout="total, prev, pager, next, jumper" @current-change="load" />
    </div>

    <el-drawer v-model="drawer" size="720px" :title="'患者档案 · ' + (detail?.patient?.patientId || '')">
      <div v-if="detail" class="detail">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="性别">{{ detail.patient.gender }}</el-descriptions-item>
          <el-descriptions-item label="年龄">{{ detail.patient.age }}</el-descriptions-item>
          <el-descriptions-item label="地区">{{ detail.patient.province }} / {{ detail.patient.city }}</el-descriptions-item>
          <el-descriptions-item label="模拟证件号" :span="2">{{ detail.patient.idNumber }}</el-descriptions-item>
          <el-descriptions-item label="健康评分"><b>{{ detail.healthScore?.healthScore ?? '—' }}</b>（{{ detail.healthScore?.healthLevel ?? '—' }}）</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detail.patient.phone }}</el-descriptions-item>
          <el-descriptions-item label="建档时间" :span="2">{{ detail.patient.createTime }}</el-descriptions-item>
        </el-descriptions>
        <el-tabs class="mt-16">
          <el-tab-pane label="慢病诊断"><el-table :data="detail.diseases" size="small" stripe max-height="260"><el-table-column prop="diseaseType" label="类型" /><el-table-column prop="diseaseName" label="名称" /><el-table-column prop="diagnoseDate" label="确诊日期" /><el-table-column prop="severity" label="严重度" /><el-table-column prop="hospital" label="医院" /></el-table></el-tab-pane>
          <el-tab-pane label="体检指标"><el-table :data="detail.checkups" size="small" stripe max-height="260"><el-table-column prop="checkupDate" label="日期" /><el-table-column prop="sbp" label="收缩压" /><el-table-column prop="dbp" label="舒张压" /><el-table-column prop="fastingGlucose" label="空腹血糖" /><el-table-column prop="bmi" label="BMI" /><el-table-column prop="tc" label="总胆固醇" /></el-table></el-tab-pane>
          <el-tab-pane label="生活习惯"><el-descriptions v-if="detail.lifestyle?.[0]" :column="2" border size="small"><el-descriptions-item label="吸烟">{{ detail.lifestyle[0].smokingStatus }}（{{ detail.lifestyle[0].smokingAmount }} 支/日）</el-descriptions-item><el-descriptions-item label="饮酒">{{ detail.lifestyle[0].drinkingStatus }}</el-descriptions-item><el-descriptions-item label="运动">{{ detail.lifestyle[0].exerciseFreq }}</el-descriptions-item><el-descriptions-item label="睡眠">{{ detail.lifestyle[0].sleepHours }} 小时</el-descriptions-item><el-descriptions-item label="饮食">{{ detail.lifestyle[0].dietPattern }}</el-descriptions-item></el-descriptions></el-tab-pane>
          <el-tab-pane label="就诊记录"><el-table :data="detail.visits" size="small" stripe max-height="260"><el-table-column prop="visitDate" label="日期" /><el-table-column prop="visitType" label="类型" /><el-table-column prop="department" label="科室" /><el-table-column prop="cost" label="费用" /><el-table-column prop="selfPay" label="自付" /></el-table></el-tab-pane>
          <el-tab-pane label="用药记录"><el-table :data="detail.medications" size="small" stripe max-height="260"><el-table-column prop="drugName" label="药品" /><el-table-column prop="drugType" label="类别" /><el-table-column prop="startDate" label="开始" /><el-table-column prop="endDate" label="结束" /><el-table-column prop="isEffective" label="有效" /></el-table></el-tab-pane>
          <el-tab-pane label="随访记录"><el-table :data="detail.followups" size="small" stripe max-height="260"><el-table-column prop="followDate" label="日期" /><el-table-column prop="followType" label="方式" /><el-table-column prop="symptomStatus" label="症状" /><el-table-column prop="medicationAdherence" label="依从性" /><el-table-column prop="doctorAdvice" label="医嘱" /></el-table></el-tab-pane>
        </el-tabs>
      </div>
      <el-empty v-else description="加载中" />
    </el-drawer>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getPatients, getPatientDetail } from '../api'
const rows = ref([]); const total = ref(0); const page = ref(1); const size = ref(10); const loading = ref(false); const error = ref('')
const filters = reactive({ keyword: '', gender: '', level: '' })
const drawer = ref(false); const detail = ref(null)
const tagType = (lv) => ({ '优秀':'success','良好':'primary','一般':'warning','较差':'danger','危险':'danger' }[lv] || 'info')
const load = async () => { loading.value = true; error.value = ''; try { const r = await getPatients({ page: page.value, size: size.value, ...filters }); rows.value = r.records; total.value = r.total } catch(e) { error.value = e.message } finally { loading.value = false } }
const search = () => { page.value = 1; load() }
const reset = () => { filters.keyword = ''; filters.gender = ''; filters.level = ''; search() }
const openDetail = async (row) => { drawer.value = true; detail.value = null; try { detail.value = await getPatientDetail(row.patientId) } catch(e) { error.value = e.message } }
onMounted(() => { const kw = new URLSearchParams(location.hash.split('?')[1] || '').get('keyword'); if (kw) filters.keyword = kw; load() })
</script>
<style scoped>
.filter-panel { display: flex; gap: 10px; align-items: center; padding: 14px 16px; flex-wrap: wrap; }
.detail { padding-bottom: 30px; }
</style>