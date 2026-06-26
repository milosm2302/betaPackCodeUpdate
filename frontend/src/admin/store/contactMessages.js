import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/auth'

export const useContactMessagesStore = defineStore('contactMessages', {
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
                    'contact-messages/',
                    { params, headers: { Authorization: `Bearer ${auth.accessToken}` } }
                )
                this.list = response.data
                this.error = null
            } catch (e) {
                console.error('Error fetching contact messages:', e)
                this.error = e
            } finally {
                this.loading = false
            }
        },

        selectMessage(message) {
            this.selected = message
        },

        clearSelected() {
            this.selected = null
        },

        async markAsRead(id) {
            const auth = useAuthStore()

            try {
                await api.patch(
                    `contact-messages/${id}/`,
                    { is_read: true },
                    {
                        headers: { Authorization: `Bearer ${auth.accessToken}` }
                    }
                )

                // Update in list
                const msg = this.list.find(m => m.id === id)
                if (msg) {
                    msg.is_read = true
                }

                // Update selected if it's the same message
                if (this.selected && this.selected.id === id) {
                    this.selected.is_read = true
                }

                // Refresh to ensure sync
                await this.fetchAll()

            } catch (e) {
                console.error('Error marking message as read:', e)
                throw e
            }
        },

        async markAsReplied(id) {
            const auth = useAuthStore()

            try {
                await api.patch(
                    `contact-messages/${id}/`,
                    { is_replied: true },
                    {
                        headers: { Authorization: `Bearer ${auth.accessToken}` }
                    }
                )

                // Update in list
                const msg = this.list.find(m => m.id === id)
                if (msg) {
                    msg.is_replied = true
                }

                // Update selected if it's the same message
                if (this.selected && this.selected.id === id) {
                    this.selected.is_replied = true
                }

                // Refresh to ensure sync
                await this.fetchAll()

            } catch (e) {
                console.error('Error marking message as replied:', e)
                throw e
            }
        },

        async deleteMessage(id) {
            const auth = useAuthStore()

            try {
                await api.delete(
                    `contact-messages/${id}/`,
                    {
                        headers: { Authorization: `Bearer ${auth.accessToken}` }
                    }
                )

                // Refresh table
                await this.fetchAll()

                // Clear selected if deleted
                if (this.selected && this.selected.id === id) {
                    this.clearSelected()
                }

            } catch (e) {
                console.error('Error deleting contact message:', e)
                throw e
            }
        }
    },

    getters: {
        unreadCount: (state) => {
            return state.list.filter(m => !m.is_read).length
        }
    }
})







