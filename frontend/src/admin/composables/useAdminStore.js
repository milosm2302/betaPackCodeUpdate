import { ref } from 'vue'
import { STORES } from '@/config/stores'

export function useAdminStore() {
    const activeStore = ref('steel')

    const setStore = (storeId) => {
        activeStore.value = storeId
    }

    const storeTabs = [
        { id: 'steel', label: STORES.steel.label, icon: '🔩' },
        { id: 'ambalaza', label: STORES.ambalaza.label, icon: '📦' },
    ]

    return { activeStore, setStore, storeTabs }
}
