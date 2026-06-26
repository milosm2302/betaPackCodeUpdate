export function getSellingMode(product) {
  if (!product) return 'piece'
  if (product.selling_mode) return product.selling_mode
  if (product.sold_by_length) return 'length'
  return 'piece'
}

export function isOnRequest(product) {
  return getSellingMode(product) === 'on_request'
}

export function isPackageMode(product) {
  return getSellingMode(product) === 'package'
}

export function isWeightMode(product) {
  return getSellingMode(product) === 'weight'
}

export function isLengthMode(product) {
  return getSellingMode(product) === 'length'
}

export function getPackageSize(product) {
  return parseInt(product?.package_size, 10) || 1
}

export function getQuantityStep(product) {
  const mode = getSellingMode(product)
  if (mode === 'length') return 0.5
  if (mode === 'package') return getPackageSize(product)
  return 1
}

export function getMinQuantity(product) {
  const mode = getSellingMode(product)
  if (mode === 'length') return 0.5
  if (mode === 'package') return getPackageSize(product)
  return 1
}

export function getDefaultQuantity(product) {
  return getMinQuantity(product)
}

export function isValidLengthQuantity(quantity) {
  if (quantity <= 0) return false
  const decimalPart = quantity % 1
  return decimalPart === 0 || decimalPart === 0.5
}

export function isValidQuantity(product, quantity) {
  const mode = getSellingMode(product)
  if (mode === 'length') return isValidLengthQuantity(quantity)
  if (mode === 'package') {
    const pkg = getPackageSize(product)
    return quantity > 0 && quantity % pkg === 0
  }
  return quantity >= 1
}

export function formatQuantityLabel(product, quantity) {
  const mode = getSellingMode(product)
  if (mode === 'package') {
    const pkg = getPackageSize(product)
    const packages = quantity / pkg
    return `${packages} pak. (${quantity} kom.)`
  }
  if (mode === 'weight') return `${quantity} kg`
  if (mode === 'length') return `${quantity} kom.`
  return `${quantity} kom.`
}

export function formatPriceLabel(product, formatPrice) {
  if (isOnRequest(product)) return 'Cena na upit'
  const mode = getSellingMode(product)
  const price = product.current_price ?? product.min_price
  if (price == null) return 'Cena na upit'
  if (mode === 'package') return `${formatPrice(price)} / kom.`
  if (mode === 'weight') return `${formatPrice(price)} / kg`
  if (mode === 'length') return `${formatPrice(price)} / kom.`
  return formatPrice(price)
}

export function getPackageNote(product) {
  if (!isPackageMode(product)) return null
  const pkg = getPackageSize(product)
  return `Pakovanje: ${pkg} komada`
}
