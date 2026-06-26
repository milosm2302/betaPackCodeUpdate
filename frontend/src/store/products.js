import { defineStore} from 'pinia'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const useProductStore = defineStore('products', {
    state: () => ({
        products: [],
        loading: false,
        currentStore: 'steel'
    }),

    getters: {
        filteredProducts: (state) => (filters) => {
            let res = state.products.filter(p => p.store === state.currentStore || !p.store)

            if (filters.category) {
                res = res.filter(p => p.category === filters.category)
            }

            if (filters.search) {
                const q = filters.search.toLowerCase()
                res = res.filter(p =>
                    p.name.toLowerCase().includes(q) ||
                    p.description.toLowerCase().includes(q) ||
                    p.category_name.toLowerCase().includes(q)
                )
            }

            if (filters.minPrice) {
                res = res.filter(p => parseFloat(p.current_price) >= filters.minPrice)
            }
            if (filters.maxPrice) {
                res = res.filter(p => parseFloat(p.current_price) <= filters.maxPrice)
            }

            if (filters.showOnlyOnSale) {
                res = res.filter(p => p.on_sale)
            }

            return res
        }
    },

    actions: {
        async fetchProducts(store = 'steel') {
            this.loading = true
            this.currentStore = store
            try {
                const r = await axios.get(`${API_URL}/products/`, { params: { store } })
                this.products = r.data
            } finally {
                this.loading = false
            }
        }
    }
})
