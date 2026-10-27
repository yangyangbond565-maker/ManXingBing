<template>
  <div class="stat">
    <div class="stat-top">
      <span class="stat-label">{{ label }}</span>
      <span class="stat-icon" :style="{ background: tint }"><el-icon :size="18"><component :is="icon" /></el-icon></span>
    </div>
    <div class="stat-value">{{ display }}<small v-if="unit">{{ unit }}</small></div>
    <div class="stat-foot"><span class="dot" :style="{ background: color }"></span>{{ hint }}</div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ label: String, value: [Number, String], unit: String, hint: String, icon: { type: String, default: 'DataLine' }, color: { type: String, default: '#2563eb' }, tint: { type: String, default: 'rgba(37,99,235,.1)' } })
const display = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return '—'
  if (typeof props.value === 'number') return props.value.toLocaleString('zh-CN')
  return props.value
})
</script>
<style scoped>
.stat { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 18px 18px 14px; box-shadow: var(--shadow); }
.stat-top { display: flex; justify-content: space-between; align-items: center; }
.stat-label { color: var(--muted); font-size: 13px; }
.stat-icon { width: 34px; height: 34px; border-radius: 9px; display: grid; place-items: center; color: var(--blue); }
.stat-value { margin-top: 12px; font-size: 30px; font-weight: 800; letter-spacing: .4px; color: #0f2a4d; }
.stat-value small { margin-left: 4px; font-size: 13px; font-weight: 500; color: var(--muted); }
.stat-foot { margin-top: 8px; color: var(--muted); font-size: 12px; display: flex; align-items: center; }
.dot { width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; }
</style>
