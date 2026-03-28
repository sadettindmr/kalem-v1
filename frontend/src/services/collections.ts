/**
 * Collections Service
 * Koleksiyon/Proje API fonksiyonlari
 */

import api from '@/lib/api';
import type { Collection, CollectionListResponse } from '@/types/api';

export async function fetchCollections(): Promise<CollectionListResponse> {
  return api.get<never, CollectionListResponse>('/collections');
}

export async function createCollection(name: string, description?: string): Promise<Collection> {
  return api.post<never, Collection>('/collections', { name, description });
}

export async function deleteCollection(id: number): Promise<void> {
  return api.delete(`/collections/${id}`);
}

export async function syncCollectionEntries(
  collectionId: number,
  entryIds: number[],
): Promise<{ status: string; added: number; removed: number }> {
  return api.post(`/collections/${collectionId}/entries`, { entry_ids: entryIds });
}

export async function addEntriesToCollection(
  collectionId: number,
  entryIds: number[],
): Promise<{ status: string; added: number; already_exists: number }> {
  return api.post(`/collections/${collectionId}/entries/add`, { entry_ids: entryIds });
}

export async function getEntryCollections(entryId: number): Promise<{ collection_ids: number[] }> {
  return api.get<never, { collection_ids: number[] }>(`/collections/by-entry/${entryId}`);
}
