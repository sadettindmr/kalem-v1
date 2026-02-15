/**
 * SearchForm - Arama formu
 * Keywords, yil araligi ve arama butonu
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Search, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { searchPapers } from '@/services/search';
import { checkLibraryPapers } from '@/services/library';
import { useUIStore } from '@/stores/ui-store';
import type { SearchFilters } from '@/types/api';

export default function SearchForm() {
  const [query, setQuery] = useState('');
  const [yearStart, setYearStart] = useState<string>('');
  const [yearEnd, setYearEnd] = useState<string>('');

  const { setSearchResults, setSearchMeta, setIsSearching, setSelectedPaperId, setLastSearchQuery, setSavedPaperIds } = useUIStore();

  const mutation = useMutation({
    mutationFn: (filters: SearchFilters) => searchPapers(filters),
    onMutate: (filters) => {
      setIsSearching(true);
      setSelectedPaperId(null);
      setLastSearchQuery(filters.query);
    },
    onSuccess: async (data) => {
      setSearchResults(data.results);
      setSearchMeta(data.meta);
      setIsSearching(false);

      // Kutuphanede kayitli makaleleri kontrol et
      const externalIds = data.results
        .map((p) => p.external_id)
        .filter((id): id is string => id !== null && id.startsWith('10.'));

      if (externalIds.length > 0) {
        try {
          const response = await checkLibraryPapers(externalIds);
          setSavedPaperIds(response.saved_ids);
        } catch {
          // Check endpoint hatasi arama sonuclarini etkilemesin
        }
      }
    },
    onError: () => {
      setSearchResults([]);
      setIsSearching(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    const filters: SearchFilters = {
      query: query.trim(),
      year_start: yearStart ? parseInt(yearStart) : null,
      year_end: yearEnd ? parseInt(yearEnd) : null,
    };

    mutation.mutate(filters);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Anahtar Kelimeler */}
      <div className="space-y-2">
        <label htmlFor="query" className="text-sm font-medium">
          Anahtar Kelimeler
        </label>
        <Input
          id="query"
          type="text"
          placeholder="ornek: machine learning"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={mutation.isPending}
        />
      </div>

      {/* Yil Araligi */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Yil Araligi</label>
        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Min"
            min={1900}
            max={2100}
            value={yearStart}
            onChange={(e) => setYearStart(e.target.value)}
            disabled={mutation.isPending}
            className="w-1/2"
          />
          <Input
            type="number"
            placeholder="Max"
            min={1900}
            max={2100}
            value={yearEnd}
            onChange={(e) => setYearEnd(e.target.value)}
            disabled={mutation.isPending}
            className="w-1/2"
          />
        </div>
      </div>

      {/* Ara Butonu */}
      <Button
        type="submit"
        className="w-full"
        disabled={!query.trim() || mutation.isPending}
      >
        {mutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Araniyor...
          </>
        ) : (
          <>
            <Search className="h-4 w-4 mr-2" />
            Ara
          </>
        )}
      </Button>

      {/* Status Bar */}
      {mutation.isPending && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Kaynaklar taraniyor...</span>
        </div>
      )}
    </form>
  );
}
