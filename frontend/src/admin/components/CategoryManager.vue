<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useCategoryStore } from '@/admin/store/categories'
import { useSubcategoryStore } from '@/admin/store/subcategories'
import ConfirmModal from '@/components/ConfirmModal.vue'
import AdminModal from './AdminModal.vue'

const emit = defineEmits(['update-count'])
const props = defineProps({ store: { type: String, default: 'steel' } })

const categoryStore = useCategoryStore()
const subcategoryStore = useSubcategoryStore()

// Confirm modal
const showConfirm = ref(false)
const confirmMessage = ref("")
const confirmAction = ref(null)

const openConfirm = (message, action) => {
  confirmMessage.value = message
  confirmAction.value = action
  showConfirm.value = true
}

const closeConfirm = () => {
  showConfirm.value = false
  confirmMessage.value = ""
  confirmAction.value = null
}

const doConfirm = () => {
  if (confirmAction.value) confirmAction.value()
  closeConfirm()
}

// Category modal
const showCategoryModal = ref(false)
const isEditingCategory = ref(false)
const savingCategory = ref(false)
const categoryError = ref('')

const categoryForm = ref({
  id: null,
  name: '',
  description: ''
})

const openAddCategoryModal = () => {
  isEditingCategory.value = false
  categoryForm.value = { id: null, name: '', description: '' }
  showCategoryModal.value = true
  categoryError.value = ''
}

const openEditCategoryModal = (cat) => {
  isEditingCategory.value = true
  categoryForm.value = {
    id: cat.id,
    name: cat.name,
    description: cat.description || ''
  }
  showCategoryModal.value = true
  categoryError.value = ''
}

const closeCategoryModal = () => {
  showCategoryModal.value = false
  categoryForm.value = { id: null, name: '', description: '' }
  categoryError.value = ''
}

const saveCategory = async () => {
  savingCategory.value = true
  categoryError.value = ''

  try {
    const payload = {
      name: categoryForm.value.name,
      description: categoryForm.value.description,
      store: props.store
    }

    if (isEditingCategory.value) {
      await categoryStore.update(categoryForm.value.id, payload)
    } else {
      await categoryStore.create(payload)
    }

    await loadData()
    closeCategoryModal()

  } catch (err) {
    console.error(err)
    categoryError.value = 'Greška pri čuvanju kategorije.'
  } finally {
    savingCategory.value = false
  }
}

const deleteCategory = (cat) => {
  openConfirm(
    `Da li želiš da obrišeš kategoriju "${cat.name}"?`,
    async () => {
      try {
        await categoryStore.remove(cat.id)
        await loadData()
      } catch {
        openConfirm("Ne može da se obriše kategorija jer ima proizvode!", null)
      }
    }
  )
}

// Subcategory modal
const showSubcategoryModal = ref(false)
const isEditingSubcategory = ref(false)
const savingSubcategory = ref(false)
const subcategoryError = ref('')
const selectedCategoryForSubcategory = ref(null)

const subcategoryForm = ref({
  id: null,
  name: '',
  category: '',
  description: ''
})

const openAddSubcategoryModal = (categoryId) => {
  isEditingSubcategory.value = false
  selectedCategoryForSubcategory.value = categoryId
  subcategoryForm.value = {
    id: null,
    name: '',
    category: categoryId,
    description: ''
  }
  showSubcategoryModal.value = true
  subcategoryError.value = ''
}

const openEditSubcategoryModal = (sub) => {
  isEditingSubcategory.value = true
  selectedCategoryForSubcategory.value = sub.category
  subcategoryForm.value = {
    id: sub.id,
    name: sub.name,
    category: sub.category,
    description: sub.description || ''
  }
  showSubcategoryModal.value = true
  subcategoryError.value = ''
}

const closeSubcategoryModal = () => {
  showSubcategoryModal.value = false
  subcategoryForm.value = { id: null, name: '', category: '', description: '' }
  subcategoryError.value = ''
  selectedCategoryForSubcategory.value = null
}

const saveSubcategory = async () => {
  savingSubcategory.value = true
  subcategoryError.value = ''

  try {
    const payload = {
      name: subcategoryForm.value.name,
      category: subcategoryForm.value.category,
      description: subcategoryForm.value.description
    }

    if (isEditingSubcategory.value) {
      await subcategoryStore.update(subcategoryForm.value.id, payload)
    } else {
      await subcategoryStore.create(payload)
    }

    await loadData()
    closeSubcategoryModal()

  } catch (err) {
    console.error(err)
    subcategoryError.value = 'Greška pri čuvanju podkategorije. Proveri da li naziv već postoji.'
  } finally {
    savingSubcategory.value = false
  }
}

const deleteSubcategory = (sub) => {
  openConfirm(
    `Obrisati podkategoriju "${sub.name}"?`,
    async () => {
      try {
        await subcategoryStore.remove(sub.id)
        await loadData()
      } catch (err) {
        console.error(err)
        openConfirm(
          "Ne može da se obriše podkategorija! Moguće da postoje proizvodi u njoj.",
          null
        )
      }
    }
  )
}

// Expanded categories tracking
const expandedCategories = ref(new Set())

const toggleCategory = (categoryId) => {
  if (expandedCategories.value.has(categoryId)) {
    expandedCategories.value.delete(categoryId)
  } else {
    expandedCategories.value.add(categoryId)
  }
}

const isCategoryExpanded = (categoryId) => {
  return expandedCategories.value.has(categoryId)
}

// Get subcategories for a category
const getSubcategoriesForCategory = (categoryId) => {
  return subcategoryStore.list.filter(sub => sub.category === categoryId)
}

const categories = computed(() => categoryStore.list)
const loading = computed(() => categoryStore.loading || subcategoryStore.loading)

const loadData = async () => {
  await categoryStore.fetch(props.store)
  await subcategoryStore.fetch(props.store)
  emit('update-count')
}

watch(() => props.store, loadData)

onMounted(loadData)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <div>
        <h2 class="text-xs lg:text-sm font-bold text-gray-900 mb-1 flex items-center gap-1">📁 Kategorije i Podkategorije</h2>
        <p class="text-xs text-gray-500 font-medium">Organizujte proizvode u kategorije i podkategorije</p>
      </div>

      <button
        @click="openAddCategoryModal"
        class="px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-lg text-xs font-semibold shadow-md hover:shadow-lg transition-all cursor-pointer flex items-center gap-1.5"
      >
        <span class="text-sm">➕</span>
        <span>Dodaj Kategoriju</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-[#1976d2] mb-4"></div>
      <p class="text-gray-600 text-sm font-semibold">Učitavanje...</p>
    </div>

    <!-- Categories List -->
    <div v-else-if="categories.length > 0" class="space-y-4">
      <div
        v-for="cat in categories"
        :key="cat.id"
        class="bg-white border border-gray-200 rounded-lg shadow-md hover:shadow-lg transition-all duration-300"
      >
        <!-- Category Header -->
        <div class="p-3">
          <div class="flex justify-between items-start mb-2">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <h3 class="text-xs font-bold text-gray-900">{{ cat.name }}</h3>
                <span class="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-bold border border-green-200">
                  📦 {{ cat.product_count || 0 }}
                </span>
              </div>

              <p v-if="cat.description" class="text-gray-600 text-sm leading-relaxed">
                {{ cat.description }}
              </p>
            </div>

            <div class="flex gap-1.5 ml-2">
              <button
                @click="openEditCategoryModal(cat)"
                class="px-2 py-1 border border-[#1976d2] text-[#1976d2] hover:bg-[#1976d2] hover:text-white rounded-lg transition-all cursor-pointer text-xs font-medium"
              >
                ✏️ Izmeni
              </button>

              <button
                @click="deleteCategory(cat)"
                class="px-2 py-1 border border-red-500 text-red-600 hover:bg-red-500 hover:text-white rounded-lg transition-all cursor-pointer text-xs font-medium"
              >
                🗑️ Obriši
              </button>
            </div>
          </div>

          <!-- Subcategories Toggle -->
          <div class="flex items-center justify-between pt-2 border-t border-gray-200">
            <button
              @click="toggleCategory(cat.id)"
              class="flex items-center gap-1 text-[#1976d2] hover:text-[#1565c0] font-medium transition cursor-pointer text-xs"
            >
              <span class="text-sm">{{ isCategoryExpanded(cat.id) ? '▼' : '▶' }}</span>
              <span>Podkategorije ({{ getSubcategoriesForCategory(cat.id).length }})</span>
            </button>

            <button
              @click="openAddSubcategoryModal(cat.id)"
              class="px-3 py-1.5 bg-gray-700 hover:bg-gray-800 text-white rounded-lg text-xs font-medium shadow-sm hover:shadow transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span class="text-sm">➕</span>
              <span>Dodaj</span>
            </button>
          </div>
        </div>

        <!-- Subcategories List -->
        <div
          v-if="isCategoryExpanded(cat.id)"
          class="border-t border-gray-200 bg-gray-50 p-3"
        >
          <div v-if="getSubcategoriesForCategory(cat.id).length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div
              v-for="sub in getSubcategoriesForCategory(cat.id)"
              :key="sub.id"
              class="bg-white border border-gray-200 rounded-lg p-2 hover:shadow-md hover:border-[#1976d2] transition-all"
            >
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <h4 class="text-xs font-bold text-gray-900 mb-1 flex items-center gap-1">📂 {{ sub.name }}</h4>
                  <p v-if="sub.description" class="text-gray-600 text-xs leading-relaxed">
                    {{ sub.description }}
                  </p>
                </div>

                <div class="flex gap-1 ml-2">
                  <button
                    @click="openEditSubcategoryModal(sub)"
                    class="px-2 py-1 border border-[#1976d2] text-[#1976d2] hover:bg-[#1976d2] hover:text-white rounded-lg transition-all cursor-pointer text-xs font-medium"
                  >
                    ✏️
                  </button>

                  <button
                    @click="deleteSubcategory(sub)"
                    class="px-2 py-1 border border-red-500 text-red-600 hover:bg-red-500 hover:text-white rounded-lg transition-all cursor-pointer text-xs font-medium"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-8">
            <p class="text-gray-500 text-sm mb-3">Nema podkategorija u ovoj kategoriji</p>
            <button
              @click="openAddSubcategoryModal(cat.id)"
              class="px-2 py-1 bg-[#1976d2] hover:bg-[#1565c0] text-white rounded-md text-xs font-medium shadow-md hover:shadow-lg transition-all cursor-pointer"
            >
              ➕ Dodaj Prvu Podkategoriju
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-10">
      <div class="inline-block bg-gray-100 rounded-full p-4 mb-3">
        <span class="text-2xl">📁</span>
      </div>
      <p class="text-sm font-bold text-gray-600 mb-1">
        Nema kategorija
      </p>
      <p class="text-sm text-gray-500 mb-3">Dodajte prvu kategoriju da započnete!</p>
      <button
        @click="openAddCategoryModal"
        class="px-4 py-2.5 bg-[#1976d2] hover:bg-[#1565c0] text-white rounded-lg font-bold shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer text-xs flex items-center gap-1.5"
      >
        ➕ Dodaj Prvu Kategoriju
      </button>
    </div>

    <!-- Category Modal -->
    <AdminModal
      :show="showCategoryModal"
      :title="isEditingCategory ? 'Izmeni Kategoriju' : 'Nova Kategorija'"
      @close="closeCategoryModal"
    >
      <form @submit.prevent="saveCategory" class="space-y-4">
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Naziv *</label>
          <input
            v-model="categoryForm.name"
            required
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Opis</label>
          <textarea
            v-model="categoryForm.description"
            rows="3"
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm resize-none"
          ></textarea>
        </div>

        <p v-if="categoryError" class="text-red-600 text-sm font-medium px-1">{{ categoryError }}</p>

        <div class="flex justify-end gap-2 pt-1">
          <button
            type="button"
            @click="closeCategoryModal"
            class="px-3 py-2 bg-gray-300 rounded-lg font-semibold hover:bg-gray-400
                   transition cursor-pointer text-xs"
          >
            Otkaži
          </button>

          <button
            type="submit"
            :disabled="savingCategory"
            class="px-3 py-2 bg-[#1976d2] text-white rounded-lg font-semibold shadow
                   hover:bg-[#1565c0] transition cursor-pointer disabled:opacity-60 text-xs"
          >
            {{ savingCategory ? 'Čuvanje...' : 'Sačuvaj' }}
          </button>
        </div>
      </form>
    </AdminModal>

    <!-- Subcategory Modal -->
    <AdminModal
      :show="showSubcategoryModal"
      :title="isEditingSubcategory ? 'Izmeni Podkategoriju' : 'Nova Podkategorija'"
      max-width="max-w-[400px]"
      @close="closeSubcategoryModal"
    >
      <form @submit.prevent="saveSubcategory" class="space-y-4">
        <!-- CATEGORY (hidden when adding from category) -->
        <div v-if="!selectedCategoryForSubcategory || isEditingSubcategory">
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Kategorija *</label>
          <select
            v-model="subcategoryForm.category"
            required
            class="w-full px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-white border border-gray-300 text-xs sm:text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:border-[#1976d2] focus:outline-none transition-all 
                   shadow-sm hover:border-gray-400 cursor-pointer"
          >
            <option value="">Izaberi kategoriju</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>

        <!-- NAME -->
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Naziv *</label>
          <input
            v-model="subcategoryForm.name"
            required
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <!-- DESCRIPTION -->
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Opis</label>
          <textarea
            v-model="subcategoryForm.description"
            rows="3"
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm resize-none"
          ></textarea>
        </div>

        <!-- ERROR -->
        <p v-if="subcategoryError" class="text-red-600 text-xs font-medium px-1">{{ subcategoryError }}</p>

        <!-- BUTTONS -->
        <div class="flex justify-end gap-2 pt-1">
          <button
            type="button"
            @click="closeSubcategoryModal"
            class="px-3 py-2 rounded-lg bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold
                   transition cursor-pointer text-xs"
          >
            Otkaži
          </button>

          <button
            type="submit"
            :disabled="savingSubcategory"
            class="px-3 py-2 rounded-lg bg-[#1976d2] hover:bg-[#1565c0] text-white font-semibold
                   transition cursor-pointer disabled:opacity-60 text-xs"
          >
            {{ savingSubcategory ? "Čuvanje..." : "Sačuvaj" }}
          </button>
        </div>
      </form>
    </AdminModal>

    <!-- Confirm Modal -->
    <ConfirmModal
      :show="showConfirm"
      :message="confirmMessage"
      title="Potvrda"
      confirmText="Obriši"
      cancelText="Odustani"
      @confirm="doConfirm"
      @cancel="closeConfirm"
    />
  </div>
</template>
