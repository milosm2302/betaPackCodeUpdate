<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useOrderStore } from '../store/orders'
import { useAuthStore } from '@/store/auth'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { api } from '@/services/api'
import { getStoreById } from '@/config/stores'

const emit = defineEmits(['update-count'])
const orderStore = useOrderStore()

// Status boje i nazivi ostaju u komponenti
const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  processing: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800'
}

const statusLabels = {
  pending: 'Na čekanju',
  confirmed: 'Potvrđena',
  processing: 'U obradi',
  completed: 'Završena',
  cancelled: 'Otkazana'
}

// Tabovi za filtriranje
const activeTab = ref('all')
const showFilterDropdown = ref(false)
const tabs = [
  { id: 'all', label: 'Sve', count: null, icon: '📋', color: 'bg-gray-600 hover:bg-gray-700' },
  { id: 'pending', label: 'Na čekanju', count: null, icon: '⏳', color: 'bg-yellow-500 hover:bg-yellow-600' },
  { id: 'confirmed', label: 'Potvrđena', count: null, icon: '✅', color: 'bg-[#1976d2] hover:bg-[#1565c0]' },
  { id: 'processing', label: 'U obradi', count: null, icon: '⚙️', color: 'bg-purple-700 hover:bg-purple-800' },
  { id: 'completed', label: 'Završena', count: null, icon: '🎉', color: 'bg-green-500 hover:bg-green-600' },
  { id: 'cancelled', label: 'Otkazana', count: null, icon: '❌', color: 'bg-red-500 hover:bg-red-600' }
]

// Funkcija za promenu taba
const selectTab = (tabId) => {
  activeTab.value = tabId
  showFilterDropdown.value = false
}

// Funkcija za dobijanje aktivnog taba
const getActiveTab = () => {
  return tabs.find(tab => tab.id === activeTab.value) || tabs[0]
}

// Filtrirane porudžbine
const filteredOrders = computed(() => {
  if (activeTab.value === 'all') {
    return orderStore.list
  }
  return orderStore.list.filter(order => order.status === activeTab.value)
})

// Ažuriraj brojeve u tabovima
const updateTabCounts = () => {
  tabs.forEach(tab => {
    if (tab.id === 'all') {
      tab.count = orderStore.list.length
    } else {
      tab.count = orderStore.list.filter(order => order.status === tab.id).length
    }
  })
}

const showDetailModal = ref(false)
const showConfirmDelete = ref(false)

const openDetailModal = (order) => {
  orderStore.selectOrder(order)
  showDetailModal.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  orderStore.clearSelected()
}

const deleteOrder = () => {
  showConfirmDelete.value = true
}

const confirmDelete = async () => {
  if (orderStore.selected) {
    try {
      await orderStore.deleteOrder(orderStore.selected.id)
      closeDetailModal()
      await refreshOrders()
    } catch (error) {
      console.error('Error deleting order:', error)
      alert('Greška pri brisanju narudžbine')
    }
  }
  showConfirmDelete.value = false
}

const cancelDelete = () => {
  showConfirmDelete.value = false
}

// format funkcije ostaju ovde
const formatPrice = (price) =>
  new Intl.NumberFormat('sr-RS', { style: 'currency', currency: 'RSD' }).format(price)

const formatDate = (dateString) =>
  new Date(dateString).toLocaleString('sr-RS')

// Label za prodavnicu/e iz kojih je narudžbina (mešovite narudžbine spaja sa +)
const getOrderStores = (order) => {
  const ids = (order.stores && order.stores.length) ? order.stores : (order.store ? [order.store] : [])
  return ids.map(id => getStoreById(id))
}

const orderStoreLabel = (order) =>
  getOrderStores(order).map(s => s.shortLabel).join(' + ')

const orderStoreIcons = (order) =>
  getOrderStores(order).map(s => s.icon).join(' ')

const isMixedOrder = (order) => (order.stores && order.stores.length > 1)

// Watch za promene u listi porudžbina - samo ažuriraj tabove, ne emituj event
watch(() => orderStore.list, () => {
  updateTabCounts()
}, { deep: true })

// Funkcija za osvežavanje
const refreshOrders = async () => {
  await orderStore.fetchAll()
  updateTabCounts()
  emit('update-count')
}

// Server-Sent Events za real-time notifikacije
let eventSource = null

// Funkcija za zatvaranje dropdown-a pri kliku van njega
const handleClickOutside = (event) => {
  const filterDropdown = event.target.closest('.filter-dropdown-container')
  if (!filterDropdown && showFilterDropdown.value) {
    showFilterDropdown.value = false
  }
}

// onMounted → fetch i osveži brojač, pokreni SSE
onMounted(async () => {
  await refreshOrders()
  startSSE()
  
  // Osveži kada se tab vrati u fokus
  if (typeof window !== 'undefined') {
    document.addEventListener('visibilitychange', async () => {
      if (document.visibilityState === 'visible' && !orderStore.loading) {
        await refreshOrders()
        // Restartuj SSE ako je zatvoren
        if (!eventSource || eventSource.readyState === EventSource.CLOSED) {
          startSSE()
        }
      }
    })
    
    // Dodaj event listener za zatvaranje dropdown-a
    document.addEventListener('click', handleClickOutside)
  }
})

// onUnmounted → zatvori SSE
onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  
  // Ukloni event listener za zatvaranje dropdown-a
  if (typeof window !== 'undefined') {
    document.removeEventListener('click', handleClickOutside)
  }
})

// SSE funkcija za real-time notifikacije
const startSSE = () => {
  const authStore = useAuthStore()
  
  if (!authStore.accessToken) {
    return
  }
  
  // Zatvori postojeći SSE ako postoji
  if (eventSource) {
    eventSource.close()
  }

  // Kreiraj SSE konekciju sa tokenom u query parametru
  const baseURL = api.defaults.baseURL || 'http://127.0.0.1:8000/api'
  
  eventSource = new EventSource(`${baseURL}/orders/notifications/?token=${authStore.accessToken}`)
  
  eventSource.onmessage = async (event) => {
    try {
      // Heartbeat poruke se ignorišu
      if (event.data.startsWith(':')) {
        return
      }
      
      const data = JSON.parse(event.data)
      
      if (data.type === 'new_order') {
        // Nova porudžbina - osveži listu
        await refreshOrders()
      } else if (data.type === 'init') {
        // Inicijalizacija - proveri da li ima novih ordera
        if (data.count > orderStore.list.length) {
          await refreshOrders()
        }
      }
    } catch (e) {
      // Ignoriši parse greške za heartbeat
      if (!event.data.startsWith(':')) {
        console.error('SSE parse error:', e)
      }
    }
  }
  
  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error)
    // Pokušaj ponovo nakon 5 sekundi
    setTimeout(() => {
      if (eventSource && eventSource.readyState === EventSource.CLOSED) {
        startSSE()
      }
    }, 5000)
  }
}
</script>


<template>
  <div>

    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-4 mb-4 pt-4">
      <div class="flex-1">
        <h2 class="text-xs lg:text-sm font-bold text-gray-900 mb-1 flex items-center gap-1">🛒 Narudžbine</h2>
        <p class="text-xs text-gray-500 font-medium">Upravljajte narudžbinama</p>
      </div>

      <button
        @click="refreshOrders"
        class="px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-lg text-xs font-semibold shadow-md hover:shadow-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap"
      >
        <span class="text-sm">🔄</span>
        <span>Osveži</span>
      </button>
    </div>

    <!-- Filter Dropdown (Mobile Only) -->
    <div class="mb-4 relative filter-dropdown-container block md:hidden z-10">
      <div class="bg-white rounded-lg shadow-md border border-gray-200">
        <!-- Active Tab Button -->
        <button
          @click.stop="showFilterDropdown = !showFilterDropdown"
          :class="getActiveTab().color"
          class="w-full px-4 py-3 text-white shadow-md transition-all duration-300 cursor-pointer flex items-center justify-between rounded-lg font-bold text-xs"
        >
          <div class="flex items-center gap-2">
            <span class="text-sm">{{ getActiveTab().icon }}</span>
            <span class="font-semibold">
              {{ activeTab === 'all' ? 'Sve narudžbine' : getActiveTab().label }}
            </span>
            <span 
              v-if="getActiveTab().count !== null"
              class="bg-white/30 text-white border border-white/50 px-1.5 py-0.5 rounded-full text-xs font-bold min-w-[20px] flex items-center justify-center"
            >
              {{ getActiveTab().count }}
            </span>
          </div>
          <span class="text-sm transition-transform duration-300" :class="{ 'rotate-180': showFilterDropdown }">▼</span>
        </button>

        <!-- Dropdown Options -->
        <div
          v-if="showFilterDropdown"
          class="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 z-[100] max-h-[400px] overflow-y-auto"
        >
          <div class="py-1">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="selectTab(tab.id)"
              :class="activeTab === tab.id
                ? `${tab.color} text-white`
                : 'bg-white text-gray-700 hover:bg-gray-100'"
              class="w-full px-4 py-2.5 font-bold text-xs transition-all duration-200 cursor-pointer flex items-center justify-between border-b border-gray-100 last:border-b-0"
            >
              <div class="flex items-center gap-2">
                <span class="text-sm">{{ tab.icon }}</span>
                <span class="font-semibold">{{ tab.label }}</span>
              </div>
              <span 
                v-if="tab.count !== null"
                :class="activeTab === tab.id 
                  ? 'bg-white/30 text-white border-white/50' 
                  : 'bg-gray-200 text-gray-700 border-gray-300'"
                class="px-1.5 py-0.5 rounded-full text-xs font-bold border min-w-[20px] flex items-center justify-center"
              >
                {{ tab.count }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs (Tablet & Desktop Only) -->
    <div class="mb-4 bg-white rounded-lg p-2 shadow-md border border-gray-200 overflow-x-auto hidden md:block">
      <div class="flex gap-1.5 min-w-max">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="activeTab === tab.id
            ? `${tab.color} text-white shadow-md scale-[1.01]`
            : 'bg-gray-50 text-gray-700 hover:bg-gray-100 hover:shadow-sm'"
          class="px-3 py-2 font-bold text-xs transition-all duration-300 cursor-pointer whitespace-nowrap flex items-center gap-1.5 rounded-lg border min-w-[100px] justify-center"
          :style="activeTab === tab.id ? { borderColor: 'transparent' } : { borderColor: '#e5e7eb' }"
        >
          <span class="text-sm">{{ tab.icon }}</span>
          <span class="font-semibold">{{ tab.label }}</span>
          <span 
            v-if="tab.count !== null"
            :class="activeTab === tab.id 
              ? 'bg-white/30 text-white border-white/50' 
              : 'bg-white text-gray-700 border-gray-300'"
            class="px-1.5 py-0.5 rounded-full text-xs font-bold border min-w-[20px] flex items-center justify-center"
          >
            {{ tab.count }}
          </span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="orderStore.loading" class="text-center py-8 text-gray-600 text-sm">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#1976d2] mb-2"></div>
      <p>Učitavanje narudžbina...</p>
    </div>

    <!-- Orders LIST -->
    <div v-else-if="filteredOrders.length > 0" class="space-y-2">
      <TransitionGroup name="order-list">
        <div
          v-for="order in filteredOrders"
          :key="order.id"
          class="bg-white rounded-lg shadow-md border border-gray-200 p-3 hover:shadow-lg hover:border-blue-300 transition-all duration-300 cursor-pointer transform hover:scale-[1.01] group"
          @click="openDetailModal(order)"
        >
          <div class="flex flex-col sm:flex-row justify-between items-start gap-2 sm:gap-3">

            <!-- Left Section -->
            <div class="flex-1 w-full sm:w-auto">
              <!-- Order ID and Date -->
              <div class="flex items-center gap-2 mb-2 flex-wrap">
                <div class="bg-[#1976d2] text-white rounded-lg px-2 py-1 shadow-md">
                  <span class="text-xs font-bold opacity-90">#</span>
                  <span class="text-sm font-bold">{{ order.id }}</span>
                </div>
                <div class="flex items-center gap-1.5 text-gray-500">
                  <span class="text-sm">📅</span>
                  <p class="text-xs font-medium">{{ formatDate(order.created_at) }}</p>
                </div>
                <span
                  v-if="getOrderStores(order).length"
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                  :class="isMixedOrder(order) ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'"
                >
                  {{ orderStoreIcons(order) }} {{ orderStoreLabel(order) }}
                </span>
              </div>

              <!-- Customer Info -->
              <div class="space-y-1 mb-2">
                <div class="flex items-center gap-1.5">
                  <span class="text-sm">👤</span>
                  <p class="text-sm font-bold text-gray-900">{{ order.customer_name }}</p>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="text-sm">📞</span>
                  <a 
                    :href="`tel:${order.customer_phone}`"
                    @click.stop
                    class="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                  >
                    {{ order.customer_phone }}
                  </a>
                </div>
                <div v-if="order.customer_email" class="flex items-center gap-1.5">
                  <span class="text-sm">✉️</span>
                  <a 
                    :href="`mailto:${order.customer_email}`"
                    @click.stop
                    class="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                  >
                    {{ order.customer_email }}
                  </a>
                </div>
              </div>

              <!-- Total Amount -->
              <div class="mt-2 pt-2 border-t border-gray-200">
                <p class="text-xs font-semibold text-gray-500 uppercase mb-0.5">Ukupno</p>
                <p class="text-sm font-bold text-green-600">
                  {{ formatPrice(order.total_amount) }}
                </p>
              </div>
            </div>

            <!-- Right Section -->
            <div class="flex flex-row sm:flex-col items-start sm:items-end gap-2 w-full sm:w-auto mt-2 sm:mt-0">
              <!-- Status Badge -->
              <div class="flex flex-col items-start sm:items-end gap-1 flex-1 sm:flex-none">
                <span
                  :class="statusColors[order.status]"
                  class="px-2 py-1 rounded-full text-xs font-bold shadow-sm border whitespace-nowrap"
                  :style="{ borderColor: 'transparent' }"
                >
                  {{ statusLabels[order.status] }}
                </span>
              </div>

              <!-- Items Count -->
              <div v-if="order.items && order.items.length > 0" class="text-left sm:text-right">
                <p class="text-xs text-gray-500 uppercase font-semibold mb-0.5">Stavki</p>
                <p class="text-sm font-bold text-gray-700">
                  {{ order.items.length }} {{ order.items.length === 1 ? 'stavka' : 'stavki' }}
                </p>
              </div>

              <!-- View Button -->
              <button
                @click.stop="openDetailModal(order)"
                class="px-4 py-2 bg-[#1976d2] hover:bg-[#1565c0] text-white rounded-lg font-bold shadow-md
                   hover:shadow-lg transition-all duration-300 cursor-pointer transform hover:scale-[1.02] flex items-center gap-1.5 text-xs whitespace-nowrap"
              >
                <span>👁️</span>
                <span class="hidden sm:inline">Pregled</span>
              </button>
            </div>

          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Empty -->
    <div v-else class="py-10 text-center">
      <div class="inline-block bg-gray-100 rounded-full p-4 mb-3">
        <span class="text-3xl">📦</span>
      </div>
      <p class="text-sm font-semibold text-gray-600 mb-1">
        Nema narudžbina
      </p>
      <p class="text-sm text-gray-500">Nove narudžbine će se pojaviti ovde automatski</p>
    </div>

    <!-- DETAIL MODAL -->
    <div
      v-if="showDetailModal && orderStore.selected"
      @click.self="closeDetailModal"
      class="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-[1500]"
    >
      <div class="bg-white rounded-lg w-full max-w-[600px] max-h-[98vh] overflow-y-auto">

        <!-- Modal Header -->
        <div class="p-5 border-b bg-[#1976d2] text-white flex justify-between">
          <div>
            <h3 class="text-base font-bold mb-1.5 px-1">
              Narudžbina #{{ orderStore.selected.id }}
            </h3>
            <p class="text-xs opacity-90 px-1">{{ formatDate(orderStore.selected.created_at) }}</p>
            <p v-if="getOrderStores(orderStore.selected).length" class="text-xs opacity-90 px-1 mt-1">
              {{ orderStoreIcons(orderStore.selected) }} {{ orderStoreLabel(orderStore.selected) }}
            </p>
          </div>

          <button @click="closeDetailModal" class="text-2xl hover:bg-white/20 rounded px-2 py-1 cursor-pointer transition">
            &times;
          </button>
        </div>

        <div class="p-6 space-y-6">

          <!-- Kupac -->
          <div>
            <h4 class="font-bold text-base mb-2 text-gray-900 px-1">Kupac</h4>
            <div class="space-y-3 bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div>
                <p class="text-xs text-gray-500 uppercase font-medium mb-1 px-1">Ime</p>
                <p class="text-sm font-semibold text-gray-900 px-1">{{ orderStore.selected.customer_name }}</p>
              </div>

              <div>
                <p class="text-xs text-gray-500 uppercase font-medium mb-1 px-1">Telefon</p>
                <a
                  :href="`tel:${orderStore.selected.customer_phone}`"
                  class="text-sm font-semibold text-[#1976d2] hover:text-[#1565c0] hover:underline cursor-pointer px-1"
                >
                  {{ orderStore.selected.customer_phone }}
                </a>
              </div>

              <div v-if="orderStore.selected.customer_email">
                <p class="text-xs text-gray-500 uppercase font-medium mb-1 px-1">Email</p>
                <a
                  :href="`mailto:${orderStore.selected.customer_email}`"
                  class="text-sm font-semibold text-[#1976d2] hover:text-[#1565c0] hover:underline cursor-pointer px-1"
                >
                  {{ orderStore.selected.customer_email }}
                </a>
              </div>

              <div v-if="orderStore.selected.address">
                <p class="text-xs text-gray-500 uppercase font-medium mb-1 px-1">Adresa</p>
                <p class="text-sm text-gray-900 px-1">{{ orderStore.selected.address }}</p>
              </div>
              <div v-if="orderStore.selected.city">
                <p class="text-xs text-gray-500 uppercase font-medium mb-1 px-1">Grad</p>
                <p class="text-sm text-gray-900 px-1">{{ orderStore.selected.city }}</p>
              </div>
            </div>
          </div>

          <!-- Items -->
          <div>
            <h4 class="font-bold text-base mb-2 text-gray-900 px-1">Stavke</h4>

            <div class="space-y-3">
              <div
                v-for="item in orderStore.selected.items"
                :key="item.id"
                class="bg-white border border-gray-200 p-3 rounded-lg hover:shadow-sm transition"
              >
                <div class="flex justify-between items-start">

                  <div class="flex-1">
                    <p class="font-bold text-sm text-gray-900 mb-1 px-1">{{ item.product_name }}</p>
                    <p v-if="item.variant_name" class="text-xs text-gray-600 mb-1.5 px-1">{{ item.variant_name }}</p>

                    <p class="text-xs text-gray-500 px-1">
                      Količina:
                      <span class="font-semibold text-gray-700">{{ item.quantity }}</span> kom
                      <span v-if="item.sold_by_length && item.effective_length_per_unit" class="text-gray-600">
                        - {{ (parseFloat(item.quantity) * parseFloat(item.effective_length_per_unit)).toFixed(2) }} metara
                      </span>
                    </p>

                    <p class="text-xs text-gray-500 mt-1 px-1">{{ formatPrice(item.unit_price) }} / kom</p>
                  </div>

                  <div class="text-right ml-3">
                    <p class="text-sm font-bold text-green-700 px-1">
                      {{ formatPrice(item.total_price) }}
                    </p>
                  </div>

                </div>
              </div>
            </div>
          </div>

          <!-- Total -->
          <div class="border-t border-gray-300 pt-3">
            <div class="flex justify-between items-center bg-green-600
            text-white p-3 rounded-lg">
              <span class="text-base font-bold px-1">Ukupno:</span>
              <span class="text-base font-bold px-1">{{ formatPrice(orderStore.selected.total_amount) }}</span>
            </div>
          </div>

          <!-- Napomena -->
          <div v-if="orderStore.selected.notes">
            <h4 class="font-bold text-base mb-2 text-gray-900 px-1">Napomena kupca</h4>
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-r-lg">
              <p class="text-sm text-gray-800 px-1">{{ orderStore.selected.notes }}</p>
            </div>
          </div>

          <!-- UPDATE STATUS -->
          <div>
            <h4 class="font-bold text-base mb-3 text-gray-900 px-1">Ažuriraj status</h4>

            <div class="flex flex-col md:flex-row md:flex-nowrap gap-2 md:overflow-x-auto">
              <button
                v-for="(label, status) in statusLabels"
                :key="status"
                @click="async () => {
                  await orderStore.updateStatus(orderStore.selected.id, status)
                  await refreshOrders()
                }"
                :class="orderStore.selected.status === status
                  ? 'bg-[#1976d2] hover:bg-[#1565c0] text-white shadow-md scale-[1.02]'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer whitespace-nowrap flex-shrink-0 w-full md:w-auto"
              >
                {{ label }}
              </button>
            </div>
          </div>

          <!-- DELETE ORDER -->
          <div class="border-t pt-3 mt-3">
            <button
              @click="deleteOrder"
              class="w-full px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
            >
              Obriši narudžbinu
            </button>
          </div>

        </div>

      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <ConfirmModal
      :show="showConfirmDelete"
      message="Da li ste sigurni da želite da obrišete ovu narudžbinu? Ova akcija je nepovratna."
      title="Potvrda brisanja"
      confirmText="Obriši"
      cancelText="Odustani"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<style scoped>
.order-list-enter-active {
  transition: all 0.4s ease;
}

.order-list-leave-active {
  transition: all 0.3s ease;
}

.order-list-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.order-list-leave-to {
  opacity: 0;
  transform: translateX(20px) scale(0.95);
}

.order-list-move {
  transition: transform 0.3s ease;
}
</style>
