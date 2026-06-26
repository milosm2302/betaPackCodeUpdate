<script setup>
import { useHead } from '@unhead/vue'
import { useRouter } from 'vue-router'
import { STORE_LIST } from '@/config/stores'

const router = useRouter()

useHead({
  title: 'BetaPack | Gvožđara i Ambalaža Beograd',
  meta: [
    {
      name: 'description',
      content: 'BetaPack - izaberite između Gvožđare (kovano gvožđe, bravarski materijali) i Ambalaže (posude, folije, kese) u Beogradu.'
    }
  ]
})

const selectStore = (store) => {
  router.push(store.path)
}

const goTo = (path) => {
  router.push(path)
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white flex flex-col">
    <!-- Header -->
    <header class="border-b border-white/10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 cursor-pointer" @click="goTo('/')">
          <img src="/betapack-logo.png" alt="Beta Pack Logo" class="h-10 w-auto" />
          <div class="text-lg font-bold">BETA PACK</div>
        </div>
        <nav class="flex items-center gap-1 sm:gap-3">
          <button
            @click="goTo('/o-nama')"
            class="text-gray-300 hover:text-white hover:bg-white/10 px-3 py-2 rounded-lg transition font-semibold text-sm cursor-pointer"
          >
            O nama
          </button>
          <button
            @click="goTo('/kontakt')"
            class="text-gray-300 hover:text-white hover:bg-white/10 px-3 py-2 rounded-lg transition font-semibold text-sm cursor-pointer"
          >
            Kontakt
          </button>
        </nav>
      </div>
    </header>

    <!-- Hero -->
    <main class="relative flex-1 flex flex-col items-center justify-center px-4 py-12 overflow-hidden">
      <!-- Animated background blobs -->
      <div class="pointer-events-none absolute inset-0 overflow-hidden">
        <div class="blob blob-blue absolute -top-24 -left-24 w-96 h-96 rounded-full opacity-30 blur-3xl"></div>
        <div class="blob blob-green absolute -bottom-24 -right-24 w-96 h-96 rounded-full opacity-30 blur-3xl"></div>
      </div>

      <div class="relative text-center mb-12 max-w-2xl">
        <span class="inline-block mb-4 px-4 py-1.5 rounded-full text-xs font-semibold tracking-wider uppercase bg-white/10 border border-white/15 text-gray-200">
          Dve prodavnice · jedno mesto
        </span>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold mb-4 leading-tight">
          Dobrodošli u
          <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-green-400 bg-clip-text text-transparent">
            Beta Pack
          </span>
        </h1>
        <p class="text-gray-300 text-base sm:text-lg">
          Izaberite prodavnicu koju želite da posetite
        </p>
      </div>

      <!-- Store selection cards -->
      <div class="relative grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-5xl w-full">
        <button
          v-for="store in STORE_LIST"
          :key="store.id"
          @click="selectStore(store)"
          class="store-card group relative overflow-hidden rounded-3xl border border-white/10 p-8 text-left transition-all duration-500 hover:-translate-y-2 cursor-pointer"
          :style="{ '--glow': store.glow, '--g-from': store.gradientFrom, '--g-to': store.gradientTo }"
        >
          <!-- Gradient sheen on hover -->
          <div
            class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
            :style="{ background: `radial-gradient(120% 120% at 0% 0%, ${store.gradientFrom}33, transparent 60%)` }"
          ></div>
          <!-- Top accent bar -->
          <div
            class="absolute top-0 left-0 right-0 h-1.5 scale-x-0 group-hover:scale-x-100 origin-left transition-transform duration-500"
            :style="{ background: `linear-gradient(90deg, ${store.gradientFrom}, ${store.gradientTo})` }"
          ></div>

          <div class="relative">
            <div
              class="inline-flex items-center justify-center w-16 h-16 rounded-2xl text-4xl mb-5 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-transform duration-500"
              :style="{ background: `linear-gradient(135deg, ${store.gradientFrom}, ${store.gradientTo})` }"
            >
              {{ store.icon }}
            </div>
            <h2 class="text-2xl font-bold mb-1.5">{{ store.label }}</h2>
            <p class="text-sm mb-3 font-medium" :style="{ color: store.gradientFrom }">{{ store.tagline }}</p>
            <p class="text-gray-400 text-sm leading-relaxed mb-5">{{ store.description }}</p>

            <ul class="space-y-1.5 mb-6">
              <li
                v-for="feature in store.features"
                :key="feature"
                class="flex items-center gap-2 text-sm text-gray-300"
              >
                <span
                  class="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold"
                  :style="{ backgroundColor: store.gradientFrom }"
                >✓</span>
                {{ feature }}
              </li>
            </ul>

            <div
              class="inline-flex items-center gap-2 font-semibold text-sm px-5 py-2.5 rounded-xl shadow-md group-hover:gap-3 transition-all duration-300"
              :style="{ background: `linear-gradient(135deg, ${store.gradientFrom}, ${store.gradientTo})` }"
            >
              Uđi u prodavnicu
              <span class="transition-transform duration-300 group-hover:translate-x-1">→</span>
            </div>
          </div>
        </button>
      </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-white/10 py-6 text-center text-gray-400 text-sm">
      <p>BetaPack d.o.o. · Pukovnika Milenka Pavlovića 159 A, Beograd</p>
      <p class="mt-1">📞 +381 65 330 02 42 · ✉️ office@betapack.co.rs</p>
    </footer>
  </div>
</template>

<style scoped>
.store-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(8px);
  box-shadow: 0 10px 40px -20px rgba(0, 0, 0, 0.6);
}
.store-card:hover {
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 30px 60px -25px var(--glow);
}

.blob-blue {
  background: radial-gradient(circle, #1e88e5, transparent 70%);
  animation: float 14s ease-in-out infinite;
}
.blob-green {
  background: radial-gradient(circle, #43a047, transparent 70%);
  animation: float 16s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -30px) scale(1.15); }
}

@media (prefers-reduced-motion: reduce) {
  .blob-blue, .blob-green { animation: none; }
}
</style>
