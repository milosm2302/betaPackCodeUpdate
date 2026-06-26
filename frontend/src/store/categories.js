import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const useCategoryStore = defineStore('categories', {
    state: () => ({
        categories: [],
        currentStore: 'steel'
    }),

    actions: {
        async fetchCategories(store = 'steel') {
            this.currentStore = store
            try {
                const r = await axios.get(`${API_URL}/categories/`, { params: { store } })
                this.categories = r.data
            } catch (e) {
                console.error('Greška kategorije:', e)
            }
        },

        countForCategory(id, products) {
            return products.filter(p => p.category === id).length
        }
    }
})
