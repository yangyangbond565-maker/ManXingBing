<template>
  <section class="panel">
    <div class="panel-head">
      <div><div class="panel-title">{{ title }}</div><div v-if="subtitle" class="panel-sub">{{ subtitle }}</div></div>
      <slot name="actions" />
    </div>
    <div class="panel-body"><slot /></div>
  </section>
</template>
<script setup>defineProps({ title: String, subtitle: String })</script>
