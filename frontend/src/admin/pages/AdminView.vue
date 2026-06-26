<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

import CategoryManager from '../components/CategoryManager.vue'
import ProductManager from '../components/ProductManager.vue'
import OrdersManager from '../components/OrdersManager.vue'
import ContactMessagesManager from '../components/ContactMessagesManager.vue'
import CompetitorMonitor from '../components/CompetitorMonitor.vue'

import { useAdminNav } from '../composables/useAdminNav'
import { useAdminStore } from '../composables/useAdminStore'
import { useAdminStatsStore } from '../store/adminStats'

const router = useRouter()
const authStore = useAuthStore()

const { activeView, setView, views } = useAdminNav()
const { activeStore, setStore, storeTabs } = useAdminStore()
const statsStore = useAdminStatsStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/admin/login')
}

const goToHomePage = () => {
  router.push('/')
}

const refreshStats = () => statsStore.refresh(activeStore.value)

const selectStore = (storeId) => {
  setStore(storeId)
  refreshStats()
}

watch(activeStore, () => refreshStats())

onMounted(async () => {
  await authStore.initialize()
  await refreshStats()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">

    <!-- Header -->
    <header class="bg-white px-4 py-3 shadow-md border-b border-gray-200 flex justify-between items-center sticky top-0 z-[100] backdrop-blur-sm bg-white/95">
      <div class="flex items-center gap-1.5">
        <div class="bg-[#1976d2] text-white rounded-lg px-2 py-1 shadow-md">
          <span class="text-base font-bold">⚙️</span>
        </div>
        <div>
          <h1 class="text-base font-bold text-gray-900">Beta Pack</h1>
          <p class="text-xs text-gray-500 font-medium">Admin Panel</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          @click="goToHomePage"
          class="px-4 py-2 border border-[#1976d2] text-[#1976d2] hover:bg-[#1976d2] hover:text-white rounded-lg font-semibold transition-all duration-300 cursor-pointer flex items-center gap-1.5 text-xs"
        >
          <span>🏠</span>
          <span class="hidden sm:inline">Glavna</span>
        </button>
        <div class="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200">
          <div class="w-8 h-8 bg-[#1976d2] rounded-full flex items-center justify-center text-white font-bold shadow-md text-sm">
            {{ authStore.user?.username?.charAt(0).toUpperCase() }}
          </div>
          <span class="font-semibold text-gray-800 text-xs">{{ authStore.user?.username }}</span>
        </div>
        <button
          @click="handleLogout"
          class="px-4 py-2 border border-red-500 text-red-600 hover:bg-red-500 hover:text-white rounded-lg font-semibold transition-all duration-300 cursor-pointer flex items-center gap-1.5 text-xs"
        >
          <span>🚪</span>
          <span class="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden flex-col md:flex-row md:-mt-0">

      <!-- Sidebar -->
      <aside class="w-full md:w-[240px] bg-white border-r border-gray-200 overflow-y-auto md:fixed md:top-[64px] md:left-0 md:h-[calc(100vh-64px)] shadow-lg z-40">
        <nav class="p-3 pt-4">

          <h3 class="text-xs uppercase text-gray-500 font-bold mb-3 ml-1 tracking-wider">
            📋 Katalog
          </h3>

          <!-- Dinamička navigacija -->
          <div class="space-y-1.5">
            <button
              v-for="v in views"
              :key="v.id"
              @click="setView(v.id)"
              :class="activeView === v.id
                ? 'bg-[#1976d2] text-white shadow-md scale-[1.01]'
                : 'bg-transparent text-gray-700 hover:bg-gray-50 hover:text-gray-900'"
              class="w-full flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-300 font-semibold text-sm border"
              :style="activeView === v.id ? { borderColor: 'transparent' } : { borderColor: '#e5e7eb' }"
            >
              <span class="text-lg">{{ v.icon }}</span>
              <span class="flex-1 text-left text-xs">{{ v.label }}</span>

              <span
                v-if="v.id !== 'competitors'"
                class="px-2 py-0.5 rounded-full text-xs font-bold min-w-[24px] text-center"
                :class="activeView === v.id ? 'bg-white/30 text-white' : 'bg-gray-200 text-gray-700'"
              >
                {{
                  v.id === 'categories' ? statsStore.categories :
                  v.id === 'subcategories' ? statsStore.subcategories :
                  v.id === 'orders' ? statsStore.orders :
                  v.id === 'contact' ? statsStore.contactMessages :
                  statsStore.products
                }}
              </span>
            </button>
          </div>

          <!-- Statistika -->
          <div class="mt-4 bg-[#1976d2] p-3 rounded-lg text-white shadow-lg border border-[#1976d2]/30">
            <h4 class="text-xs font-bold uppercase mb-3 opacity-90 tracking-wider">📊 Statistika</h4>
            <div class="space-y-2">
              <div class="flex justify-between items-center bg-white/10 rounded-lg p-2 backdrop-blur-sm">
                <div class="flex items-center gap-1.5">
                  <span class="text-base">📦</span>
                  <span class="text-xs font-semibold opacity-90">Proizvoda</span>
                </div>
                <span class="text-lg font-bold">{{ statsStore.products }}</span>
              </div>

              <div class="flex justify-between items-center bg-white/10 rounded-lg p-2 backdrop-blur-sm">
                <div class="flex items-center gap-1.5">
                  <span class="text-base">📁</span>
                  <span class="text-xs font-semibold opacity-90">Kategorija</span>
                </div>
                <span class="text-lg font-bold">{{ statsStore.categories }}</span>
              </div>

              <div class="flex justify-between items-center bg-white/10 rounded-lg p-2 backdrop-blur-sm">
                <div class="flex items-center gap-1.5">
                  <span class="text-base">📋</span>
                  <span class="text-xs font-semibold opacity-90">Narudžbina</span>
                </div>
                <span class="text-lg font-bold">{{ statsStore.orders }}</span>
              </div>
            </div>
          </div>

        </nav>
      </aside>
        
      <!-- Main content -->
      <main class="flex-1 overflow-y-auto max-w-[1600px] mx-auto md:ml-[240px]" :class="activeView === 'orders' ? 'p-4 pt-0' : 'p-4'">

        <!-- Store selector (catalog only) -->
        <div v-if="activeView !== 'competitors' && activeView !== 'orders' && activeView !== 'contact'" class="flex gap-2 mb-4">
          <button
            v-for="tab in storeTabs"
            :key="tab.id"
            @click="selectStore(tab.id)"
            :class="activeStore === tab.id
              ? 'bg-[#1976d2] text-white shadow-md'
              : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'"
            class="px-4 py-2 rounded-lg font-semibold text-sm cursor-pointer transition flex items-center gap-2"
          >
            <span>{{ tab.icon }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <CategoryManager
          v-if="activeView === 'categories'"
          :store="activeStore"
          @update-count="refreshStats"
        />

        <ProductManager
          v-if="activeView === 'products'"
          :store="activeStore"
          @update-count="refreshStats"
        />

        <OrdersManager
          v-if="activeView === 'orders'"
          @update-count="refreshStats"
        />

        <ContactMessagesManager
          v-if="activeView === 'contact'"
          @update-count="refreshStats"
        />

        <CompetitorMonitor
          v-if="activeView === 'competitors'"
        />

      </main>
    </div>
  </div>
</template>
