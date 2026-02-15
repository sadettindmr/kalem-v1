/**
 * Library Service
 * Kütüphane API fonksiyonları
 */

import api from '@/lib/api';
import type { LibraryListResponse, IngestRequest, IngestResponse, BulkIngestRequest, BulkIngestResponse, CheckLibraryResponse } from '@/types/api';

interface LibraryParams {
  page?: number;
  limit?: number;
  tag?: string;
  status?: string;
  min_citations?: number;
  year_start?: number;
  year_end?: number;
  search?: string;
}

/**
 * Kütüphane listesini getirir
 */
export async function fetchLibrary(params: LibraryParams = {}): Promise<LibraryListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.tag) searchParams.set('tag', params.tag);
  if (params.status) searchParams.set('status', params.status);
  if (params.min_citations != null) searchParams.set('min_citations', String(params.min_citations));
  if (params.year_start != null) searchParams.set('year_start', String(params.year_start));
  if (params.year_end != null) searchParams.set('year_end', String(params.year_end));
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  return api.get<never, LibraryListResponse>(`/library${query ? `?${query}` : ''}`);
}

/**
 * Makaleyi kütüphaneye ekler
 */
export async function ingestPaper(data: IngestRequest): Promise<IngestResponse> {
  return api.post<never, IngestResponse>('/library/ingest', data);
}

/**
 * Birden fazla makaleyi toplu olarak kutuphanye ekler
 */
export async function bulkIngestPapers(data: BulkIngestRequest): Promise<BulkIngestResponse> {
  return api.post<never, BulkIngestResponse>('/library/ingest/bulk', data);
}

/**
 * Verilen external_id'lerin kutuphanede kayitli olup olmadigini kontrol eder
 */
export async function checkLibraryPapers(external_ids: string[]): Promise<CheckLibraryResponse> {
  return api.post<never, CheckLibraryResponse>('/library/check', { external_ids });
}

/**
 * Tamamlanmamis tum indirmeleri tekrar kuyruga ekler
 */
export async function retryDownloads(scope: 'stuck' | 'all' = 'stuck'): Promise<{ status: string; message: string }> {
  return api.post<never, { status: string; message: string }>(`/library/retry-downloads?scope=${scope}`);
}

/**
 * Indirme durumu istatistiklerini getirir
 */
export interface DownloadStats {
  pending: number;
  downloading: number;
  completed: number;
  failed: number;
  total: number;
  failed_entries: Array<{
    id: number;
    paper_id: number;
    title: string;
    updated_at: string | null;
  }>;
}

export async function fetchDownloadStats(): Promise<DownloadStats> {
  return api.get<never, DownloadStats>('/library/download-stats');
}

export interface EnrichMetadataResponse {
  status: string;
  message: string;
  processed: number;
  updated: number;
  skipped: number;
  failed: number;
  details: Array<{
    entry_id: number;
    paper_id: number;
    status: string;
    error?: string;
  }>;
}

/**
 * Kütüphanedeki eksik metadata alanlarını tamamlar
 */
export async function enrichMetadata(limit = 20): Promise<EnrichMetadataResponse> {
  return api.post<never, EnrichMetadataResponse>(`/library/enrich-metadata?limit=${limit}`);
}
