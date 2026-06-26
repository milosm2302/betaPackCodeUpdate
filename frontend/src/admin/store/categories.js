import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/auth'

export const useCategoryStore = defineStore('adminCategories', {
    state: () => ({
        list: [],
        loading: false,
        error: null,
        currentStore: null,
    }),

    actions: {

        async fetch(store = null) {
            this.loading = true
            if (store !== null) this.currentStore = store
            try {
                const activeStore = store !== null ? store : this.currentStore
                const params = activeStore ? { store: activeStore } : {}
                const res = await api.get('categories/', { params })
                this.list = res.data
            } catch (e) {
                console.error('Greška fetch kategorija:', e)
            } finally {
                this.loading = false
            }
        },

        async create(payload) {
            const auth = useAuthStore()

            await api.post(
                'categories/',
                payload,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

        async update(id, payload) {
            const auth = useAuthStore()

            await api.put(
                `categories/${id}/`,
                payload,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

        async remove(id) {
            const auth = useAuthStore()

            await api.delete(
                `categories/${id}/`,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        }
    }
})
