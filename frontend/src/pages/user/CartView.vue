<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import TheHeader from '@/components/TheHeader.vue'
import TheFooter from '@/components/TheFooter.vue'
import { useCartStore } from '@/store/cart'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { getImageUrl } from '@/composables/useImageUrl'
import { useStore } from '@/composables/useStore'
import {
  getQuantityStep, getMinQuantity, isValidLengthQuantity, isPackageMode, isLengthMode, isOnRequest, formatQuantityLabel
} from '@/composables/useSellingMode'

// SEO Meta Tags
useHead({
  title: 'Korpa - BetaPack',
  meta: [
    { name: 'robots', content: 'noindex, nofollow' } // Cart pages should not be indexed
  ]
})

const showConfirm = ref(false)
const confirmMessage = ref("")
const confirmAction = ref(null)
const quantityErrors = ref({})

const openConfirm = (msg, action) => {
  confirmMessage.value = msg
  confirmAction.value = action
  showConfirm.value = true
}

const closeConfirm = () => {
  showConfirm.value = false
  confirmMessage.value = ""
  confirmAction.value = null
}

const confirm = () => {
  if (confirmAction.value) confirmAction.value()
  closeConfirm()
}


const router = useRouter()
const cartStore = useCartStore()
const { storeRoute } = useStore()

const formatPrice = (price) => {
  return new Intl.NumberFormat('sr-RS', {
    style: 'currency',
    currency: 'RSD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

const cartItems = computed(() => cartStore.items)
const cartTotal = computed(() => cartStore.total)
const cartCount = computed(() => cartStore.itemCount)

const updateQuantity = (item, newQuantity) => {
  const minQuantity = getMinQuantity(item)
  if (newQuantity < minQuantity) return

  if (isLengthMode(item) && !isValidLengthQuantity(newQuantity)) {
    const itemId = item.cartId || item.id
    quantityErrors.value[itemId] = 'Proizvod se prodaje ceo ili na pola (npr. 1, 1.5, 2, 2.5).'
    const whole = Math.floor(newQuantity)
    const decimal = newQuantity % 1
    newQuantity = decimal < 0.25 ? whole : (decimal < 0.75 ? whole + 0.5 : whole + 1)
    setTimeout(() => { quantityErrors.value[itemId] = null }, 3000)
  } else {
    quantityErrors.value[item.cartId || item.id] = null
  }

  cartStore.updateQuantity(item.cartId || item.id, newQuantity)
}

const removeItem = (item) => {
  openConfirm(
    `Ukloniti "${item.name}" iz korpe?"`,
    () => cartStore.remove(item.cartId || item.id)
  )
}

const clearCart = () => {
  openConfirm(
    "Da li želite da ispraznite korpu?",
    () => cartStore.clear()
  )
}


const goToCheckout = () => {
  router.push(storeRoute('/checkout'))
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <TheHeader />

    <main class="flex-1 py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <!-- Back Button -->
        <button
          @click="router.push(storeRoute())"
          class="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition cursor-pointer"
        >
          <span>←</span>
          <span>Nazad na prodavnicu</span>
        </button>

        <h1 class="text-2xl lg:text-3xl font-bold text-gray-900 mb-4">Korpa</h1>

        <!-- Empty Cart -->
        <div v-if="cartItems.length === 0" class="bg-white rounded-xl shadow-lg p-8 text-center">
          <span class="text-4xl text-gray-300 mb-4 block">🛒</span>
          <h2 class="text-xl lg:text-2xl font-bold text-gray-900 mb-2">Vaša korpa je prazna</h2>
          <p class="text-gray-600 mb-4 text-sm lg:text-base">Dodajte proizvode u korpu da biste nastavili</p>
          <button
            @click="router.push(storeRoute())"
            class="bg-[#1976d2] hover:bg-[#1565c0] text-white font-semibold px-4 py-2 rounded-lg transition cursor-pointer text-sm"
          >
            Pogledaj proizvode
          </button>
        </div>

        <!-- Cart Items -->
        <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-8">

          <!-- Items List -->
          <div class="lg:col-span-2 space-y-4">
            <div
              v-for="item in cartItems"
              :key="item.id"
              class="bg-white rounded-lg shadow p-3 flex gap-3"
            >
              <!-- Image -->
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

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-gray-900 text-sm mb-0.5">{{ item.name }}</h3>
                <p class="text-xs text-gray-600 mb-1">{{ item.category_name }}</p>
                <p v-if="item.selectedVariant" class="text-xs text-[#1565c0] font-semibold">
                  Dimenzija: {{ item.selectedVariant.name }}
                </p>
                <p class="text-sm font-bold text-green-700 mt-1">{{ formatPrice(item.current_price) }}</p>
              </div>

              <!-- Quantity & Actions -->
              <div class="flex flex-col items-end justify-between">
                <!-- Quantity -->
                <div v-if="!isOnRequest(item)" class="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                  <button
                    @click="updateQuantity(item, item.quantity - getQuantityStep(item))"
                    :disabled="item.quantity <= getMinQuantity(item)"
                    class="w-8 h-8 bg-white rounded text-gray-700 hover:bg-gray-200 hover:text-black font-bold transition disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed border border-gray-300 hover:border-gray-400"
                  >-</button>
                  <input
                    :value="item.quantity"
                    @input="updateQuantity(item, parseFloat($event.target.value) || getMinQuantity(item))"
                    @blur="updateQuantity(item, Math.max(getMinQuantity(item), parseFloat($event.target.value) || getMinQuantity(item)))"
                    type="number"
                    :min="getMinQuantity(item)"
                    :step="getQuantityStep(item)"
                    class="w-24 text-center font-semibold bg-white border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-[#1976d2] focus:outline-none"
                  />
                  <button
                    @click="updateQuantity(item, item.quantity + getQuantityStep(item))"
                    class="w-8 h-8 bg-white rounded text-gray-700 hover:bg-gray-200 hover:text-black font-bold transition cursor-pointer border border-gray-300 hover:border-gray-400"
                  >+</button>
                </div>
                <p v-else class="text-xs text-orange-600 font-semibold">Cena na upit</p>
                <p v-if="isLengthMode(item)" class="text-[10px] text-blue-600 font-semibold italic mt-1 text-right">
                  📏 {{ (parseFloat(item.quantity) * (item.length_per_unit || 6)).toFixed(2) }} metara
                </p>
                <p v-if="isPackageMode(item)" class="text-[10px] text-green-600 font-semibold italic mt-1 text-right">
                  📦 {{ formatQuantityLabel(item, item.quantity) }}
                </p>
                <p v-if="quantityErrors[item.cartId || item.id]" class="text-[10px] text-red-600 font-semibold italic mt-1 text-right">
                  ❌ {{ quantityErrors[item.cartId || item.id] }}
                </p>

                <!-- Subtotal -->
                <div class="text-right">
                  <p v-if="!isOnRequest(item)" class="text-base font-bold text-gray-900">
                    {{ formatPrice(item.current_price * item.quantity) }}
                  </p>
                  <p v-else class="text-sm font-semibold text-orange-600">Na upit</p>
                </div>

                <!-- Remove button below quantity controls -->
                <button
                  @click="removeItem(item)"
                  class="mt-2 text-red-600 hover:text-red-700 text-xs font-semibold cursor-pointer"
                >
                  Ukloni
                </button>
              </div>
            </div>

            <!-- Clear Cart -->
            <button
              @click="clearCart"
              class="text-red-600 hover:text-red-700 text-sm font-semibold cursor-pointer"
            >
              Isprazni korpu
            </button>
          </div>

          <!-- Order Summary -->
          <div class="lg:col-span-1">
            <div class="bg-white rounded-lg shadow-lg p-4 sticky top-20">
              <h2 class="text-lg font-bold text-gray-900 mb-4">Rezime</h2>

              <div class="space-y-2 mb-4">
                <div class="flex justify-between text-sm text-gray-600">
                  <span>Stavke ({{ cartCount }})</span>
                  <span>{{ formatPrice(cartTotal) }}</span>
                </div>
                <div class="flex justify-between text-sm text-gray-600">
                  <span>Dostava</span>
                  <span class="text-gray-400">Dogovor telefonom</span>
                </div>
              </div>

              <div class="border-t pt-3 mb-4">
                <div class="flex justify-between items-center">
                  <span class="text-base font-bold text-gray-900">Ukupno</span>
                  <span class="text-lg font-bold text-green-700">{{ formatPrice(cartTotal) }}</span>
                </div>
                <p class="text-xs text-gray-500 mt-1">Finalna cena se potvrđuje telefonom</p>
              </div>

              <button
                @click="goToCheckout"
                class="w-full bg-[#1976d2] hover:bg-[#1565c0] text-white font-bold py-2.5 rounded-lg transition mb-2 cursor-pointer text-sm"
              >
                Nastavi ka poručivanju
              </button>

              <button
                @click="router.push(storeRoute())"
                class="w-full bg-white hover:bg-gray-50 text-gray-900 font-semibold py-3 rounded-lg border-2 border-gray-300 transition"
              >
                Nastavi kupovinu
              </button>

              <!-- Info -->
              <div class="mt-6 pt-6 border-t">
                <h3 class="font-semibold text-gray-900 mb-3 text-sm">Potrebna pomoć?</h3>
                <a
                  href="tel:0653300242"
                  class="flex items-center gap-2 text-[#1565c0] hover:text-[#1565c0]"
                >
                  <span>📞</span>
                  <span class="font-semibold">065/330 02 42</span>
                </a>
              </div>
            </div>
          </div>

        </div>
          <ConfirmModal
            :show="showConfirm"
            title="Potvrda"
            :message="confirmMessage"
            confirmText="Da"
            cancelText="Odustani"
            @confirm="confirm"
            @cancel="closeConfirm"
          />
      </div>
    </main>

    <TheFooter />
  </div>
</template>
