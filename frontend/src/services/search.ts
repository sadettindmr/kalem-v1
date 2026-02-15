/**
 * Search Service
 * Makale arama API fonksiyonları
 */

import api from '@/lib/api';
import type { SearchFilters, SearchResponse } from '@/types/api';

/**
 * Makale araması yapar
 * @param filters - Arama filtreleri
 * @returns Arama yaniti (sonuclar + meta istatistikler)
 */
export async function searchPapers(filters: SearchFilters): Promise<SearchResponse> {
  return api.post<never, SearchResponse>('/search', filters);
}
