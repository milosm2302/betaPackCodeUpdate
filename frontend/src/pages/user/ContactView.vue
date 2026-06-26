<script setup>
import { ref } from 'vue'
import { useHead } from '@unhead/vue'
import { api } from '@/services/api'
import TheHeader from '@/components/TheHeader.vue'
import TheFooter from '@/components/TheFooter.vue'
import { useStore } from '@/composables/useStore'

const { storeId } = useStore()

// SEO Meta Tags
useHead({
  title: 'Kontakt - BetaPack | Kovano Gvožđe',
  meta: [
    { name: 'description', content: 'Kontaktirajte BetaPack za sve informacije o bravarskim materijalima. Adresa: Pukovnika Milenka Pavlovića 159 A, Zemun-Batajnica. Telefon: 065/330 02 42.' },
    { name: 'keywords', content: 'kontakt BetaPack, telefon gvožđara Beograd, adresa bravarija Batajnica, kovano gvožđe Zemun kontakt, gde kupiti kovano gvožđe Beograd, bravarski materijali prodavnica' },
    // Open Graph
    { property: 'og:site_name', content: 'BetaPack' },
    { property: 'og:title', content: 'Kontakt - BetaPack' },
    { property: 'og:description', content: 'Kontaktirajte nas za sve informacije o bravarskim materijalima' },
    { property: 'og:url', content: 'https://www.betapack.co.rs/kontakt' },
    { property: 'og:type', content: 'website' },
    { property: 'og:locale', content: 'sr_RS' }
  ],
  link: [
    { rel: 'canonical', href: 'https://www.betapack.co.rs/kontakt' }
  ]
})

const contactInfo = {
  name: 'Beta Pack d.o.o.',
  address: 'Pukovnika Milenka Pavlovića 159 A',
  city: 'Zemun-Batajnica',
  phone1: '065/330 02 42',
  phone2: '063/8757 725',
  email: 'office@betapack.co.rs',
  coordinates: { lat: 44.914361, lng: 20.258167 }
}

const form = ref({
  name: '',
  email: '',
  phone: '',
  message: ''
})

const sending = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Validacija
const validateEmail = (email) => {
  if (!email) return true // Opciono polje
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const validatePhone = (phone) => {
  if (!phone) return true // Opciono polje
  // Srpski telefoni: 06X/XXX-XXXX ili 06XXXXXXXX ili +381...
  const phoneRegex = /^(\+381|0)(6[0-9]|[1-3][0-9])[0-9]{6,7}$/
  // Dozvoli i sa razmakom, crtom ili kosom crtom
  const cleanPhone = phone.replace(/[\s\-\/]/g, '')
  return phoneRegex.test(cleanPhone)
}

const validateForm = () => {
  // Proveri da li je ime uneto
  if (!form.value.name.trim()) {
    errorMessage.value = 'Ime je obavezno.'
    return false
  }

  // Proveri da li je poruka uneta
  if (!form.value.message.trim()) {
    errorMessage.value = 'Poruka je obavezna.'
    return false
  }

  // Proveri da je bar email ili telefon unet
  const hasEmail = form.value.email && form.value.email.trim()
  const hasPhone = form.value.phone && form.value.phone.trim()

  if (!hasEmail && !hasPhone) {
    errorMessage.value = 'Morate navesti bar email ili telefon.'
    return false
  }

  // Ako je email unet, proveri format
  if (hasEmail && !validateEmail(form.value.email)) {
    errorMessage.value = 'Unesite ispravan email.'
    return false
  }

  // Ako je telefon unet, proveri format
  if (hasPhone && !validatePhone(form.value.phone)) {
    errorMessage.value = 'Unesite ispravan broj telefona (npr. 065/123-4567 ili 0651234567).'
    return false
  }

  return true
}

const sendMessage = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  // Validacija forme
  if (!validateForm()) {
    return
  }

  sending.value = true

  try {
    const response = await api.post('/contact/', { ...form.value, store: storeId.value || 'steel' })

    if (response.data.success) {
      successMessage.value = 'Poruka uspešno poslata! Kontaktiraćemo vas uskoro.'
      form.value = { name: '', email: '', phone: '', message: '' }
    }
  } catch (error) {
    console.error('Error sending contact message:', error)

    // Prikazi specificnu gresku sa servera
    if (error.response?.data?.non_field_errors) {
      errorMessage.value = error.response.data.non_field_errors[0]
    } else if (error.response?.data) {
      // Prikazi prvu gresku iz response
      const firstError = Object.values(error.response.data)[0]
      errorMessage.value = Array.isArray(firstError) ? firstError[0] : firstError
    } else {
      errorMessage.value = 'Došlo je do greške prilikom slanja poruke. Pokušajte ponovo.'
    }
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <TheHeader />

    <main class="flex-1 py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <!-- Page Header -->
        <div class="text-center mb-5">
          <h1 class="text-xl lg:text-2xl font-bold text-gray-900 mb-1.5">KONTAKTIRAJTE NAS</h1>
          <p class="text-xs lg:text-sm text-gray-600">
            Za sva pitanja i ponude, slobodno nas pozovite!
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">

          <!-- Kontakt Forma -->
          <div class="bg-white rounded-xl shadow-lg p-3 lg:p-5">
            <h2 class="text-base lg:text-lg font-bold text-gray-900 mb-3">Pošaljite poruku</h2>

            <form @submit.prevent="sendMessage" class="space-y-2.5">
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1.5">
                  Ime i prezime *
                </label>
                <input
                  v-model="form.name"
                  type="text"
                  class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1976d2] focus:border-transparent text-sm"
                  placeholder="Vaše ime"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1.5">
                  Email
                </label>
                <input
                  v-model="form.email"
                  type="email"
                  class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1976d2] focus:border-transparent text-sm"
                  placeholder="vas.email@primer.com"
                />
              </div>

              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1.5">
                  Telefon
                </label>
                <input
                  v-model="form.phone"
                  type="tel"
                  class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1976d2] focus:border-transparent text-sm"
                  placeholder="065/123-4567"
                />
              </div>

              <p class="text-xs text-gray-600 -mt-2">
                * Molimo vas da unesete najmanje jedan kontakt – email ili broj telefona.
              </p>

              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1.5">
                  Poruka *
                </label>
                <textarea
                  v-model="form.message"
                  required
                  rows="4"
                  class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1976d2] focus:border-transparent resize-none text-sm"
                  placeholder="Opišite vašu potrebu ili postavite pitanje..."
                ></textarea>
              </div>

              <div v-if="successMessage" class="bg-green-100 text-green-800 px-3 py-2 rounded-lg text-sm">
                {{ successMessage }}
              </div>

              <div v-if="errorMessage" class="bg-red-100 text-red-800 px-3 py-2 rounded-lg text-sm">
                {{ errorMessage }}
              </div>

              <button
                type="submit"
                :disabled="sending"
                class="w-full bg-gradient-to-r from-[#1976d2] to-[#1565c0] hover:from-[#1565c0] hover:to-[#1565c0] text-white font-semibold py-2.5 px-5 rounded-lg transition disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed text-sm"
              >
                {{ sending ? 'Slanje...' : 'Pošalji poruku' }}
              </button>
            </form>
          </div>

          <!-- Kontakt Informacije -->
          <div class="space-y-5">

            <!-- Info kartice -->
            <div class="bg-white rounded-xl shadow-lg p-3 lg:p-5">
              <h2 class="text-base lg:text-lg font-bold text-gray-900 mb-3">Kontakt informacije</h2>

              <div class="space-y-3">
                <!-- Telefoni -->
                <div class="flex items-start gap-2.5">
                  <div class="bg-blue-100 p-1.5 rounded-lg">
                    <span class="text-base">📞</span>
                  </div>
                  <div class="flex-1">
                    <h3 class="font-semibold text-xs text-gray-900 mb-0.5">Pozovite nas</h3>
                    <a
                      :href="`tel:${contactInfo.phone1.replace(/\//g, '')}`"
                      class="block text-[#1565c0] hover:text-[#1565c0] font-semibold text-xs mb-0.5 hover:underline cursor-pointer"
                    >
                      {{ contactInfo.phone1 }}
                    </a>
                    <a
                      :href="`tel:${contactInfo.phone2.replace(/\//g, '')}`"
                      class="block text-[#1565c0] hover:text-[#1565c0] font-semibold text-xs hover:underline cursor-pointer"
                    >
                      {{ contactInfo.phone2 }}
                    </a>
                  </div>
                </div>

                <!-- Email -->
                <div class="flex items-start gap-2.5">
                  <div class="bg-blue-100 p-1.5 rounded-lg">
                    <span class="text-base">✉️</span>
                  </div>
                  <div class="flex-1">
                    <h3 class="font-semibold text-xs text-gray-900 mb-0.5">Email</h3>
                    <a
                      :href="`mailto:${contactInfo.email}`"
                      class="text-xs text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
                    >
                      {{ contactInfo.email }}
                    </a>
                  </div>
                </div>

                <!-- Adresa -->
                <div class="flex items-start gap-2.5">
                  <div class="bg-green-100 p-1.5 rounded-lg">
                    <span class="text-base">📍</span>
                  </div>
                  <div class="flex-1">
                    <h3 class="font-semibold text-xs text-gray-900 mb-1.5">Adresa</h3>
                    <p class="text-xs text-gray-700">{{ contactInfo.address }}</p>
                    <p class="text-xs text-gray-700">{{ contactInfo.city }}</p>
                    <a
                      :href="`https://www.google.com/maps?q=${contactInfo.coordinates.lat},${contactInfo.coordinates.lng}`"
                      target="_blank"
                      class="inline-block mt-3 text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
                    >
                      Prikaži na mapi →
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <!-- Radno vreme -->
            <div class="bg-white rounded-xl shadow-lg p-6">
              <h2 class="text-xl font-bold text-gray-900 mb-5">Radno vreme</h2>

              <div class="space-y-2.5">
                <div class="flex justify-between items-center py-2 border-b">
                  <span class="text-gray-700">Ponedeljak - Petak</span>
                  <span class="font-semibold text-gray-900">08:00 - 17:00</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b">
                  <span class="text-gray-700">Subota</span>
                  <span class="font-semibold text-gray-900">08:00 - 14:00</span>
                </div>
                <div class="flex justify-between items-center py-2">
                  <span class="text-gray-700">Nedelja</span>
                  <span class="font-semibold text-red-600">Zatvoreno</span>
                </div>
              </div>
            </div>

          </div>

        </div>

        <!-- Google Maps -->
        <div class="mt-9 bg-white rounded-xl shadow-lg overflow-hidden">
          <iframe
            :src="`https://www.google.com/maps?q=${contactInfo.coordinates.lat},${contactInfo.coordinates.lng}&output=embed`"
            width="100%"
            height="360"
            style="border:0;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>
        </div>

      </div>
    </main>

    <TheFooter />
  </div>
</template>
