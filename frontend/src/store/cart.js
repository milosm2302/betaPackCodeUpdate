import { defineStore } from 'pinia'
import {
    getSellingMode, getPackageSize, getMinQuantity, isOnRequest
} from '@/composables/useSellingMode'

export const useCartStore = defineStore('cart', {
    state: () => {
        const savedCart = JSON.parse(localStorage.getItem('cart') || '[]')
        const validItems = savedCart.filter(item => {
            if (item.selling_mode === 'on_request') return true
            return item.current_price !== undefined && item.current_price !== null
        })
        if (validItems.length !== savedCart.length) {
            localStorage.setItem('cart', JSON.stringify(validItems))
        }
        return { items: validItems }
    },

    getters: {
        itemCount: (state) => state.items.length,

        total: (state) => {
            return state.items.reduce((sum, item) => {
                if (item.selling_mode === 'on_request') return sum
                const price = parseFloat(item.current_price) || 0
                return sum + (price * item.quantity)
            }, 0)
        },

        getItemPrice: (state) => (item) => {
            if (item.selectedVariant?.final_price) {
                return parseFloat(item.selectedVariant.final_price)
            }
            return parseFloat(item.current_price) || 0
        },

        isInCart: (state) => (productId, variantId = null) => {
            if (variantId) {
                const cartId = `${productId}-${variantId}`
                return state.items.some(i => i.cartId === cartId)
            }
            return state.items.some(i => i.id === productId)
        },

        getCartItem: (state) => (productId, variantId = null) => {
            if (variantId) {
                const cartId = `${productId}-${variantId}`
                return state.items.find(i => i.cartId === cartId)
            }
            return state.items.find(i => i.id === productId)
        },

        itemsForStore: (state) => (storeId) => {
            return state.items.filter(i => i.store === storeId)
        }
    },

    actions: {
        save() {
            localStorage.setItem('cart', JSON.stringify(this.items))
        },

        load() {
            const saved = localStorage.getItem('cart')
            if (saved) this.items = JSON.parse(saved)
        },

        add(product, quantity = 1) {
            const cartId = product.selectedVariant
                ? `${product.id}-${product.selectedVariant.id}`
                : product.id

            const found = this.items.find(i => i.cartId === cartId)
            const sellingMode = getSellingMode(product)

            let itemPrice = product.current_price
            if (product.selectedVariant?.final_price) {
                itemPrice = parseFloat(product.selectedVariant.final_price)
            } else {
                itemPrice = product.current_price != null ? parseFloat(product.current_price) : null
            }

            let lengthPerUnit = 6.0
            if (product.selectedVariant?.effective_length_per_unit) {
                lengthPerUnit = parseFloat(product.selectedVariant.effective_length_per_unit)
            } else if (product.selectedVariant?.length_per_unit) {
                lengthPerUnit = parseFloat(product.selectedVariant.length_per_unit)
            } else if (product.length_per_unit) {
                lengthPerUnit = parseFloat(product.length_per_unit)
            }

            const packageSize = getPackageSize(product)

            if (found) {
                found.quantity += quantity
                found.current_price = itemPrice
                found.sold_by_length = product.sold_by_length || sellingMode === 'length'
                found.selling_mode = sellingMode
                found.package_size = packageSize
                found.length_per_unit = lengthPerUnit
            } else {
                this.items.push({
                    cartId,
                    id: product.id,
                    store: product.store || 'steel',
                    name: product.name,
                    current_price: itemPrice,
                    images: product.images || [],
                    category_name: product.category_name,
                    selectedVariant: product.selectedVariant || null,
                    sold_by_length: product.sold_by_length || sellingMode === 'length',
                    selling_mode: sellingMode,
                    package_size: packageSize,
                    length_per_unit: lengthPerUnit,
                    dimensions: product.dimensions || '',
                    quantity
                })
            }

            this.save()
        },

        updateQuantity(itemId, newQuantity) {
            const item = this.items.find(i => i.cartId === itemId || i.id === itemId)
            if (!item) return

            const minQuantity = getMinQuantity(item)
            if (newQuantity >= minQuantity) {
                item.quantity = newQuantity
                this.save()
            }
        },

        remove(itemId) {
            this.items = this.items.filter(i => i.cartId !== itemId && i.id !== itemId)
            this.save()
        },

        clear() {
            this.items = []
            this.save()
        },

        clearStore(storeId) {
            this.items = this.items.filter(i => i.store !== storeId)
            this.save()
        }
    }
})
