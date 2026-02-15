/**
 * API Type Definitions
 * Backend Pydantic modellerine uygun TypeScript interface'leri
 */

// ==================== Search Types ====================

export type PaperSource = 'semantic' | 'openalex' | 'arxiv' | 'crossref' | 'core' | 'manual';

export interface Author {
  name: string;
}

export interface PaperResponse {
  title: string;
  abstract: string | null;
  year: number | null;
  citation_count: number;
  venue: string | null;
  authors: Author[];
  source: PaperSource;
  external_id: string | null;
  pdf_url: string | null;
}

export interface SearchFilters {
  query: string;
  year_start?: number | null;
  year_end?: number | null;
  min_citations?: number | null;
}

export interface SearchMeta {
  raw_semantic: number;
  raw_openalex: number;
  raw_arxiv: number;
  raw_crossref: number;
  raw_core: number;
  duplicates_removed: number;
  total: number;
}

export interface SearchResponse {
  results: PaperResponse[];
  meta: SearchMeta;
}

// ==================== Error Types ====================

export interface ErrorDetail {
  code: string;
  message: string;
  suggestion?: string | null;
  details?: string | null;
  request_id?: string;
}

export interface ErrorResponse {
  success: false;
  error: ErrorDetail;
}

// ==================== Library Types ====================

export type DownloadStatus = 'pending' | 'downloading' | 'completed' | 'failed';

export interface Tag {
  id: number;
  name: string;
}

export interface PaperDetail {
  id: number;
  title: string;
  abstract: string | null;
  year: number | null;
  citation_count: number;
  venue: string | null;
  doi: string | null;
  pdf_url: string | null;
  authors: Author[];
  created_at: string;
}

export interface LibraryEntry {
  id: number;
  source: PaperSource;
  download_status: DownloadStatus;
  file_path: string | null;
  is_favorite: boolean;
  tags: Tag[];
  paper: PaperDetail;
}

export interface LibraryListResponse {
  items: LibraryEntry[];
  total: number;
  page: number;
  limit: number;
}

export interface IngestRequest {
  paper: PaperResponse;
  search_query: string;
}

export interface IngestResponse {
  status: string;
  entry_id: number;
}

export interface BulkIngestRequest {
  papers: PaperResponse[];
  search_query: string;
}

export interface BulkIngestResponse {
  status: string;
  added_count: number;
  duplicate_count: number;
  failed_count: number;
  entry_ids: number[];
}

export interface CheckLibraryRequest {
  external_ids: string[];
}

export interface CheckLibraryResponse {
  saved_ids: string[];
}
