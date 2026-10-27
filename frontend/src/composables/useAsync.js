import { onMounted, ref } from 'vue'
export function useAsync(loader) {
  const data = ref(null)
  const loading = ref(true)
  const error = ref('')
  async function load() {
    loading.value = true; error.value = ''
    try { data.value = await loader() }
    catch (e) { error.value = e.message || '加载失败' }
    finally { loading.value = false }
  }
  onMounted(load)
  return { data, loading, error, load }
}
