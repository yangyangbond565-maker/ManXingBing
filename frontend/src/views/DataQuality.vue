<template>
  <div class="page">
    <div class="page-head"><div><h1>数据质量检查</h1><p>空值、重复、孤立外键、非法日期/数值、金额勾稽与 10 万患者口径核验</p></div>
      <el-tag :type="summary?.totalIssues === 0 ? 'success' : 'warning'" effect="dark">{{ summary?.totalIssues === 0 ? '全部通过' : '存在问题' }}</el-tag></div>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="mb" />
    <div class="grid grid-4" v-loading="loading">
      <StatCard label="检查表数" :value="7" unit="张" hint="七张业务表全部覆盖" icon="Files" />
      <StatCard label="检查前总行数" :value="summary?.totalBefore" hint="MySQL 实际记录" icon="Document" color="#7c3aed" tint="rgba(124,58,237,.1)" />
      <StatCard label="关键问题" :value="summary?.totalIssues" unit="项" hint="目标为 0" icon="Warning" color="#10b981" tint="rgba(16,185,129,.1)" />
      <StatCard label="通过表数" :value="summary?.passedTables" unit="/ 7" hint="status=PASS" icon="CircleCheck" color="#06b6d4" tint="rgba(6,182,212,.1)" />
    </div>
    <div class="panel mt-16">
      <div class="panel-head"><div><div class="panel-title">逐表检查结果</div><div class="panel-sub">数据质量报告由 python/chronic_disease/quality_check.py 生成并写入 ads_data_quality</div></div>
        <el-button size="small" @click="$router.push('/patients')">查看患者数据</el-button></div>
      <div class="panel-body">
        <el-table :data="data?.tables || []" stripe size="small">
          <el-table-column prop="tableName" label="表名" min-width="150" />
          <el-table-column prop="beforeCount" label="记录数" align="right" min-width="110"><template #default="{row}">{{ nf(row.beforeCount) }}</template></el-table-column>
          <el-table-column prop="nullIssues" label="空值" align="right" />
          <el-table-column prop="dupIssues" label="重复" align="right" />
          <el-table-column prop="orphanIssues" label="孤立外键" align="right" />
          <el-table-column prop="invalidIssues" label="非法值/日期" align="right" />
          <el-table-column prop="status" label="结论" width="90" align="center"><template #default="{row}"><el-tag :type="row.status === 'PASS' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag></template></el-table-column>
        </el-table>
        <div class="checks">
          <div class="check"><el-icon><CircleCheckFilled /></el-icon><b>主键与外键</b><span>7 张表均建立主键；6 张子表通过外键指向 patient_info</span></div>
          <div class="check"><el-icon><CircleCheckFilled /></el-icon><b>日期合法性</b><span>确诊、体检、就诊、用药、随访日期均校验范围与先后关系</span></div>
          <div class="check"><el-icon><CircleCheckFilled /></el-icon><b>金额勾稽</b><span>visit_record 满足 insurance_pay + self_pay = cost</span></div>
          <div class="check"><el-icon><CircleCheckFilled /></el-icon><b>10 万口径</b><span>patient_info = 100,000 人；七表总行数单独统计，不混用</span></div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import StatCard from '../components/StatCard.vue'
import { useAsync } from '../composables/useAsync'
import { getDataQuality } from '../api'
import { nf } from '../utils/format'
const { data, loading, error } = useAsync(getDataQuality)
const summary = computed(() => data.value?.summary)
</script>
<style scoped>.checks { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; margin-top: 16px; }.check { display: grid; grid-template-columns: 24px 110px 1fr; align-items: center; gap: 6px; background: #f7fbff; border: 1px solid #e4eefb; border-radius: 9px; padding: 10px 12px; color: #64748b; font-size: 12px; }.check .el-icon { color: #10b981; }.check b { color: #0f2a4d; } @media(max-width:900px){.checks{grid-template-columns:1fr}}</style>
