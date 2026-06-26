<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '@/store/cart'
import { useAuthStore } from '@/store/auth'
import { getImageUrl } from '@/composables/useImageUrl'
import { useStore } from '@/composables/useStore'
import { STORE_LIST } from '@/config/stores'
import {
  getQuantityStep, getMinQuantity, isPackageMode, isLengthMode, isOnRequest
} from '@/composables/useSellingMode'

const router = useRouter()
const cartStore = useCartStore()
const authStore = useAuthStore()
const { store, storeRoute, storeId } = useStore()

const mobileMenuOpen = ref(false)
const showCartPreview = ref(false)

const cartItemCount = computed(() => cartStore.itemCount)
const cartItems = computed(() => cartStore.items)
const cartTotal = computed(() => cartStore.total)
const isAdmin = computed(() => authStore.isAdmin)

const formatPrice = (price) => {
  if (price == null) return 'Na upit'
  return new Intl.NumberFormat('sr-RS', {
    style: 'currency',
    currency: 'RSD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

const navigateTo = (route) => {
  router.push(route)
  mobileMenuOpen.value = false
  showCartPreview.value = false
}

const updateQuantity = (item, newQuantity) => {
  const min = getMinQuantity(item)
  if (newQuantity < min) return
  cartStore.updateQuantity(item.cartId || item.id, newQuantity)
}

const removeItem = (item) => {
  cartStore.remove(item.cartId || item.id)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <header class="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white sticky top-0 z-50 shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16 lg:h-18">

        <div class="flex items-center gap-3 lg:gap-4 cursor-pointer" @click="navigateTo('/')">
          <img src="/betapack-logo.png" alt="Beta Pack Logo" class="h-10 lg:h-12 w-auto" />
          <div>
            <div class="text-base lg:text-lg font-bold text-white">BETA PACK</div>
            <div v-if="store" class="text-[10px] text-gray-400 font-medium hidden sm:block">{{ store.shortLabel }}</div>
          </div>
        </div>

        <nav class="hidden md:flex items-center gap-2 lg:gap-3">
          <!-- Store switcher -->
          <div class="flex items-center gap-1 bg-white/5 rounded-xl p-1 border border-white/10">
            <button
              v-for="s in STORE_LIST"
              :key="s.id"
              @click="navigateTo(s.path)"
              :class="storeId === s.id ? 'bg-[#1976d2] text-white shadow' : 'text-gray-300 hover:text-white hover:bg-white/10'"
              class="flex items-center gap-1 px-3 lg:px-4 py-1.5 rounded-lg transition font-semibold text-sm cursor-pointer"
            >
              <span>{{ s.icon }}</span>
              <span>{{ s.shortLabel }}</span>
            </button>
          </div>

          <template v-if="store">
            <button
              @click="navigateTo(storeRoute('/o-nama'))"
              class="text-gray-300 hover:text-white hover:bg-white/10 px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg transition font-semibold text-sm lg:text-base cursor-pointer"
            >
              O nama
            </button>
            <button
              @click="navigateTo(storeRoute('/kontakt'))"
              class="text-gray-300 hover:text-white hover:bg-white/10 px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg transition font-semibold text-sm lg:text-base cursor-pointer"
            >
              Kontakt
            </button>
          </template>
        </nav>

        <div class="flex items-center gap-4">
          <button
            v-if="isAdmin"
            @click="navigateTo('/admin')"
            class="hidden md:flex items-center gap-1 bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded-lg transition font-semibold text-xs cursor-pointer border border-gray-600 hover:border-gray-500"
          >
            <span class="text-sm">⚙️</span>
            <span>Admin</span>
          </button>

          <button
            v-if="authStore.isAuthenticated"
            @click="handleLogout"
            class="hidden md:flex items-center gap-1 bg-red-600 hover:bg-red-700 px-2 py-1 rounded-lg transition font-semibold text-xs cursor-pointer"
          >
            <span class="text-sm">🚪</span>
            <span>Logout</span>
          </button>

          <div v-if="store" class="relative group">
            <button
              @click="navigateTo(storeRoute('/cart'))"
              class="relative flex items-center gap-1 bg-[#1976d2] hover:bg-[#1565c0] px-2 py-1 rounded-lg transition font-semibold text-xs cursor-pointer"
            >
              <span class="text-lg">🛒</span>
              <span class="hidden sm:inline">Korpa</span>
              <span
                v-if="cartItemCount > 0"
                class="absolute -top-1.5 -right-1.5 bg-red-600 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center"
              >
                {{ cartItemCount }}
              </span>
            </button>

            <div
              v-if="cartItems.length > 0"
              class="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 absolute right-0 top-full pt-2 w-96 z-[100]"
            >
              <div class="bg-white rounded-xl shadow-2xl border border-gray-200 max-h-[600px] overflow-hidden flex flex-col">
                <div class="p-4 border-b bg-gray-50">
                  <h3 class="font-bold text-lg text-gray-900">Korpa ({{ cartItemCount }})</h3>
                </div>
                <div class="flex-1 overflow-y-auto p-4 space-y-3">
                  <div
                    v-for="item in cartItems"
                    :key="item.cartId || item.id"
                    class="flex gap-3 pb-3 border-b last:border-0"
                  >
                    <div class="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                      <img
                        v-if="item.images && item.images.length > 0"
                        :src="getImageUrl(item.images[0].image)"
                        :alt="item.name"
                        class="w-full h-full object-contain"
                      />
                      <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                        <span class="text-2xl">📦</span>
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h4 class="font-semibold text-sm text-gray-900 line-clamp-1">{{ item.name }}</h4>
                      <p v-if="item.selectedVariant" class="text-xs text-gray-600">{{ item.selectedVariant.name }}</p>
                      <p class="text-sm font-bold text-green-700 mt-1">{{ formatPrice(item.current_price) }}</p>
                      <div v-if="!isOnRequest(item)" class="flex items-center gap-2 mt-2">
                        <button
                          @click.stop="updateQuantity(item, item.quantity - getQuantityStep(item))"
                          class="w-6 h-6 bg-gray-200 hover:bg-gray-300 rounded text-xs font-semibold text-gray-900 cursor-pointer"
                        >-</button>
                        <span class="text-sm font-semibold text-gray-900 w-6 text-center">{{ item.quantity }}</span>
                        <button
                          @click.stop="updateQuantity(item, item.quantity + getQuantityStep(item))"
                          class="w-6 h-6 bg-gray-200 hover:bg-gray-300 rounded text-xs font-semibold text-gray-900 cursor-pointer"
                        >+</button>
                        <button
                          @click.stop="removeItem(item)"
                          class="ml-auto text-red-600 hover:text-red-700 text-xs font-semibold cursor-pointer"
                        >Ukloni</button>
                      </div>
                      <p v-if="isPackageMode(item)" class="text-[10px] text-green-600 mt-1">
                        {{ item.quantity / (item.package_size || 1) }} pak. ({{ item.quantity }} kom.)
                      </p>
                    </div>
                  </div>
                </div>
                <div class="p-4 border-t bg-gray-50 space-y-3">
                  <div class="flex justify-between items-center">
                    <span class="font-bold text-gray-900">Ukupno:</span>
                    <span class="text-xl font-bold text-green-700">{{ formatPrice(cartTotal) }}</span>
                  </div>
                  <button
                    @click="navigateTo(storeRoute('/cart'))"
                    class="w-full bg-[#1976d2] hover:bg-[#1565c0] text-white font-semibold py-2.5 rounded-lg transition cursor-pointer"
                  >
                    Pogledaj korpu
                  </button>
                </div>
              </div>
            </div>
          </div>

          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="md:hidden text-gray-300 hover:text-white p-2 cursor-pointer"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="mobileMenuOpen" class="md:hidden bg-gray-800 border-t border-gray-700">
      <nav class="px-4 py-4 space-y-2">
        <p class="text-[10px] uppercase tracking-wider text-gray-500 font-bold px-4 pt-1">Prodavnica</p>
        <button
          v-for="s in STORE_LIST"
          :key="s.id"
          @click="navigateTo(s.path)"
          :class="storeId === s.id ? 'bg-[#1976d2] text-white' : 'text-gray-300 hover:text-white hover:bg-white/10'"
          class="flex items-center gap-2 w-full text-left px-4 py-3 rounded-lg transition font-semibold text-base cursor-pointer"
        >
          <span>{{ s.icon }}</span>
          <span>{{ s.label }}</span>
        </button>
        <template v-if="store">
          <button @click="navigateTo(storeRoute('/o-nama'))" class="block w-full text-left text-gray-300 hover:text-white hover:bg-white/10 px-4 py-3 rounded-lg transition font-semibold text-base cursor-pointer">O nama</button>
          <button @click="navigateTo(storeRoute('/kontakt'))" class="block w-full text-left text-gray-300 hover:text-white hover:bg-white/10 px-4 py-3 rounded-lg transition font-semibold text-base cursor-pointer">Kontakt</button>
          <button @click="navigateTo(storeRoute('/cart'))" class="block w-full text-left text-gray-300 hover:text-white hover:bg-white/10 px-4 py-3 rounded-lg transition font-semibold text-base cursor-pointer">🛒 Korpa</button>
        </template>
        <button v-if="isAdmin" @click="navigateTo('/admin')" class="block w-full text-left text-gray-300 hover:text-white hover:bg-white/10 px-4 py-3 rounded-lg transition font-semibold text-base cursor-pointer border-t border-gray-700 mt-2">⚙️ Admin Panel</button>
        <button v-if="authStore.isAuthenticated" @click="handleLogout" class="block w-full text-left text-red-400 hover:text-white hover:bg-red-600/20 px-4 py-3 rounded-lg transition font-semibold text-base cursor-pointer border-t border-gray-700">🚪 Logout</button>
      </nav>
    </div>
  </header>
</template>
