import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/auth'

export const useProductStore = defineStore('adminProducts', {
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
                const res = await api.get('products/', { params })
                this.list = res.data
            } catch (e) {
                console.error('Greška fetch proizvoda:', e)
            } finally {
                this.loading = false
            }
        },

        async create(payload) {
            const auth = useAuthStore()

            await api.post(
                'products/',
                payload,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

        async update(id, payload) {
            const auth = useAuthStore()

            await api.put(
                `products/${id}/`,
                payload,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

        async remove(id) {
            const auth = useAuthStore()

            await api.delete(
                `products/${id}/`,
                { headers: { Authorization: `Bearer ${auth.accessToken}` } }
            )

            await this.fetch()
        },

    }
})
