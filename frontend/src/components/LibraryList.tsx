/**
 * LibraryList - Kütüphane makale listesi
 * useQuery ile GET /api/v2/library + refetchInterval: 5000
 */

import { Archive, Library, Loader2, RefreshCw, FolderOpen } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useUIStore } from '@/stores/ui-store';
import { fetchDownloadStats, fetchLibrary, retryDownloads } from '@/services/library';
import LibraryItem from '@/components/LibraryItem';
import CollectionPickerDialog from '@/components/CollectionPickerDialog';

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
  const queryClient = useQueryClient();
  const {
    selectedPaperId,
    setSelectedPaperId,
    libraryFilterTag,
    libraryFilterStatus,
    libraryFilterMinCitations,
    libraryFilterYearStart,
    libraryFilterYearEnd,
    libraryFilterSearch,
    selectedCollectionId,
  } = useUIStore();

  const [selectedEntryIds, setSelectedEntryIds] = useState<Set<number>>(new Set());
  const [showCollectionDialog, setShowCollectionDialog] = useState(false);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['library', libraryFilterTag, libraryFilterStatus, libraryFilterMinCitations, libraryFilterYearStart, libraryFilterYearEnd, libraryFilterSearch, selectedCollectionId],
    queryFn: () => fetchLibrary({
      limit: 100,
      tag: libraryFilterTag || undefined,
      status: libraryFilterStatus || undefined,
      min_citations: libraryFilterMinCitations ?? undefined,
      year_start: (libraryFilterYearStart && libraryFilterYearStart >= 1900) ? libraryFilterYearStart : undefined,
      year_end: (libraryFilterYearEnd && libraryFilterYearEnd >= 1900) ? libraryFilterYearEnd : undefined,
      search: libraryFilterSearch || undefined,
      collection_id: selectedCollectionId ?? undefined,
    }),
    refetchInterval: 5000,
  });

  const { data: downloadStats } = useQuery({
    queryKey: ['download-stats'],
    queryFn: fetchDownloadStats,
    refetchInterval: 10000,
  });

  const retryMutation = useMutation({
    mutationFn: () => {
      const hasFailed = (downloadStats?.failed ?? 0) > 0;
      return retryDownloads(hasFailed ? 'all' : 'stuck');
    },
    onSuccess: (result) => {
      toast.success(result.message);
      queryClient.invalidateQueries({ queryKey: ['library'] });
      queryClient.invalidateQueries({ queryKey: ['download-stats'] });
    },
    onError: () => {
      toast.error('Takili indirmeler tekrar denenemedi');
    },
  });

  const entries = data?.items ?? [];
  const total = data?.total ?? 0;
  const selectionCount = selectedEntryIds.size;
  const allSelected = entries.length > 0 && entries.every((entry) => selectedEntryIds.has(entry.id));
  const hasRetryable =
    (downloadStats?.pending ?? 0) > 0 ||
    (downloadStats?.downloading ?? 0) > 0 ||
    (downloadStats?.failed ?? 0) > 0;

  const handleDownloadZip = () => {
    const params = new URLSearchParams();
    if (libraryFilterTag) params.set('tag', libraryFilterTag);
    if (libraryFilterStatus) params.set('status', libraryFilterStatus);
    if (libraryFilterMinCitations != null) params.set('min_citations', String(libraryFilterMinCitations));
    if (libraryFilterYearStart != null && libraryFilterYearStart >= 1900) params.set('year_start', String(libraryFilterYearStart));
    if (libraryFilterYearEnd != null && libraryFilterYearEnd >= 1900) params.set('year_end', String(libraryFilterYearEnd));
    if (libraryFilterSearch) params.set('search', libraryFilterSearch);
    if (selectedCollectionId != null) params.set('collection_id', String(selectedCollectionId));

    const query = params.toString();
    window.open(`/api/v2/library/download-zip${query ? `?${query}` : ''}`, '_blank');
  };

  useEffect(() => {
    if (entries.length === 0) {
      setSelectedEntryIds(new Set());
      return;
    }
    setSelectedEntryIds((prev) => {
      const validIds = new Set(entries.map((entry) => entry.id));
      const next = new Set(Array.from(prev).filter((id) => validIds.has(id)));
      return next;
    });
  }, [entries]);

  const handleToggleSelect = (entryId: number) => {
    setSelectedEntryIds((prev) => {
      const next = new Set(prev);
      if (next.has(entryId)) {
        next.delete(entryId);
      } else {
        next.add(entryId);
      }
      return next;
    });
  };

  const handleSelectAllToggle = () => {
    if (allSelected) {
      setSelectedEntryIds(new Set());
    } else {
      setSelectedEntryIds(new Set(entries.map((entry) => entry.id)));
    }
  };

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
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5"
            onClick={handleDownloadZip}
          >
            <Archive className="h-3.5 w-3.5" />
            PDF Arsivi Indir (.zip)
          </Button>
          {hasRetryable && (
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5"
              onClick={() => retryMutation.mutate()}
              disabled={retryMutation.isPending}
            >
              <RefreshCw className={`h-3.5 w-3.5 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
              {retryMutation.isPending ? 'Kuyruga Ekleniyor...' : 'Indirmeleri Tekrar Dene'}
            </Button>
          )}
          {total > 0 && (
            <span className="text-sm text-muted-foreground">
              {total} makale
            </span>
          )}
        </div>
      </div>

      {/* Bulk Selection Toolbar */}
      {!isLoading && entries.length > 0 && (
        <div className="h-10 border-b flex items-center justify-between px-4 shrink-0 bg-muted/30">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={allSelected}
              onCheckedChange={handleSelectAllToggle}
            />
            <span className="text-xs text-muted-foreground">
              {selectionCount > 0 ? `${selectionCount} secili` : 'Tumunu sec'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="default"
              className="h-7 text-xs"
              onClick={() => setShowCollectionDialog(true)}
              disabled={selectionCount === 0}
            >
              <FolderOpen className="h-3 w-3 mr-1" />
              Projeye Ekle
            </Button>
          </div>
        </div>
      )}

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
                    isChecked={selectedEntryIds.has(entry.id)}
                    onToggleSelect={() => handleToggleSelect(entry.id)}
                  />
                ))}
              </>
            )}
        </div>
      </ScrollArea>

      {selectionCount > 0 && (
        <CollectionPickerDialog
          open={showCollectionDialog}
          onOpenChange={setShowCollectionDialog}
          entryIds={Array.from(selectedEntryIds)}
          mode="bulk"
        />
      )}
    </div>
  );
}
