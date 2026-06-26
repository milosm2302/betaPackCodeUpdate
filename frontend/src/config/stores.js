export const STORES = {
  steel: {
    id: 'steel',
    path: '/steel',
    label: 'Beta Pack Gvožđara',
    shortLabel: 'Gvožđara',
    tagline: 'Kovano gvožđe i bravarski materijali',
    description: 'Profili, kutije, firiketi i ukrasni elementi za ograde, kapije i gelendere.',
    icon: '🔩',
    heroImage: '/Betapack-hero-image-optimized.jpg',
    heroTitle: 'Kovano gvožđe i bravarski proizvodi',
    heroSubtitle: 'Širok asortiman kvalitetnih proizvoda - profili, cevi, čelik u traci, ukrasni elementi i dodatna oprema za bravariju',
    accentColor: '#1976d2',
    accentColorDark: '#0d47a1',
    gradientFrom: '#1e88e5',
    gradientTo: '#0d47a1',
    glow: 'rgba(25, 118, 210, 0.45)',
    features: ['Profili i kutije', 'Firiketi i šipke', 'Ukrasni elementi'],
    seoTitle: 'Kovano Gvožđe Beograd | BetaPack Gvožđara',
    seoDescription: 'BetaPack Gvožđara - prodaja bravarskih materijala od kovanog gvožđa u Beogradu.',
  },
  ambalaza: {
    id: 'ambalaza',
    path: '/ambalaza',
    label: 'Beta Pack Ambalaža',
    shortLabel: 'Ambalaža',
    tagline: 'Ambalaža, posude i plastika za vaše poslovanje',
    description: 'Plastične posude, folije, kese i kompletna ambalaža — prodaja na pakovanje, po kilogramu ili po dogovoru.',
    icon: '📦',
    heroImage: '/Betapack-hero-image-optimized.jpg',
    heroTitle: 'Ambalaža, posude i plastika',
    heroSubtitle: 'Plastične posude, folije i kese — prodaja na pakovanje, po kilogramu ili po dogovoru za vaše poslovanje',
    accentColor: '#2e7d32',
    accentColorDark: '#1b5e20',
    gradientFrom: '#43a047',
    gradientTo: '#1b5e20',
    glow: 'rgba(46, 125, 50, 0.45)',
    features: ['Posude i ambalaža', 'Folije i kese', 'Prodaja na pakovanje'],
    seoTitle: 'Ambalaža Beograd | BetaPack Ambalaža',
    seoDescription: 'BetaPack Ambalaža - širok asortiman ambalaže, posuda i plastičnih proizvoda u Beogradu.',
  },
}

export const STORE_LIST = Object.values(STORES)

export function getStoreById(id) {
  return STORES[id] || STORES.steel
}

export function getStoreFromPath(path) {
  if (path.startsWith('/ambalaza')) return STORES.ambalaza
  if (path.startsWith('/steel')) return STORES.steel
  return null
}
