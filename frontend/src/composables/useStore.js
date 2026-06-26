import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getStoreById } from '@/config/stores'

export function useStore() {
  const route = useRoute()

  const storeId = computed(() => route.meta.store || null)
  const store = computed(() => storeId.value ? getStoreById(storeId.value) : null)
  const storePath = computed(() => store.value?.path || '/')

  const storeRoute = (suffix = '') => {
    const base = storePath.value
    if (!suffix) return base
    return `${base}${suffix.startsWith('/') ? suffix : `/${suffix}`}`
  }

  return { storeId, store, storePath, storeRoute }
}
