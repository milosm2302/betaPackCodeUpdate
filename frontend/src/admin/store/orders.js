import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/auth'

export const useOrderStore = defineStore('orders', {
    state: () => ({
        list: [],
        selected: null,
        loading: false,
        error: null
    }),

    actions: {
        async fetchAll(store = null) {
            this.loading = true
            const auth = useAuthStore()
            const params = store ? { store } : {}

            try {
                const response = await api.get(
                    'orders/',
                    { params, headers: { Authorization: `Bearer ${auth.accessToken}` } }
                )
                this.list = response.data
            } finally {
                this.loading = false
            }
        },

        selectOrder(order) {
            this.selected = order
        },

        clearSelected() {
            this.selected = null
        },

        async updateStatus(id, newStatus) {
            const auth = useAuthStore()

            try {
                await api.post(
                    `orders/${id}/update_status/`,
                    { status: newStatus },
                    {
                        headers: { Authorization: `Bearer ${auth.accessToken}` }
                    }
                )

                // refresh table
                await this.fetchAll()

                // update modal instantly
                if (this.selected && this.selected.id === id) {
                    this.selected.status = newStatus
                }

            } catch (e) {
                console.error('Greška pri ažuriranju statusa:', e)
            }
        },

        async deleteOrder(id) {
            const auth = useAuthStore()

            try {
                await api.delete(
                    `orders/${id}/`,
                    {
                        headers: { Authorization: `Bearer ${auth.accessToken}` }
                    }
                )

                // refresh table
                await this.fetchAll()

                // clear selected if deleted
                if (this.selected && this.selected.id === id) {
                    this.clearSelected()
                }

            } catch (e) {
                console.error('Greška pri brisanju narudžbine:', e)
                throw e
            }
        }
    }
})
