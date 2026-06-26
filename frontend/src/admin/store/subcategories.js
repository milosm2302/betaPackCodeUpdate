import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/auth'

export const useSubcategoryStore = defineStore('adminSubcategories', {
    state: () => ({
        list: [],
        loading: false,
        error: null,
        currentStore: null
    }),

    actions: {
        async fetch(store = null) {
            this.loading = true
            if (store !== null) this.currentStore = store
            try {
                const activeStore = store !== null ? store : this.currentStore
                const params = activeStore ? { store: activeStore } : {}
                const res = await api.get('subcategories/', { params })
                this.list = res.data
            } catch (e) {
                console.error('Greška fetch subcategories:', e)
                this.error = 'Ne mogu da učitam podkategorije'
            } finally {
                this.loading = false
            }
        },

        async create(payload) {
            const auth = useAuthStore()

            await api.post(
                'subcategories/',
                payload,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

        async update(id, payload) {
            const auth = useAuthStore()

            await api.put(
                `subcategories/${id}/`,
                payload,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

        async remove(id) {
            const auth = useAuthStore()

            await api.delete(
                `subcategories/${id}/`,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        }
    }
})
