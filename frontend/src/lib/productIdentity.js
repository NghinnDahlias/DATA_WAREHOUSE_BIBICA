const LABELS = {
  bibica_official_store: 'Shopee · Bibica',
  quasure_specialized_store: 'Shopee · Quasure',
  bibica_tiktok_shop: 'TikTok · Bibica',
}

export function productIdentity(p) {
  return [LABELS[p.store] || p.store, p.variation, p.sku ? `SKU ${p.sku}` : `SP #${p.key} · thiếu mã SKU nguồn`].filter(Boolean).join(' · ')
}
