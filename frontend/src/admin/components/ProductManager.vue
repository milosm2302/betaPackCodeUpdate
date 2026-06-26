<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProductStore } from '@/admin/store/products'
import { useProductStore as useUserProductStore } from '@/store/products'
import { useCategoryStore } from '@/admin/store/categories'
import { useSubcategoryStore } from '@/admin/store/subcategories'
import { useAuthStore } from '@/store/auth'
import ProductDetailModal from './ProductDetailModal.vue'
import ProductVariantManager from './ProductVariantManager.vue'
import ProductImageManager from './ProductImageManager.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import AdminModal from './AdminModal.vue'
import { api } from '@/services/api'
import { getImageUrl } from '@/composables/useImageUrl'
import draggable from 'vuedraggable'

const showConfirm = ref(false)
const confirmMessage = ref("")
const confirmAction = ref(null)

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

const doConfirm = () => {
  if (confirmAction.value) confirmAction.value()
  closeConfirm()
}
const emit = defineEmits(['update-count'])
const props = defineProps({ store: { type: String, default: 'steel' } })

const productStore = useProductStore()
const userProductStore = useUserProductStore()
const categoryStore = useCategoryStore()
const subcategoryStore = useSubcategoryStore()

// Detail modal
const showDetailModal = ref(false)
const selectedProduct = ref(null)

// UI
const showModal = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const error = ref('')
const loading = ref(false)

const filterCategory = ref('')
const filterSubcategory = ref('')
const searchQuery = ref('')

// Tab navigation (for editing mode) - each variant has its own tab
const currentTab = ref('basic') // 'basic' or variant ID
const productVariantsForEdit = ref([]) // List of variants for the edited product

// Reset subcategory when category changes
watch(filterCategory, () => {
  filterSubcategory.value = ''
})

// Form
const form = ref({
  id: null,
  name: '',
  description: '',
  price: '',
  category: '',
  subcategory: '',
  on_sale: false,
  sale_price: '',
  featured: false,
  in_stock: true,
  stock_quantity: 0,
  sold_by_length: false,
  length_per_unit: 6.0,
  selling_mode: 'piece',
  package_size: 1,
  dimensions: ''
})

// Stock management
const showStockModal = ref(false)
const stockProduct = ref(null)
const stockQuantityChange = ref(0)
const stockOperation = ref('add') // 'add' or 'subtract'

// Images and variants for new product
const productImages = ref([])
const productVariants = ref([])
const showVariantForm = ref(false)
const editingVariant = ref(null)
const variantForm = ref({
  name: '',
  price: 0,
  on_sale: false,
  sale_price: null,
  sku: '',
  in_stock: true,
  stock_quantity: 0,
  length_per_unit: null
})

// Filtered subcategories
const filteredSubcategories = computed(() => {
  if (!form.value.category) return []
  return subcategoryStore.list.filter(s => s.category === form.value.category)
})

// Filtered products
const filteredProducts = computed(() => {
  let result = [...productStore.list]

  if (filterCategory.value) {
    result = result.filter(p => Number(p.category) === Number(filterCategory.value))
  }

  if (filterSubcategory.value) {
    result = result.filter(p => p.subcategory && Number(p.subcategory) === Number(filterSubcategory.value))
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(
      p =>
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        (p.category_name && p.category_name.toLowerCase().includes(q)) ||
        (p.subcategory_name && p.subcategory_name.toLowerCase().includes(q))
    )
  }

  return result
})

// Drag & Drop state
const isDraggingMode = ref(false)
const draggableProducts = ref([])
const savingOrder = ref(false)

// Toggle dragging mode
const toggleDraggingMode = () => {
  isDraggingMode.value = !isDraggingMode.value
  if (isDraggingMode.value) {
    // Copy products to draggable list
    draggableProducts.value = [...filteredProducts.value]
  }
}

// Cancel dragging
const cancelDragging = () => {
  isDraggingMode.value = false
  draggableProducts.value = []
}

// Save new order
const saveProductOrder = async () => {
  savingOrder.value = true
  try {
    // Prepare orders data
    const orders = draggableProducts.value.map((product, index) => ({
      id: product.id,
      order: index
    }))

    // Send to API
    await api.post('/products/reorder/', { orders })

    // Refresh products
    await productStore.fetch(props.store)
    await userProductStore.fetchProducts()

    isDraggingMode.value = false
    draggableProducts.value = []

    openConfirm('Redosled proizvoda uspešno sačuvan!', null)
  } catch (err) {
    console.error('Error saving order:', err)
    openConfirm('Greška pri čuvanju redosleda!', null)
  } finally {
    savingOrder.value = false
  }
}

// Watch for on_sale changes and ask about featured status
watch(() => form.value?.on_sale, (newVal, oldVal) => {
  // Skip if this is initial load or reset
  if (oldVal === undefined) return

  if (newVal && !oldVal) {
    // Proizvod je stavljen na akciju
    if (!form.value.featured) {
      openConfirm(
        'Proizvod je označen kao "Na akciji". Da li želite da dodate ovaj proizvod u preporučene?',
        () => { form.value.featured = true }
      )
    }
  } else if (!newVal && oldVal) {
    // Proizvod je sklonjen sa akcije
    if (form.value.featured) {
      openConfirm(
        'Proizvod je sklonjen sa akcije. Da li želite da uklonite ovaj proizvod iz preporučenih?',
        () => { form.value.featured = false }
      )
    }
  }
})

// Watch for variant on_sale changes
watch(() => variantForm.value?.on_sale, (newVal, oldVal) => {
  // Skip if this is initial load or reset
  if (oldVal === undefined) return

  if (newVal && !oldVal) {
    // Varijanta je stavljena na akciju
    if (!form.value.featured) {
      openConfirm(
        'Varijanta je označena kao "Na akciji". Da li želite da dodate ovaj proizvod u preporučene?',
        () => { form.value.featured = true }
      )
    }
  } else if (!newVal && oldVal) {
    // Varijanta je sklonjena sa akcije
    // Proveri da li još neka varijanta ima akciju
    const hasOtherSaleVariants = productVariants.value.some(v =>
      v.id !== editingVariant.value?.id && v.on_sale
    )

    if (form.value.featured && !hasOtherSaleVariants && !form.value.on_sale) {
      openConfirm(
        'Varijanta je sklonjena sa akcije. Da li želite da uklonite ovaj proizvod iz preporučenih?',
        () => { form.value.featured = false }
      )
    }
  }
})

// Price formatting
const formatPrice = price =>
  new Intl.NumberFormat('sr-RS', {
    style: 'currency',
    currency: 'RSD'
  }).format(price)

// Modal
const openAddModal = () => {
  if (categoryStore.list.length === 0) {
    openConfirm('Najpre dodaj kategoriju!', null)
    return
  }

  isEditing.value = false
  form.value = {
    id: null,
    name: '',
    description: '',
    price: '',
    category: '',
    subcategory: '',
    on_sale: false,
    sale_price: '',
    featured: false,
    in_stock: true,
    stock_quantity: 0,
    sold_by_length: false,
    length_per_unit: 6.0,
    selling_mode: 'piece',
    package_size: 1,
    dimensions: ''
  }

  // Reset first variant form
  variantForm.value = {
    name: '',
    price: 0,
    on_sale: false,
    sale_price: null,
    sku: '',
    in_stock: true,
    stock_quantity: 0,
    length_per_unit: null
  }

  productImages.value = []
  productVariants.value = []
  showVariantForm.value = false
  editingVariant.value = null

  showModal.value = true
}

const openEditModal = async (product) => {
  isEditing.value = true
  form.value = {
    ...product,
    in_stock: product.in_stock !== undefined ? product.in_stock : true,
    stock_quantity: product.stock_quantity || 0,
    sold_by_length: product.sold_by_length || false,
    length_per_unit: product.length_per_unit || 6.0,
    selling_mode: product.selling_mode || 'piece',
    package_size: product.package_size || 1,
    dimensions: product.dimensions || ''
  }

  // Fetch variants for this product
  try {
    const authStore = useAuthStore()
    const response = await api.get(`product-variants/?product_id=${product.id}`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    productVariantsForEdit.value = response.data
  } catch (err) {
    console.error('Error fetching variants:', err)
    productVariantsForEdit.value = []
  }

  currentTab.value = 'basic' // Reset to basic tab
  showModal.value = true
}

// Stock management
const openStockModal = (product) => {
  stockProduct.value = product
  stockQuantityChange.value = 0
  stockOperation.value = 'add'
  showStockModal.value = true
}

const closeStockModal = () => {
  showStockModal.value = false
  stockProduct.value = null
  stockQuantityChange.value = 0
  stockOperation.value = 'add'
}

const updateStockQuantity = async () => {
  if (!stockProduct.value || stockQuantityChange.value <= 0) return
  
  try {
    const authStore = useAuthStore()
    const authHeaders = { Authorization: `Bearer ${authStore.accessToken}` }
    
    const currentQuantity = stockProduct.value.stock_quantity || 0
    let newQuantity
    if (stockOperation.value === 'add') {
      newQuantity = currentQuantity + stockQuantityChange.value
    } else {
      newQuantity = Math.max(0, currentQuantity - stockQuantityChange.value)
    }
    
    await api.patch(`products/${stockProduct.value.id}/`, {
      stock_quantity: newQuantity,
      in_stock: newQuantity > 0
    }, {
      headers: authHeaders
    })
    
    // Refresh products
    await productStore.fetch(props.store)
    closeStockModal()
  } catch (err) {
    console.error('Error updating stock:', err)
    error.value = err.response?.data?.detail || 'Greška pri ažuriranju količine'
  }
}

const closeModal = () => {
  showModal.value = false
  error.value = ''
  productImages.value = []
  productVariants.value = []
  productVariantsForEdit.value = []
  showVariantForm.value = false
  editingVariant.value = null
}

// Image handling
const handleImageSelect = (event) => {
  const files = Array.from(event.target.files)
  files.forEach(file => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        productImages.value.push({
          file: file,
          preview: e.target.result,
          is_primary: productImages.value.length === 0
        })
      }
      reader.readAsDataURL(file)
    }
  })
  event.target.value = '' // Reset input
}

const removeImage = (index) => {
  productImages.value.splice(index, 1)
  // If we removed the primary image, make the first one primary
  if (productImages.value.length > 0 && !productImages.value.some(img => img.is_primary)) {
    productImages.value[0].is_primary = true
  }
}

const setPrimaryImage = (index) => {
  productImages.value.forEach((img, i) => {
    img.is_primary = i === index
  })
}

// Variant handling
const openVariantForm = (variant = null) => {
  if (variant) {
    editingVariant.value = variant
    variantForm.value = { ...variant }
  } else {
    editingVariant.value = null
    variantForm.value = {
      name: '',
      price: 0,
      on_sale: false,
      sale_price: null,
      sku: '',
      in_stock: true,
      stock_quantity: 0,
      length_per_unit: null
    }
  }
  showVariantForm.value = true
}

const closeVariantForm = () => {
  showVariantForm.value = false
  editingVariant.value = null
  editingExistingVariant.value = null
}

const saveVariant = async () => {
  if (!variantForm.value.name.trim()) {
    openConfirm('Naziv varijante je obavezan!', null)
    return
  }

  // If editing an existing variant (from tabs)
  if (editingExistingVariant.value) {
    try {
      const authStore = useAuthStore()
      const authHeaders = { Authorization: `Bearer ${authStore.accessToken}` }

      await api.patch(`product-variants/${editingExistingVariant.value.id}/`, variantForm.value, {
        headers: authHeaders
      })

      // Refresh data
      await handleTabUpdate()
      closeVariantForm()
    } catch (err) {
      console.error('Error updating variant:', err)
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Greška pri ažuriranju varijante'
      openConfirm(errorMsg, null)
    }
    return
  }

  // For new products (not yet saved)
  if (editingVariant.value) {
    const index = productVariants.value.findIndex(v => v === editingVariant.value)
    if (index !== -1) {
      productVariants.value[index] = { ...variantForm.value }
    }
  } else {
    productVariants.value.push({ ...variantForm.value })
  }
  closeVariantForm()
}

const removeVariant = (variant) => {
  // Proveri da li je ovo poslednja varijanta
  if (productVariants.value.length <= 1) {
    openConfirm('Ne možeš obrisati poslednju varijantu! Proizvod mora imati bar jednu varijantu.', null)
    return
  }

  const index = productVariants.value.indexOf(variant)
  if (index !== -1) {
    productVariants.value.splice(index, 1)
  }
}

// Open edit form for existing variant (from tab)
const editingExistingVariant = ref(null)
const openVariantEditForm = (variant) => {
  editingExistingVariant.value = variant
  variantForm.value = { ...variant }
  showVariantForm.value = true
}

// Save
const saveProduct = async () => {
  saving.value = true
  error.value = ''

  try {
    const isAmbalaza = props.store === 'ambalaza'

    let data
    if (isAmbalaza) {
      // === AMBALAŽA: cena, način prodaje i dimenzije se unose direktno na proizvodu ===
      const onRequest = form.value.selling_mode === 'on_request'

      // Validacija
      if (!isEditing.value && !onRequest && (!form.value.price || form.value.price <= 0)) {
        openConfirm('Cena je obavezna i mora biti veća od 0!', null)
        saving.value = false
        return
      }

      const priceValue = onRequest ? null : parseFloat(form.value.price || 0)

      data = {
        name: form.value.name,
        description: form.value.description,
        price: priceValue,
        category: form.value.category,
        subcategory: form.value.subcategory || null,
        store: 'ambalaza',
        on_sale: form.value.on_sale || false,
        sale_price: form.value.on_sale ? parseFloat(form.value.sale_price || 0) : null,
        featured: form.value.featured || false,
        in_stock: form.value.in_stock !== undefined ? form.value.in_stock : true,
        stock_quantity: form.value.stock_quantity || 0,
        sold_by_length: false,
        selling_mode: form.value.selling_mode || 'piece',
        package_size: form.value.package_size || 1,
        dimensions: form.value.dimensions || ''
      }
    } else {
      // === GVOŽĐARA: originalno ponašanje (cena iz prve varijante) — NE MENJATI ===
      if (!isEditing.value) {
        // Validate first variant price
        if (!variantForm.value.price || variantForm.value.price <= 0) {
          openConfirm('Cena varijante je obavezna i mora biti veća od 0!', null)
          saving.value = false
          return
        }
        // Set default variant name if empty
        if (!variantForm.value.name.trim()) {
          variantForm.value.name = 'Standardna'
        }
      }

      data = {
        name: form.value.name,
        description: form.value.description,
        // Use first variant's price as product price (for backward compatibility)
        price: !isEditing.value ? parseFloat(variantForm.value.price) : parseFloat(form.value.price || 0),
        category: form.value.category,
        subcategory: form.value.subcategory || null,
        // Product-level on_sale and sale_price are deprecated, set to false/null
        on_sale: false,
        sale_price: null,
        featured: form.value.featured || false,
        in_stock: form.value.in_stock !== undefined ? form.value.in_stock : true,
        stock_quantity: form.value.stock_quantity || 0,
        sold_by_length: form.value.sold_by_length || false
      }
    }

    let productId
    const authStore = useAuthStore()
    const authHeaders = { Authorization: `Bearer ${authStore.accessToken}` }

    if (isEditing.value) {
      await productStore.update(form.value.id, data)
      productId = form.value.id
    } else {
      // Create product and get ID from response
      const response = await api.post('products/', data, {
        headers: authHeaders
      })
      productId = response.data.id
      await productStore.fetch(props.store) // Refresh list

      // Gvožđara: kreiraj obaveznu prvu varijantu. Ambalaža nema varijante (cena je na proizvodu).
      try {
        if (!isAmbalaza) {
          await api.post('product-variants/', {
            product: productId,
            ...variantForm.value
          }, {
            headers: authHeaders
          })
        }
      } catch (err) {
        console.error('Error creating first variant:', err)
        const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Greška pri kreiranju varijante.'
        error.value = errorMsg
        throw err
      }
    }

    // Upload images if any
    if (productImages.value.length > 0 && productId) {
      for (let i = 0; i < productImages.value.length; i++) {
        const imageData = productImages.value[i]
        const formData = new FormData()
        formData.append('image', imageData.file)
        formData.append('product', productId)
        formData.append('is_primary', imageData.is_primary)

        try {
          await api.post('product-images/', formData, {
            headers: { 
              ...authHeaders,
              'Content-Type': 'multipart/form-data' 
            }
          })
        } catch (err) {
          console.error('Error uploading image:', err)
          const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Greška pri upload-u slike.'
          error.value = errorMsg
          throw err // Re-throw da se vidi u konzoli
        }
      }
    }

    // Create variants if any
    if (productVariants.value.length > 0 && productId) {
      for (const variant of productVariants.value) {
        try {
          await api.post('product-variants/', {
            product: productId,
            ...variant
          }, {
            headers: authHeaders
          })
        } catch (err) {
          console.error('Error creating variant:', err)
          const errorMsg = err.response?.data?.detail || err.response?.data?.message || JSON.stringify(err.response?.data) || 'Greška pri kreiranju varijante.'
          error.value = errorMsg
          throw err // Re-throw da se vidi u konzoli
        }
      }
    }

    await productStore.fetch(props.store)
    emit('update-count')
    // Osveži proizvode u user store-u da se prikažu nove slike
    await userProductStore.fetchProducts()
    closeModal()
  } catch (err) {
    console.error(err)
    error.value = 'Greška pri čuvanju proizvoda.'
  } finally {
    saving.value = false
  }
}

// Delete
const deleteProduct = (product) => {
  openConfirm(
    `Da li želiš da obrišeš proizvod "${product.name}"?`,
    async () => {
      try {
        await productStore.remove(product.id)
        await productStore.fetch(props.store)
        emit('update-count')
      } catch (err) {
        console.error(err)
        const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Ne može da se obriše proizvod! Proizvod možda se koristi u narudžbinama.'
        openConfirm(errorMsg, null)
      }
    }
  )
}


// Detail modal functions
const openDetailModal = (product) => {
  selectedProduct.value = product
  showDetailModal.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedProduct.value = null
}

const handleDetailUpdate = async () => {
  await productStore.fetch(props.store)
  emit('update-count')
}

// Handle updates from variant/image managers in tabs
const handleTabUpdate = async () => {
  await productStore.fetch(props.store)
  await userProductStore.fetchProducts()

  // Refresh variants list for the current product
  if (form.value.id) {
    try {
      const authStore = useAuthStore()
      const response = await api.get(`product-variants/?product_id=${form.value.id}`, {
        headers: { Authorization: `Bearer ${authStore.accessToken}` }
      })
      productVariantsForEdit.value = response.data
    } catch (err) {
      console.error('Error refreshing variants:', err)
    }
  }

  emit('update-count')
}

// On load
const loadData = async () => {
  loading.value = true
  await categoryStore.fetch(props.store)
  await subcategoryStore.fetch(props.store)
  await productStore.fetch(props.store)
  loading.value = false
}

watch(() => props.store, loadData)

onMounted(loadData)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
        <div>
        <h2 class="text-xs lg:text-sm font-bold text-gray-900 mb-1 flex items-center gap-1">📦 Proizvodi</h2>
        <p class="text-xs text-gray-500 font-medium">Upravljajte proizvodima u vašoj prodavnici</p>
      </div>

      <div class="flex gap-2">
        <button
          @click="toggleDraggingMode"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium shadow-md hover:shadow-lg transition-all cursor-pointer flex items-center gap-1.5"
          :class="{ 'bg-orange-600 hover:bg-orange-700': isDraggingMode }"
        >
          <span class="text-sm">{{ isDraggingMode ? '✖️' : '☰' }}</span>
          <span>{{ isDraggingMode ? 'Otkaži' : 'Promeni redosled' }}</span>
        </button>

        <button
          @click="openAddModal"
          class="px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-md text-xs font-medium shadow-md hover:shadow-lg transition-all cursor-pointer flex items-center gap-1.5"
        >
          <span class="text-sm">➕</span>
          <span>Dodaj Proizvod</span>
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-lg shadow-lg border border-gray-200 p-4 mb-4">
      <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-1.5">
        <span>🔍</span>
        <span>Filteri i pretraga</span>
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <!-- Search -->
        <div>
          <label class="block text-xs font-bold text-gray-700 mb-1">🔎 Pretraga</label>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Pretraži proizvode..."
            class="w-full px-2 py-1.5 border border-gray-300 rounded-lg focus:ring-1 focus:ring-[#1976d2] focus:border-[#1976d2] transition shadow-sm text-sm"
          />
        </div>

        <!-- Category Filter -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Kategorija</label>
          <select
            v-model="filterCategory"
            class="w-full px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-300 rounded-lg 
                   focus:ring-2 focus:ring-[#1976d2] focus:border-[#1976d2] focus:outline-none 
                   transition-all shadow-sm hover:border-gray-400 cursor-pointer 
                   text-xs sm:text-sm bg-white mobile-select"
          >
            <option value="">Sve kategorije</option>
            <option 
              v-for="cat in categoryStore.list" 
              :key="cat.id" 
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </div>

        <!-- Subcategory Filter -->
        <div>
          <label class="block text-xs font-medium text-gray-700 mb-1">Podkategorija</label>
          <select
            v-model="filterSubcategory"
            class="w-full px-2 sm:px-3 py-1.5 sm:py-2 border border-gray-300 rounded-lg 
                   focus:ring-2 focus:ring-[#1976d2] focus:border-[#1976d2] focus:outline-none 
                   transition-all shadow-sm hover:border-gray-400 cursor-pointer 
                   text-xs sm:text-sm bg-white disabled:bg-gray-100 disabled:cursor-not-allowed mobile-select"
            :disabled="!filterCategory"
          >
            <option value="">Sve podkategorije</option>
            <option
              v-for="subcat in subcategoryStore.list.filter(s => s.category == filterCategory)"
              :key="subcat.id"
              :value="subcat.id"
            >
              {{ subcat.name }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#3555e4] mb-2"></div>
      <p class="text-gray-600 text-sm font-semibold">Učitavanje proizvoda...</p>
    </div>

    <!-- Drag & Drop Mode -->
    <div v-else-if="isDraggingMode" class="space-y-4">
      <!-- Instructions -->
      <div class="bg-blue-50 border-2 border-blue-300 rounded-lg p-4">
        <p class="text-sm font-semibold text-blue-900 mb-2">📝 Prevucite proizvode da promenite redosled</p>
        <p class="text-xs text-blue-700">Proizvod na vrhu liste će biti prikazan prvi na sajtu.</p>
      </div>

      <!-- Draggable List -->
      <draggable
        v-model="draggableProducts"
        item-key="id"
        class="space-y-2"
        handle=".drag-handle"
        ghost-class="ghost"
      >
        <template #item="{ element: product }">
          <div class="bg-white border-2 border-gray-300 rounded-lg p-3 flex items-center gap-3 hover:shadow-md transition-all">
            <!-- Drag Handle -->
            <div class="drag-handle cursor-move text-2xl text-gray-400 hover:text-gray-600">
              ☰
            </div>

            <!-- Product Info -->
            <div class="flex-1">
              <h3 class="text-sm font-bold text-gray-900">{{ product.name }}</h3>
              <p class="text-xs text-gray-500">{{ product.category_name }}</p>
            </div>

            <!-- Price -->
            <div class="text-sm font-bold text-green-600">
              {{ formatPrice(product.current_price) }}
            </div>
          </div>
        </template>
      </draggable>

      <!-- Save Button -->
      <div class="flex gap-2 justify-end sticky bottom-4">
        <button
          @click="cancelDragging"
          class="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg text-sm font-bold shadow-lg transition-all cursor-pointer"
        >
          Otkaži
        </button>
        <button
          @click="saveProductOrder"
          :disabled="savingOrder"
          class="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-bold shadow-lg transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ savingOrder ? 'Čuvam...' : '✅ Sačuvaj redosled' }}
        </button>
      </div>
    </div>

    <!-- Normal List -->
    <div
      v-else-if="Array.isArray(filteredProducts) && filteredProducts.length > 0"
      class="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-3"
    >
      <div
        v-for="product in filteredProducts"
        :key="product.id"
        class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-lg hover:border-[#1976d2] transition-all duration-300 transform hover:scale-[1.01] group"
      >
        <!-- Header -->
        <div class="flex justify-between items-start mb-2">
          <div class="flex-1">
            <h3 class="text-[11px] font-bold text-gray-900 mb-0.5 line-clamp-2">{{ product.name }}</h3>
            <div class="flex items-center gap-1.5 mt-1">
              <span class="text-[10px] font-semibold text-[#1976d2]">
                📁 {{ product.category_name || 'Bez kategorije' }}
              </span>
              <span v-if="product.subcategory_name" class="text-[10px] text-gray-500">
                / {{ product.subcategory_name }}
              </span>
            </div>
          </div>

          <span
            v-if="product.on_sale"
            class="px-2 py-1 bg-red-500 text-white rounded text-[10px] font-bold shadow-md whitespace-nowrap flex items-center gap-0.5"
          >
            🔥 AKCIJA
          </span>
        </div>

        <!-- Description -->
        <p class="text-gray-600 text-[10px] mt-2 mb-2 line-clamp-2 leading-relaxed">
          {{ product.description }}
        </p>

        <!-- Price -->
        <div class="mb-2 pb-2 border-b border-gray-200">
          <div class="flex items-center gap-2">
            <span v-if="product.on_sale" class="line-through text-gray-400 text-[10px]">
              {{ formatPrice(product.price) }}
            </span>
            <span class="text-[11px] font-bold text-green-600">
              {{ formatPrice(product.current_price) }}
            </span>
          </div>
        </div>

        <!-- Stock Quantity Display -->
        <div class="mb-1.5 flex items-center justify-between bg-gray-50 p-1.5 rounded border border-gray-200">
          <div class="flex items-center gap-1.5">
            <span class="text-xs">📦</span>
            <div>
              <span class="text-[10px] font-semibold text-gray-600 uppercase">Količina:</span>
              <span
                class="text-[11px] font-bold ml-1.5"
                :class="(product.stock_quantity || 0) > 0 ? 'text-green-600' : 'text-gray-400'"
              >
                {{ (product.stock_quantity !== undefined && product.stock_quantity !== null) ? (product.stock_quantity > 0 ? product.stock_quantity : '0') : '∞ Neograničeno' }}
              </span>
            </div>
          </div>
          <button
            @click.stop="openStockModal(product)"
            class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-[10px] font-medium cursor-pointer shadow-sm hover:shadow transition-all flex items-center gap-0.5"
          >
            <span>➕</span>
            <span>Dodaj</span>
          </button>
        </div>

        <!-- Slike i Varijante Pregled -->
        <div class="mb-1.5 p-1.5 bg-gray-50 rounded border border-gray-200">
          <!-- Slike -->
          <div class="mb-2">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-semibold text-gray-700 uppercase flex items-center gap-0.5">
                🖼️ Slike
              </span>
              <span class="text-[10px] font-bold text-[#1976d2]">
                {{ product.images?.length || 0 }}
              </span>
            </div>
            <div v-if="product.images && product.images.length > 0" class="flex gap-1 overflow-x-auto">
              <div
                v-for="img in product.images.slice(0, 4)"
                :key="img.id"
                class="w-8 h-8 rounded overflow-hidden flex-shrink-0 border border-gray-300"
              >
                <img
                  :src="getImageUrl(img.image)"
                  :alt="product.name"
                  class="w-full h-full object-contain bg-white"
                />
              </div>
              <div v-if="product.images.length > 4" class="w-8 h-8 rounded bg-gray-200 flex items-center justify-center text-[10px] font-bold text-gray-600">
                +{{ product.images.length - 4 }}
              </div>
            </div>
            <p v-else class="text-[10px] text-gray-400">Nema slika</p>
          </div>

          <!-- Varijante -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-semibold text-gray-700 uppercase flex items-center gap-0.5">
                📐 Varijante
              </span>
              <span class="text-[10px] font-bold text-[#1976d2]">
                {{ product.variants?.length || 0 }}
              </span>
            </div>
            <div v-if="product.variants && product.variants.length > 0" class="flex flex-wrap gap-0.5">
              <span
                v-for="variant in product.variants.slice(0, 3)"
                :key="variant.id"
                class="px-1.5 py-0.5 bg-white border border-gray-300 rounded text-[10px] font-medium text-gray-700"
              >
                {{ variant.name }}
              </span>
              <span v-if="product.variants.length > 3" class="px-1.5 py-0.5 bg-gray-200 rounded text-[10px] font-bold text-gray-600">
                +{{ product.variants.length - 3 }}
              </span>
            </div>
            <p v-else class="text-[10px] text-gray-400">Nema varijanti</p>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-1.5 mt-2">
          <button
            @click="openDetailModal(product)"
            class="px-2 py-1 bg-gray-500 hover:bg-gray-600 text-white rounded text-[10px] font-medium cursor-pointer shadow-sm hover:shadow transition-all flex items-center justify-center gap-1"
          >
            <span class="text-xs">🎨</span>
            <span>Varijante/Slike</span>
          </button>

          <button
            @click="openEditModal(product)"
            class="px-2 py-1 bg-[#1976d2] hover:bg-[#1565c0] text-white rounded text-[10px] font-medium cursor-pointer shadow-sm hover:shadow transition-all flex items-center gap-1"
          >
            <span>✏️</span>
            <span>Izmeni</span>
          </button>

          <button
            @click="deleteProduct(product)"
            class="px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-[10px] font-medium cursor-pointer shadow-sm hover:shadow transition-all flex items-center gap-1"
          >
            <span>🗑️</span>
            <span>Obriši</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="py-20 text-center">
      <div class="inline-block bg-gray-100 rounded-full p-8 mb-4">
        <span class="text-4xl">📦</span>
      </div>
      <p class="text-base font-bold text-gray-600 mb-2">
        Nema proizvoda
      </p>
      <p class="text-sm text-gray-500 mb-3">Dodajte prvi proizvod da započnete!</p>
      <button
        @click="openAddModal"
        class="px-4 py-2.5 bg-[#1976d2] hover:bg-[#1565c0] text-white rounded-lg font-bold shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer text-xs flex items-center gap-1.5"
      >
        ➕ Dodaj Prvi Proizvod
      </button>
    </div>

    <!-- MODAL -->
    <AdminModal
      :show="showModal"
      :title="isEditing ? 'Izmeni Proizvod' : 'Novi Proizvod'"
      :max-width="isEditing ? 'max-w-[600px]' : 'max-w-[480px]'"
      @close="closeModal"
    >
      <!-- Tab Navigation (only when editing gvožđara - ambalaža nema varijante) -->
      <div v-if="isEditing && props.store === 'steel'" class="flex gap-1.5 mb-3 border-b border-gray-200 overflow-x-auto">
        <button
          type="button"
          @click="currentTab = 'basic'"
          :class="currentTab === 'basic'
            ? 'border-b-2 border-[#1976d2] text-[#1976d2] font-bold'
            : 'text-gray-600 hover:text-gray-800'"
          class="px-3 py-2 transition-all cursor-pointer whitespace-nowrap flex-shrink-0 text-sm"
        >
          📝 Osnovni podaci
        </button>

        <!-- Tab for each variant -->
        <button
          v-for="variant in productVariantsForEdit"
          :key="variant.id"
          type="button"
          @click="currentTab = variant.id"
          :class="currentTab === variant.id
            ? 'border-b-2 border-[#1976d2] text-[#1976d2] font-bold'
            : 'text-gray-600 hover:text-gray-800'"
          class="px-3 py-2 transition-all cursor-pointer whitespace-nowrap flex-shrink-0 text-sm"
        >
          📐 {{ variant.name }}
        </button>

        <button
          type="button"
          @click="currentTab = 'add-variant'"
          :class="currentTab === 'add-variant'
            ? 'border-b-2 border-green-600 text-green-600 font-bold'
            : 'text-green-600 hover:text-green-700'"
          class="px-3 py-2 transition-all cursor-pointer whitespace-nowrap flex-shrink-0 text-sm"
        >
          ➕ Nova varijanta
        </button>
      </div>

      <!-- Basic Info Tab (or full form for new products) -->
      <form v-show="!isEditing || currentTab === 'basic'" @submit.prevent="saveProduct" class="space-y-4">
        <!-- NAME -->
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Naziv *</label>
          <input
            v-model="form.name"
            required
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <!-- DESCRIPTION -->
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Opis *</label>
          <textarea
            v-model="form.description"
            rows="4"
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs 
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition resize-none shadow-sm"
          ></textarea>
        </div>

        <!-- CATEGORY -->
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Kategorija *</label>
          <select
            v-model="form.category"
            required
            class="w-full px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-white border border-gray-300 text-xs sm:text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:border-[#1976d2] focus:outline-none transition-all 
                   shadow-sm hover:border-gray-400 cursor-pointer"
          >
            <option value="">Izaberi kategoriju</option>
            <option v-for="c in categoryStore.list" :value="c.id" :key="c.id">
              {{ c.name }}
            </option>
          </select>
        </div>

        <!-- SUBCATEGORY -->
        <div>
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Podkategorija</label>
          <select
            v-model="form.subcategory"
            class="w-full px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-white border border-gray-300 text-xs sm:text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:border-[#1976d2] focus:outline-none transition-all 
                   shadow-sm hover:border-gray-400 cursor-pointer"
          >
            <option value="">Bez podkategorije</option>
            <option
              v-for="s in filteredSubcategories"
              :value="s.id"
              :key="s.id"
            >
              {{ s.name }}
            </option>
          </select>
        </div>

        <!-- Featured -->
        <label class="flex items-center gap-2 mt-2 cursor-pointer px-1">
          <input v-model="form.featured" type="checkbox" class="cursor-pointer" />
          <span class="text-gray-800 text-xs font-medium cursor-pointer">Preporučeni proizvod</span>
        </label>

        <!-- Dimensions -->
        <div v-if="props.store === 'ambalaza'">
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Dimenzije</label>
          <input v-model="form.dimensions" type="text" placeholder="npr. 500ml, 20x30cm"
            class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs focus:ring-2 focus:ring-[#1976d2] focus:outline-none" />
        </div>

        <!-- Selling mode (ambalaza) -->
        <div v-if="props.store === 'ambalaza'" class="mt-2 bg-green-50 p-3 rounded-lg">
          <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Način prodaje</label>
          <select v-model="form.selling_mode"
            class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-200 text-xs focus:ring-2 focus:ring-[#1976d2] focus:outline-none cursor-pointer">
            <option value="piece">Po komadu</option>
            <option value="package">Po pakovanju</option>
            <option value="weight">Po kilogramu</option>
            <option value="on_request">Na upit (bez cene)</option>
          </select>
          <div v-if="form.selling_mode === 'package'" class="mt-2">
            <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Komada u pakovanju</label>
            <input v-model.number="form.package_size" type="number" min="1"
              class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-200 text-xs focus:ring-2 focus:ring-[#1976d2] focus:outline-none" />
            <p class="text-[10px] text-gray-600 mt-1 px-1">Cena se unosi po komadu. U korpi se dodaje ceo paket.</p>
          </div>

          <!-- Cena (ambalaza) -->
          <div v-if="form.selling_mode !== 'on_request'" class="mt-3">
            <label class="block mb-1 text-xs font-medium text-gray-800 px-1">
              Cena (RSD) *
              <span v-if="form.selling_mode === 'package'" class="text-gray-500 font-normal">— po komadu</span>
              <span v-else-if="form.selling_mode === 'weight'" class="text-gray-500 font-normal">— po kilogramu</span>
            </label>
            <input v-model.number="form.price" type="number" step="0.01" min="0"
              class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-200 text-xs focus:ring-2 focus:ring-[#1976d2] focus:outline-none" />

            <label class="flex items-center gap-2 mt-2 cursor-pointer px-1">
              <input v-model="form.on_sale" type="checkbox" class="cursor-pointer" />
              <span class="text-gray-800 text-xs font-medium cursor-pointer">Na akciji</span>
            </label>
            <input v-if="form.on_sale" v-model.number="form.sale_price" type="number" step="0.01" min="0"
              placeholder="Akcijska cena (RSD)"
              class="w-full mt-1 px-2.5 py-1.5 rounded-lg bg-red-50 border border-red-200 text-xs focus:ring-2 focus:ring-red-400 focus:outline-none" />
          </div>
          <p v-else class="mt-3 text-[10px] text-orange-600 font-semibold px-1">
            ℹ️ Proizvod „na upit" — cena se ne prikazuje, kupac šalje upit.
          </p>
        </div>

        <!-- Sold by Length (steel) -->
        <div v-if="props.store === 'steel'" class="mt-2 bg-blue-50 p-3 rounded-lg">
          <label class="flex items-center gap-2 cursor-pointer px-1">
            <input v-model="form.sold_by_length" type="checkbox" class="cursor-pointer" />
            <span class="text-gray-800 text-xs font-medium cursor-pointer">Custom dužina proizvoda (prodaja po metraži)</span>
          </label>
          <p class="text-[10px] text-gray-600 mt-1 px-1">Proizvod se prodaje po metraži. Dozvoljene su decimalne vrednosti (0.5, 1, 1.5, itd.). Dužinu unesite u varijantama ispod.</p>
        </div>

        <!-- Stock Management -->
        <div class="border-t pt-4 mt-4">
          <label class="flex items-center gap-2 mb-3 cursor-pointer px-1">
            <input v-model="form.in_stock" type="checkbox" class="cursor-pointer" />
            <span class="text-gray-800 text-xs font-medium cursor-pointer">Proizvod je na stanju</span>
          </label>

          <div>
            <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Količina na stanju (opciono)</label>
            <input
              v-model.number="form.stock_quantity"
              type="number"
              min="0"
              placeholder="0 = neograničeno"
              class="w-full px-2.5 py-1.5 rounded-lg bg-gray-100 border border-gray-200 text-xs
                     focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
            />
            <p class="text-[10px] text-gray-500 mt-0.5 px-1">Ostavite 0 za neograničenu količinu</p>
          </div>
        </div>

        <!-- PRVA VARIJANTA (obavezno za nove proizvode - samo gvožđara) -->
        <div v-if="!isEditing && props.store === 'steel'" class="border-t pt-5 mt-5 bg-blue-50 p-4 rounded-lg">
          <h4 class="font-semibold text-xs mb-1.5 text-gray-800 px-1">📐 Prva varijanta (obavezno)</h4>
          <p class="text-[10px] text-gray-600 mb-3 px-1">
            Svaki proizvod mora imati bar jednu varijantu. Ako proizvod nema različitih dimenzija, samo unesi cenu.
          </p>

          <div class="space-y-3">
            <div>
              <label class="block mb-1 text-xs font-medium text-gray-800 px-1">
                Naziv dimenzije (opciono)
              </label>
              <input
                v-model="variantForm.name"
                placeholder="npr. 45×45mm ili ostavi prazno za standardnu varijantu"
                class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-300 text-xs
                       focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
              />
              <p class="text-[10px] text-gray-500 mt-0.5 px-1">Ako proizvod nema dimenzije, ostavi prazno ili unesi "Standardna"</p>
            </div>

            <div>
              <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Cena (RSD) *</label>
              <input
                v-model.number="variantForm.price"
                type="number"
                step="0.01"
                required
                class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-300 text-xs
                       focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
              />
            </div>

            <div>
              <label class="block mb-1 text-xs font-medium text-gray-800 px-1">SKU / Šifra (opciono)</label>
              <input
                v-model="variantForm.sku"
                placeholder="npr. TACNA-45"
                class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-300 text-xs
                       focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
              />
            </div>

            <div class="flex items-center gap-2 bg-yellow-50 p-2 rounded-lg">
              <input
                v-model="variantForm.on_sale"
                type="checkbox"
                id="first-variant-on-sale"
                class="cursor-pointer"
              />
              <label for="first-variant-on-sale" class="text-gray-800 text-xs font-medium cursor-pointer px-1">
                Stavi na akciju
              </label>
            </div>

            <div v-if="variantForm.on_sale">
              <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Akcijska cena (RSD) *</label>
              <input
                v-model.number="variantForm.sale_price"
                type="number"
                step="0.01"
                :required="variantForm.on_sale"
                class="w-full px-2.5 py-1.5 rounded-lg bg-red-50 border border-red-300 text-xs
                       focus:ring-2 focus:ring-red-400 focus:outline-none transition shadow-sm"
              />
              <p class="text-[10px] text-red-600 mt-0.5 px-1">Akcijska cena mora biti niža od osnovne cene</p>
            </div>

            <div>
              <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Količina na stanju</label>
              <input
                v-model.number="variantForm.stock_quantity"
                type="number"
                min="0"
                class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-300 text-xs
                       focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
              />
            </div>

            <div class="flex items-center gap-2">
              <input
                v-model="variantForm.in_stock"
                type="checkbox"
                id="first-variant-in-stock"
                class="cursor-pointer"
              />
              <label for="first-variant-in-stock" class="text-gray-800 text-xs font-medium cursor-pointer px-1">
                Na stanju
              </label>
            </div>

            <!-- Length per unit (only if product is sold by length) -->
            <div v-if="form.sold_by_length" class="bg-blue-50 p-2 rounded-lg border border-blue-200 mt-2">
              <label class="block mb-1 text-xs font-medium text-gray-800 px-1">Dužina 1 komada (u metrima) - Opciono</label>
              <input
                v-model.number="variantForm.length_per_unit"
                type="number"
                step="0.1"
                min="0.1"
                placeholder="npr. 4.0 ili 6.0"
                class="w-full px-2.5 py-1.5 rounded-lg bg-white border border-gray-300 text-xs
                       focus:ring-2 focus:ring-blue-400 focus:outline-none transition shadow-sm"
              />
              <p class="text-[10px] text-gray-600 mt-0.5 px-1">
                Unesite dužinu 1 komada za ovu varijantu (npr. 4.0 za 4m, 6.0 za 6m). Ako ostavite prazno, koristiće se default vrednost od 6m.
              </p>
            </div>
          </div>
        </div>

        <!-- SLIKE PROIZVODA (samo za nove proizvode) -->
        <div v-if="!isEditing" class="border-t pt-5 mt-5">
          <h4 class="font-semibold text-sm mb-3 text-gray-800 px-1">Slike proizvoda</h4>
          
          <!-- Upload -->
          <div class="mb-3">
            <input
              type="file"
              @change="handleImageSelect"
              accept="image/*"
              multiple
              class="w-full px-3 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm cursor-pointer"
            />
            <p class="text-xs text-gray-500 mt-1 px-1">Možete odabrati više slika odjednom</p>
          </div>

          <!-- Preview slika -->
          <div v-if="productImages.length > 0" class="grid grid-cols-4 gap-1.5 mb-2">
            <div
              v-for="(img, index) in productImages"
              :key="index"
              class="relative border rounded overflow-hidden group"
            >
              <img
                :src="img.preview"
                :alt="`Preview ${index + 1}`"
                class="w-full h-14 object-cover"
              />
              
              <div v-if="img.is_primary" class="absolute top-0.5 left-0.5 bg-green-500 text-white px-1 py-0.5 text-[10px] rounded">
                Glavna
              </div>

              <div class="absolute bottom-0 left-0 right-0 bg-black/70 p-0.5 flex gap-0.5 opacity-0 group-hover:opacity-100 transition">
                <button
                  v-if="!img.is_primary"
                  @click="setPrimaryImage(index)"
                  type="button"
                  class="flex-1 px-1 py-0.5 bg-green-600 text-white text-[10px] rounded cursor-pointer"
                >
                  Glavna
                </button>
                <button
                  @click="removeImage(index)"
                  type="button"
                  class="px-1 py-0.5 bg-red-600 text-white text-[10px] rounded cursor-pointer"
                >
                  Obriši
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- VARIJANTE (samo za nove proizvode) -->
        <div v-if="!isEditing" class="border-t pt-5 mt-5">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium text-sm text-gray-800 px-1">Varijante (Dimenzije)</h4>
            <button
              @click="openVariantForm()"
              type="button"
              class="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium cursor-pointer flex items-center gap-1.5"
            >
              <span>➕</span>
              <span>Dodaj varijantu</span>
            </button>
          </div>

          <!-- Lista varijanti -->
          <div v-if="productVariants.length > 0" class="space-y-1.5 mb-2">
            <div
              v-for="(variant, index) in productVariants"
              :key="index"
              class="flex items-center justify-between border rounded-lg p-1.5 bg-gray-50"
            >
              <div class="flex-1 min-w-0">
                <p class="font-medium text-xs text-gray-900">{{ variant.name || 'Standardna' }}</p>
                <p class="text-[11px] text-gray-600">
                  SKU: {{ variant.sku || 'N/A' }} |
                  <span v-if="variant.on_sale" class="text-red-600">
                    <span class="line-through text-gray-400">{{ variant.price }} RSD</span>
                    <span class="ml-1 font-bold">{{ variant.sale_price }} RSD</span>
                    <span class="ml-1 text-[9px] bg-red-100 text-red-800 px-0.5 rounded">AKCIJA</span>
                  </span>
                  <span v-else class="text-green-600 font-medium">{{ variant.price }} RSD</span>
                </p>
                <p class="text-[11px] mt-0.5" :class="variant.in_stock ? 'text-green-600' : 'text-red-600'">
                  {{ variant.in_stock ? `Na stanju: ${variant.stock_quantity}` : 'Nije na stanju' }}
                </p>
              </div>

              <div class="flex gap-1 ml-2">
                <button
                  @click="openVariantForm(variant)"
                  type="button"
                  class="px-2 py-1 bg-[#1976d2] text-white rounded text-xs font-medium cursor-pointer flex items-center gap-1"
                >
                  <span>✏️</span>
                  <span>Izmeni</span>
                </button>
                <button
                  @click="removeVariant(variant)"
                  type="button"
                  :disabled="productVariants.length <= 1"
                  :class="productVariants.length <= 1
                    ? 'px-2 py-1 bg-gray-400 text-white rounded text-xs font-medium cursor-not-allowed opacity-50 flex items-center gap-1'
                    : 'px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-xs font-medium cursor-pointer flex items-center gap-1'"
                  :title="productVariants.length <= 1 ? 'Ne možeš obrisati poslednju varijantu!' : 'Obriši varijantu'"
                >
                  <span>🗑️</span>
                  <span>Obriši</span>
                </button>
              </div>
            </div>
          </div>

          <p v-if="productVariants.length === 0" class="text-gray-400 text-sm text-center py-4">
            Nema varijanti. Dodaj dimenzije/varijacije proizvoda.
          </p>
        </div>

        <!-- ERROR -->
        <p v-if="error" class="text-red-600 font-semibold">{{ error }}</p>

        <!-- BUTTONS (only show in basic tab when editing, always show for new products) -->
        <div v-if="!isEditing || currentTab === 'basic'" class="flex justify-end gap-2 pt-1">
          <button
            type="button"
            @click="closeModal"
            class="px-3 py-2 bg-gray-300 rounded-lg font-semibold hover:bg-gray-400 transition cursor-pointer text-xs"
          >
            Otkaži
          </button>

          <button
            type="submit"
            :disabled="saving"
            class="px-3 py-2 bg-[#1976d2] text-white rounded-lg font-semibold shadow
                   hover:bg-[#1565c0] transition cursor-pointer disabled:opacity-60 text-xs"
          >
            {{ saving ? "Čuvanje..." : "Sačuvaj" }}
          </button>
        </div>
      </form>

      <!-- Individual Variant Tab Content -->
      <div
        v-for="variant in productVariantsForEdit"
        :key="`tab-${variant.id}`"
        v-show="isEditing && currentTab === variant.id"
        class="space-y-4"
      >
        <h3 class="text-base font-bold text-gray-900 mb-3 px-1">Varijanta: {{ variant.name }}</h3>

        <!-- Variant Details Form -->
        <div class="space-y-3 bg-gray-50 p-4 rounded-lg mb-4">
          <h4 class="font-semibold text-sm text-gray-800 mb-3 px-1">Informacije o varijanti</h4>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5 px-1">Naziv (dimenzije)</label>
              <p class="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900">{{ variant.name }}</p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5 px-1">SKU</label>
              <p class="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900">{{ variant.sku || 'N/A' }}</p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5 px-1">Osnovna cena</label>
              <p class="px-3 py-2 bg-white border border-gray-300 rounded-lg text-base text-gray-900 font-semibold">{{ variant.price }} RSD</p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5 px-1">Status akcije</label>
              <p class="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm" :class="variant.on_sale ? 'text-red-600 font-bold' : 'text-gray-600'">
                {{ variant.on_sale ? `Akcija: ${variant.sale_price} RSD` : 'Nije na akciji' }}
              </p>
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1.5 px-1">Količina na stanju</label>
              <p class="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-semibold" :class="variant.in_stock ? 'text-green-600' : 'text-red-600'">
                {{ variant.in_stock ? variant.stock_quantity : 'Nije na stanju' }}
              </p>
            </div>

            <div class="flex items-end">
              <button
                @click="openVariantEditForm(variant)"
                type="button"
                class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium cursor-pointer transition-all w-full text-sm flex items-center gap-1.5 justify-center"
              >
                <span>✏️</span>
                <span>Izmeni varijantu</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Images for this product -->
        <div class="bg-gray-50 p-3 rounded-lg">
          <h4 class="font-semibold text-xs text-gray-800 mb-2 px-1">Slike proizvoda</h4>
          <p class="text-xs text-gray-600 mb-2 px-1">Slike se primenjuju na ceo proizvod (sve varijante dele iste slike)</p>
          <ProductImageManager
            :product-id="form.id"
            @updated="handleTabUpdate"
          />
        </div>
      </div>

      <!-- Add New Variant Tab Content -->
      <div v-if="isEditing && currentTab === 'add-variant'" class="space-y-4">
        <h3 class="text-sm font-bold text-gray-900 mb-3 px-1">Dodaj novu varijantu</h3>
        <ProductVariantManager
          :product-id="form.id"
          @updated="handleTabUpdate"
        />
      </div>
    </AdminModal>


    <!-- Detail Modal za varijante/slike -->
    <ProductDetailModal
      :show="showDetailModal"
      :product="selectedProduct"
      @close="closeDetailModal"
      @updated="handleDetailUpdate"
    />
    <!-- Variant Form Modal -->
    <AdminModal
      :show="showVariantForm"
      :title="(editingVariant || editingExistingVariant) ? 'Izmeni varijantu' : 'Nova varijanta'"
      max-width="max-w-md"
      z-index="z-[2000]"
      @close="closeVariantForm"
    >
      <form @submit.prevent="saveVariant" class="space-y-2">
        <div>
          <label class="block text-xs font-medium mb-1.5 text-gray-800 px-1">Naziv (dimenzije) *</label>
          <input
            v-model="variantForm.name"
            required
            placeholder="npr. 180×135×18mm"
            class="w-full px-3 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <div>
          <label class="block text-xs font-medium mb-1.5 text-gray-800 px-1">SKU (šifra)</label>
          <input
            v-model="variantForm.sku"
            placeholder="npr. TACNA-70-180"
            class="w-full px-3 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <div>
          <label class="block text-xs font-medium mb-1.5 text-gray-800 px-1">Osnovna cena (RSD) *</label>
          <input
            v-model.number="variantForm.price"
            type="number"
            step="0.01"
            required
            class="w-full px-3 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <div class="flex items-center gap-2 bg-yellow-50 p-3 rounded-lg">
          <input
            v-model="variantForm.on_sale"
            type="checkbox"
            id="product-variant-on-sale"
            class="cursor-pointer"
          />
          <label for="product-variant-on-sale" class="text-gray-800 text-xs font-medium cursor-pointer px-1">Stavi na akciju</label>
        </div>

        <div v-if="variantForm.on_sale">
          <label class="block text-xs font-medium mb-1.5 text-gray-800 px-1">Akcijska cena (RSD) *</label>
          <input
            v-model.number="variantForm.sale_price"
            type="number"
            step="0.01"
            :required="variantForm.on_sale"
            class="w-full px-3 py-2 rounded-lg bg-red-50 border border-red-300 text-sm
                   focus:ring-2 focus:ring-red-400 focus:outline-none transition shadow-sm"
          />
          <p class="text-xs text-red-600 mt-1 px-1">Akcijska cena mora biti niža od osnovne cene</p>
        </div>

        <div>
          <label class="block text-xs font-medium mb-1.5 text-gray-800 px-1">Količina na stanju</label>
          <input
            v-model.number="variantForm.stock_quantity"
            type="number"
            class="w-full px-3 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
        </div>

        <div class="flex items-center gap-2">
          <input
            v-model="variantForm.in_stock"
            type="checkbox"
            id="variant-in-stock-form"
            class="cursor-pointer"
          />
          <label for="variant-in-stock-form" class="text-gray-800 text-xs font-medium cursor-pointer px-1">Na stanju</label>
        </div>

        <!-- Length per unit (only if product is sold by length) -->
        <div v-if="form.sold_by_length" class="bg-blue-50 p-3 rounded-lg border border-blue-200">
          <label class="block text-xs font-medium mb-1.5 text-gray-800 px-1">Dužina 1 komada (u metrima) - Opciono</label>
          <input
            v-model.number="variantForm.length_per_unit"
            type="number"
            step="0.1"
            min="0.1"
            placeholder="npr. 4.0 ili 6.0"
            class="w-full px-3 py-2 rounded-lg bg-white border border-gray-300 text-sm
                   focus:ring-2 focus:ring-blue-400 focus:outline-none transition shadow-sm"
          />
          <p class="text-xs text-gray-600 mt-1 px-1">
            Unesite dužinu 1 komada za ovu varijantu (npr. 4.0 za 4m, 6.0 za 6m). 
            Ako ostavite prazno, koristiće se default vrednost od 6m.
          </p>
        </div>

        <div class="flex justify-end gap-2 pt-1">
          <button
            type="button"
            @click="closeVariantForm"
            class="px-3 py-2 bg-gray-300 rounded-lg font-semibold hover:bg-gray-400
                   transition cursor-pointer text-xs"
          >
            Otkaži
          </button>
          <button
            type="submit"
            class="px-3 py-2 bg-[#1976d2] text-white rounded-lg font-semibold shadow
                   hover:bg-[#1565c0] transition cursor-pointer text-xs"
          >
            Sačuvaj
          </button>
        </div>
      </form>
    </AdminModal>

    <ConfirmModal
      :show="showConfirm"
      :message="confirmMessage"
      title="Potvrda"
      :confirmText="confirmAction ? 'Potvrdi' : 'U redu'"
      :cancelText="confirmAction ? 'Odustani' : null"
      @confirm="doConfirm"
      @cancel="closeConfirm"
    />

    <!-- Stock Management Modal -->
    <AdminModal
      :show="showStockModal"
      title="Upravljanje količinom na stanju"
      max-width="max-w-md"
      @close="closeStockModal"
    >
      <div v-if="stockProduct" class="space-y-4">
        <div class="bg-gray-50 p-3 rounded-lg">
          <p class="text-gray-700 mb-2 text-sm">
            <span class="font-semibold px-1">Proizvod:</span> 
            <span class="px-1">{{ stockProduct.name }}</span>
          </p>
          <p class="text-gray-700 text-sm">
            <span class="font-semibold px-1">Trenutna količina:</span> 
            <span class="text-lg font-bold text-green-600 ml-2 px-1">
              {{ stockProduct.stock_quantity || 0 }}
            </span>
          </p>
        </div>

        <!-- Operation Selection -->
        <div>
          <label class="block mb-2 text-xs font-medium text-gray-800 px-1">Operacija</label>
          <div class="flex gap-2">
            <button
              @click="stockOperation = 'add'"
              :class="stockOperation === 'add' 
                ? 'bg-green-600 text-white shadow-md' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
              class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer"
            >
              ➕ Dodaj
            </button>
            <button
              @click="stockOperation = 'subtract'"
              :class="stockOperation === 'subtract' 
                ? 'bg-red-600 text-white shadow-md' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
              class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer"
            >
              ➖ Smanji
            </button>
          </div>
        </div>

        <div>
          <label class="block mb-1.5 text-xs font-medium text-gray-800 px-1">
            Količina za {{ stockOperation === 'add' ? 'dodavanje' : 'smanjenje' }} *
          </label>
          <input
            v-model.number="stockQuantityChange"
            type="number"
            min="1"
            placeholder="Unesite količinu"
            class="w-full px-3 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm
                   focus:ring-2 focus:ring-[#1976d2] focus:outline-none transition shadow-sm"
          />
          <p v-if="stockOperation === 'subtract' && stockProduct.stock_quantity" class="text-xs text-gray-500 mt-1 px-1">
            Nova količina: {{ Math.max(0, (stockProduct.stock_quantity || 0) - (stockQuantityChange || 0)) }}
          </p>
        </div>

        <div class="flex gap-2 pt-1">
          <button
            @click="updateStockQuantity"
            :disabled="!stockQuantityChange || stockQuantityChange <= 0"
            :class="stockOperation === 'add' 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-red-600 hover:bg-red-700'"
            class="flex-1 px-3 py-2 disabled:bg-gray-400 
                   text-white rounded-lg text-sm font-semibold transition-all cursor-pointer shadow-md hover:shadow-lg"
          >
            {{ stockOperation === 'add' ? 'Dodaj količinu' : 'Smanji količinu' }}
          </button>
          <button
            @click="closeStockModal"
            class="px-3 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 rounded-lg text-sm font-semibold transition-all cursor-pointer"
          >
            Odustani
          </button>
        </div>
      </div>
    </AdminModal>
  </div>
</template>

<style scoped>
.ghost {
  opacity: 0.5;
  background: #e3f2fd;
  border: 2px dashed #1976d2;
}
</style>
