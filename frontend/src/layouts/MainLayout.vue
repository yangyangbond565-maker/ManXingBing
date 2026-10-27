<template>
  <div class="shell">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand">
        <div class="brand-mark">CD</div>
        <div v-show="!collapsed" class="brand-text">
          <strong>慢病大数据</strong>
          <span>CHRONIC DISEASE ANALYTICS</span>
        </div>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu :default-active="$route.path" :collapse="collapsed" router class="side-menu" background-color="transparent" text-color="#b8c7dd" active-text-color="#ffffff">
          <el-menu-item index="/home"><el-icon><HomeFilled /></el-icon><template #title>系统首页</template></el-menu-item>
          <div class="menu-label" v-show="!collapsed">分析模块</div>
          <el-menu-item index="/profile"><el-icon><User /></el-icon><template #title>患者画像</template></el-menu-item>
          <el-menu-item index="/disease"><el-icon><FirstAidKit /></el-icon><template #title>疾病分布</template></el-menu-item>
          <el-menu-item index="/risk"><el-icon><Warning /></el-icon><template #title>风险因素</template></el-menu-item>
          <el-menu-item index="/visits"><el-icon><Calendar /></el-icon><template #title>就诊行为</template></el-menu-item>
          <el-menu-item index="/medications"><el-icon><Sugar /></el-icon><template #title>用药分析</template></el-menu-item>
          <el-menu-item index="/trend"><el-icon><TrendCharts /></el-icon><template #title>趋势预测</template></el-menu-item>
          <el-menu-item index="/health"><el-icon><Odometer /></el-icon><template #title>健康评分</template></el-menu-item>
          <div class="menu-label" v-show="!collapsed">数据管理</div>
          <el-menu-item index="/patients"><el-icon><Search /></el-icon><template #title>患者查询</template></el-menu-item>
          <el-menu-item index="/data-quality"><el-icon><CircleCheck /></el-icon><template #title>数据质量</template></el-menu-item>
        </el-menu>
      </el-scrollbar>
      <div class="side-foot" v-show="!collapsed">
        <div class="side-foot-line"></div>
        <span>社区慢性病大数据分析系统</span>
        <small>v1.0 · 教学实训</small>
      </div>
    </aside>
    <div class="main" :class="{ wide: collapsed }">
      <header class="topbar">
        <div class="top-left">
          <el-button text class="collapse-btn" @click="collapsed = !collapsed"><el-icon :size="20"><Fold v-if="!collapsed" /><Expand v-else /></el-icon></el-button>
          <div class="crumb"><span>慢性病大数据平台</span><el-icon><ArrowRight /></el-icon><b>{{ $route.meta.title || '系统首页' }}</b></div>
        </div>
        <div class="top-right">
          <span class="api-state"><i :class="apiOk ? 'ok' : 'bad'"></i>{{ apiOk ? '服务正常' : '服务未连接' }}</span>
          <span class="date">{{ today }}</span>
          <el-button type="primary" plain size="small" @click="$router.push('/screen')"><el-icon><Monitor /></el-icon> 数据大屏</el-button>
        </div>
      </header>
      <main class="content"><router-view /></main>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { getApiHealth } from '../api'
const collapsed = ref(false)
const apiOk = ref(false)
const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
onMounted(async () => { try { await getApiHealth(); apiOk.value = true } catch { apiOk.value = false } })
</script>
<style scoped>
.shell { min-height: 100vh; display: flex; background: var(--bg); }
.sidebar { width: 226px; background: linear-gradient(180deg, #0a1c33 0%, #0c2747 100%); color: #c9d6e8; display: flex; flex-direction: column; position: fixed; inset: 0 auto 0 0; z-index: 20; transition: width .2s ease; }
.sidebar.collapsed { width: 68px; }
.brand { height: 68px; display: flex; align-items: center; gap: 10px; padding: 0 16px; border-bottom: 1px solid rgba(255,255,255,.08); }
.brand-mark { width: 34px; height: 34px; border-radius: 9px; background: linear-gradient(135deg,#2f80ed,#22d3ee); color: #fff; font-weight: 900; display: grid; place-items: center; letter-spacing: .5px; box-shadow: 0 0 18px rgba(34,211,238,.3); flex: 0 0 auto; }
.brand-text { display: flex; flex-direction: column; white-space: nowrap; overflow: hidden; }
.brand-text strong { color: #fff; font-size: 15px; letter-spacing: .5px; }
.brand-text span { color: #7690b3; font-size: 8px; letter-spacing: 1.1px; margin-top: 3px; }
.menu-scroll { flex: 1; overflow: hidden; }
.side-menu { border-right: 0; padding: 8px; }
.side-menu :deep(.el-menu-item) { height: 44px; border-radius: 9px; margin: 4px 0; font-size: 13px; }
.side-menu :deep(.el-menu-item.is-active) { background: linear-gradient(90deg,rgba(37,99,235,.85),rgba(6,182,212,.55)); box-shadow: 0 8px 18px rgba(6,120,200,.25); }
.side-menu :deep(.el-menu-item:hover) { background: rgba(255,255,255,.07); }
.menu-label { color: #6f87a7; font-size: 11px; letter-spacing: 1px; padding: 14px 12px 4px; }
.side-foot { padding: 14px 18px 20px; color: #6f87a7; font-size: 11px; line-height: 1.7; }
.side-foot-line { height: 1px; background: rgba(255,255,255,.08); margin-bottom: 12px; }
.side-foot small { display: block; color: #506b8c; }
.main { margin-left: 226px; min-width: 0; flex: 1; transition: margin-left .2s ease; }
.main.wide { margin-left: 68px; }
.topbar { height: 68px; background: rgba(255,255,255,.92); backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between; padding: 0 24px 0 10px; position: sticky; top: 0; z-index: 10; }
.top-left, .top-right { display: flex; align-items: center; gap: 14px; }
.collapse-btn { color: #4a5f7c; }
.crumb { display: flex; align-items: center; gap: 8px; color: #8a9ab1; font-size: 12px; }
.crumb b { color: #20344f; font-size: 13px; }
.api-state { font-size: 12px; color: #52657f; display: flex; align-items: center; gap: 6px; }
.api-state i { width: 7px; height: 7px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,.12); }
.api-state i.ok { background: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,.12); }
.date { font-size: 12px; color: #7b8ba2; }
.content { min-height: calc(100vh - 68px); }
@media (max-width: 900px) { .sidebar { width: 68px; } .brand-text, .menu-label, .side-foot { display: none; } .main { margin-left: 68px; } .top-right .date, .top-right .api-state { display: none; } .topbar { padding-right: 12px; } .crumb span { display: none; } }
</style>
