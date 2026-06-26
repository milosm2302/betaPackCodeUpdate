import { defineStore } from 'pinia'
import { api } from '../../services/api'
import { useAuthStore } from '../../store/auth'

export const useAdminStatsStore = defineStore('adminStats', {
    state: () => ({
        categories: 0,
        subcategories: 0,
        products: 0,
        orders: 0,
        contactMessages: 0,
        currentStore: 'steel',
    }),

    actions: {
        async refresh(store = 'steel') {
            this.currentStore = store
            const auth = useAuthStore()

            if (!auth.isAuthenticated || !auth.accessToken) {
                console.warn("Korisnik nije autentifikovan, preskačem osvežavanje brojača")
                return
            }

            const catalogParams = { store }
            const authHeaders = { Authorization: `Bearer ${auth.accessToken}` }

            try {
                const [cats, subs, prods, ords, msgs] = await Promise.all([
                    api.get('/categories/', { params: catalogParams }),
                    api.get('/subcategories/', { params: catalogParams }),
                    api.get('/products/', { params: catalogParams }),
                    api.get('/orders/', { headers: authHeaders }),
                    api.get('/contact-messages/', { headers: authHeaders }),
                ])

                this.categories = cats.data.length
                this.subcategories = subs.data.length
                this.products = prods.data.length
                this.orders = ords.data.length
                this.contactMessages = msgs.data.length
            } catch (e) {
                console.error("Greška pri učitavanju brojača:", e)
                if (e.response?.status === 401) {
                    const refreshed = await auth.refreshToken()
                    if (refreshed) await this.refresh(store)
                }
            }
        }
    }
})
