/**
 * LibraryList - Kütüphane makale listesi
 * useQuery ile GET /api/v2/library + refetchInterval: 5000
 */

import { Library, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useUIStore } from '@/stores/ui-store';
import { fetchLibrary } from '@/services/library';
import LibraryItem from '@/components/LibraryItem';

// Loading skeleton
function LibraryItemSkeleton() {
  return (
    <div className="p-4 border rounded-lg space-y-3">
      <Skeleton className="h-5 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-12" />
        <Skeleton className="h-5 w-20" />
      </div>
    </div>
  );
}

export default function LibraryList() {
  const {
    selectedPaperId,
    setSelectedPaperId,
    libraryFilterTag,
    libraryFilterStatus,
    libraryFilterMinCitations,
    libraryFilterYearStart,
    libraryFilterYearEnd,
    libraryFilterSearch,
  } = useUIStore();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['library', libraryFilterTag, libraryFilterStatus, libraryFilterMinCitations, libraryFilterYearStart, libraryFilterYearEnd, libraryFilterSearch],
    queryFn: () => fetchLibrary({
      limit: 100,
      tag: libraryFilterTag || undefined,
      status: libraryFilterStatus || undefined,
      min_citations: libraryFilterMinCitations ?? undefined,
      year_start: (libraryFilterYearStart && libraryFilterYearStart >= 1900) ? libraryFilterYearStart : undefined,
      year_end: (libraryFilterYearEnd && libraryFilterYearEnd >= 1900) ? libraryFilterYearEnd : undefined,
      search: libraryFilterSearch || undefined,
    }),
    refetchInterval: 5000,
  });

  const entries = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-2">
          <h2 className="font-medium">Kutuphanem</h2>
          {isFetching && !isLoading && (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
          )}
        </div>
        <div className="flex items-center gap-2">
          {total > 0 && (
            <span className="text-sm text-muted-foreground">
              {total} makale
            </span>
          )}
        </div>
      </div>

      {/* List Area */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {/* Loading State */}
          {isLoading && (
            <>
              {[...Array(5)].map((_, i) => (
                <LibraryItemSkeleton key={i} />
              ))}
            </>
          )}

          {/* Empty State */}
          {!isLoading && entries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Library className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm">Kutuphanenizde henuz makale yok</p>
              <p className="text-xs mt-1">Arama yapip makaleleri kaydedin</p>
            </div>
          )}

          {/* Success State */}
          {!isLoading && entries.length > 0 && (
            <>
              {entries.map((entry) => (
                <LibraryItem
                  key={entry.id}
                  entry={entry}
                  isSelected={selectedPaperId === `library-${entry.id}`}
                  onClick={() => setSelectedPaperId(`library-${entry.id}`)}
                />
              ))}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
