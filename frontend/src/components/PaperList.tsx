/**
 * PaperList - Makale listesi
 * Client-side filtreleme, pagination, bulk selection ve Loading/Empty/Success state'leri
 */

import { useMemo, useState, useCallback } from 'react';
import { FileText, SearchX, ChevronLeft, ChevronRight, Loader2, Library } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useUIStore } from '@/stores/ui-store';
import { bulkIngestPapers } from '@/services/library';
import PaperCard from '@/components/PaperCard';

const BATCH_SIZE = 100;

// Loading skeleton bileseni
function PaperCardSkeleton() {
  return (
    <div className="p-4 border rounded-lg space-y-3">
      <Skeleton className="h-5 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-12" />
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-5 w-16" />
      </div>
    </div>
  );
}

export default function PaperList() {
  const {
    activeTab,
    searchResults,
    isSearching,
    selectedPaperId,
    setSelectedPaperId,
    currentPage,
    itemsPerPage,
    setCurrentPage,
    selectedPaperIds,
    togglePaperSelection,
    selectAllOnPage,
    clearSelection,
    lastSearchQuery,
    addSavedPaperIds,
    searchFilterMinCitations,
    searchFilterOpenAccess,
    searchFilterSource,
  } = useUIStore();

  const queryClient = useQueryClient();

  // Add All dialog state
  const [showAddAllDialog, setShowAddAllDialog] = useState(false);
  const [addAllProgress, setAddAllProgress] = useState<{ current: number; total: number } | null>(null);

  // Client-side filtreleme
  const filteredResults = useMemo(() => {
    let results = searchResults;

    if (searchFilterMinCitations !== null) {
      results = results.filter((p) => p.citation_count >= searchFilterMinCitations);
    }
    if (searchFilterOpenAccess) {
      results = results.filter((p) => p.pdf_url !== null);
    }
    if (searchFilterSource) {
      results = results.filter((p) => p.source === searchFilterSource);
    }

    return results;
  }, [searchResults, searchFilterMinCitations, searchFilterOpenAccess, searchFilterSource]);

  // Pagination hesaplamalari
  const totalResults = filteredResults.length;
  const totalPages = Math.ceil(totalResults / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalResults);
  const paginatedResults = filteredResults.slice(startIndex, endIndex);

  // Sayfadaki tum makalelerin secili olup olmadigini kontrol et
  const pageIds = paginatedResults.map((p, i) => p.external_id || `paper-${startIndex + i}`);
  const allOnPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedPaperIds.has(id));
  const selectionCount = selectedPaperIds.size;

  // Bulk ingest mutation
  const bulkMutation = useMutation({
    mutationFn: bulkIngestPapers,
    onSuccess: (data) => {
      // Detayli sonuc mesaji
      const parts: string[] = [];
      if (data.added_count > 0) parts.push(`${data.added_count} yeni eklendi`);
      if (data.duplicate_count > 0) parts.push(`${data.duplicate_count} zaten kayitli`);
      if (data.failed_count > 0) parts.push(`${data.failed_count} basarisiz`);
      const message = parts.join(', ') || 'Islem tamamlandi';
      toast.success(message);

      // Saved state'i guncelle - eklenen makalelerin external_id'lerini bul
      const savedIds = searchResults
        .filter((p) => {
          const id = p.external_id;
          return id && selectedPaperIds.has(id);
        })
        .map((p) => p.external_id)
        .filter((id): id is string => id !== null);
      if (savedIds.length > 0) {
        addSavedPaperIds(savedIds);
      }

      clearSelection();
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: () => {
      toast.error('Toplu kaydetme sirasinda hata olustu');
    },
  });

  const handleBulkSave = () => {
    const papersToSave = searchResults.filter((p, i) => {
      const id = p.external_id || `paper-${i}`;
      return selectedPaperIds.has(id);
    });
    if (papersToSave.length === 0) return;
    bulkMutation.mutate({ papers: papersToSave, search_query: lastSearchQuery });
  };

  const handleSelectAllToggle = () => {
    if (allOnPageSelected) {
      clearSelection();
    } else {
      selectAllOnPage();
    }
  };

  // "Tum Sonuclari Kutupaneye Ekle" - batching ile
  const handleAddAll = useCallback(async () => {
    setShowAddAllDialog(false);

    // Filtrelenmis sonuclari kullan (aktif filtreler varsa)
    const papersToAdd = filteredResults;
    const totalPapers = papersToAdd.length;

    if (totalPapers === 0) return;

    let totalAdded = 0;
    let totalDuplicate = 0;
    let totalFailed = 0;
    const allSavedIds: string[] = [];

    // Batch'ler halinde gonder
    const totalBatches = Math.ceil(totalPapers / BATCH_SIZE);

    for (let i = 0; i < totalPapers; i += BATCH_SIZE) {
      const batch = papersToAdd.slice(i, i + BATCH_SIZE);
      const batchNum = Math.floor(i / BATCH_SIZE) + 1;
      setAddAllProgress({ current: batchNum, total: totalBatches });

      try {
        const result = await bulkIngestPapers({
          papers: batch,
          search_query: lastSearchQuery,
        });
        totalAdded += result.added_count;
        totalDuplicate += result.duplicate_count;
        totalFailed += result.failed_count;

        // Kaydedilen ID'leri topla
        const batchIds = batch
          .map((p) => p.external_id)
          .filter((id): id is string => id !== null);
        allSavedIds.push(...batchIds);
      } catch {
        totalFailed += batch.length;
      }
    }

    setAddAllProgress(null);

    // Sonuc mesaji
    const parts: string[] = [];
    if (totalAdded > 0) parts.push(`${totalAdded} yeni eklendi`);
    if (totalDuplicate > 0) parts.push(`${totalDuplicate} zaten kayitli`);
    if (totalFailed > 0) parts.push(`${totalFailed} basarisiz`);
    const message = parts.join(', ') || 'Islem tamamlandi';
    toast.success(message);

    // State guncelle
    if (allSavedIds.length > 0) {
      addSavedPaperIds(allSavedIds);
    }
    clearSelection();
    queryClient.invalidateQueries({ queryKey: ['library'] });
  }, [filteredResults, lastSearchQuery, addSavedPaperIds, clearSelection, queryClient]);

  const isAddAllRunning = addAllProgress !== null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-4 shrink-0">
        <h2 className="font-medium">
          {activeTab === 'search' ? 'Arama Sonuclari' : 'Kutuphanem'}
        </h2>
        {totalResults > 0 && (
          <span className="text-sm text-muted-foreground">
            {startIndex + 1}-{endIndex} / {totalResults} sonuc
          </span>
        )}
      </div>

      {/* Bulk Selection Toolbar */}
      {!isSearching && totalResults > 0 && activeTab === 'search' && (
        <div className="h-10 border-b flex items-center justify-between px-4 shrink-0 bg-muted/30">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={allOnPageSelected}
              onCheckedChange={handleSelectAllToggle}
            />
            <span className="text-xs text-muted-foreground">
              {selectionCount > 0 ? `${selectionCount} secili` : 'Tumunu sec'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {selectionCount > 0 && (
              <Button
                size="sm"
                variant="default"
                className="h-7 text-xs"
                onClick={handleBulkSave}
                disabled={bulkMutation.isPending || isAddAllRunning}
              >
                {bulkMutation.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                ) : null}
                Secilenleri Kaydet ({selectionCount})
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs"
              onClick={() => setShowAddAllDialog(true)}
              disabled={bulkMutation.isPending || isAddAllRunning}
            >
              {isAddAllRunning ? (
                <>
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  {addAllProgress.current}/{addAllProgress.total}
                </>
              ) : (
                <>
                  <Library className="h-3 w-3 mr-1" />
                  Tumunu Ekle ({totalResults})
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Add All Confirmation Dialog */}
      <Dialog open={showAddAllDialog} onOpenChange={setShowAddAllDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tum Sonuclari Kutupaneye Ekle</DialogTitle>
            <DialogDescription>
              {totalResults} makale kutuphanenize eklenecek.
              {totalResults > 500 && (
                <> Bu islem {Math.ceil(totalResults / BATCH_SIZE)} paket halinde gonderilecek ve biraz zaman alabilir.</>
              )}
              {' '}Devam etmek istiyor musunuz?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddAllDialog(false)}>
              Iptal
            </Button>
            <Button onClick={handleAddAll}>
              <Library className="h-4 w-4 mr-2" />
              Ekle ({totalResults})
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* List Area */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {/* Loading State - 5 Skeleton */}
          {isSearching && (
            <>
              {[...Array(5)].map((_, i) => (
                <PaperCardSkeleton key={i} />
              ))}
            </>
          )}

          {/* Empty State - Henuz arama yapilmadi */}
          {!isSearching && searchResults.length === 0 && activeTab === 'search' && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <FileText className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm">Arama yapmak icin bir sorgu girin</p>
            </div>
          )}

          {/* Empty State - Filtre sonucu bos */}
          {!isSearching && searchResults.length > 0 && totalResults === 0 && activeTab === 'search' && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <SearchX className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm">Filtrelere uygun sonuc bulunamadi</p>
            </div>
          )}

          {/* Empty State - Kutuphane bos */}
          {!isSearching && totalResults === 0 && activeTab === 'library' && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <SearchX className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm">Kutuphanenizde henuz makale yok</p>
            </div>
          )}

          {/* Success State - Sayfalanmis sonuclar */}
          {!isSearching && totalResults > 0 && (
            <>
              {paginatedResults.map((paper, index) => {
                const paperId = paper.external_id || `paper-${startIndex + index}`;
                return (
                  <PaperCard
                    key={paperId}
                    paper={paper}
                    isSelected={selectedPaperId === paperId}
                    onClick={() => setSelectedPaperId(paperId)}
                    isChecked={selectedPaperIds.has(paperId)}
                    onToggleSelect={() => togglePaperSelection(paperId)}
                  />
                );
              })}
            </>
          )}
        </div>
      </ScrollArea>

      {/* Pagination Controls */}
      {!isSearching && totalPages > 1 && (
        <div className="h-12 border-t flex items-center justify-between px-4 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(currentPage - 1)}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Onceki
          </Button>
          <span className="text-sm text-muted-foreground">
            {currentPage} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={currentPage >= totalPages}
          >
            Sonraki
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}
