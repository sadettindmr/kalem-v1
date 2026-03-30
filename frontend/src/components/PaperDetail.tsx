/**
 * PaperDetail - Makale detay paneli
 * Secilen makalenin detaylarini gosterir (search ve library)
 * PDF Viewer (iframe embed) destegi
 * Etiket duzenleme destegi
 */

import { useEffect, useState } from 'react';
import { BookOpen, ExternalLink, Calendar, Users, Quote, Tag, Save, Loader2, Check, FileText, FolderOpen, Pencil } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { useUIStore } from '@/stores/ui-store';
import { fetchLibrary, ingestPaper, updateLibraryTags } from '@/services/library';
import CollectionPickerDialog from '@/components/CollectionPickerDialog';
import type { PaperResponse } from '@/types/api';

export default function PaperDetail() {
  const { selectedPaperId, searchResults, activeTab, lastSearchQuery } = useUIStore();
  const queryClient = useQueryClient();
  const [isPdfViewerVisible, setIsPdfViewerVisible] = useState(false);
  const [showCollectionDialog, setShowCollectionDialog] = useState(false);
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [tagInput, setTagInput] = useState('');

  // Library verisi
  const { data: libraryData } = useQuery({
    queryKey: ['library', null, null],
    queryFn: () => fetchLibrary({ limit: 100 }),
    enabled: activeTab === 'library',
  });

  // Ingest mutation
  const ingestMutation = useMutation({
    mutationFn: ingestPaper,
    onSuccess: () => {
      toast.success('Makale kutuphaneme eklendi');
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });

  // Tag update mutation
  const tagMutation = useMutation({
    mutationFn: ({ entryId, tags }: { entryId: number; tags: string[] }) =>
      updateLibraryTags(entryId, tags),
    onSuccess: () => {
      toast.success('Etiketler guncellendi');
      setIsEditingTags(false);
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: () => {
      toast.error('Etiketler guncellenemedi');
    },
  });

  // Secili makaleyi bul - search veya library'den
  let selectedPaper: PaperResponse | undefined;
  let libraryTags: { id: number; name: string }[] = [];
  let downloadStatus: string | null = null;
  let filePath: string | null = null;
  let errorMessage: string | null = null;
  let libraryEntryId: number | null = null;

  if (selectedPaperId?.startsWith('library-')) {
    const entryId = Number(selectedPaperId.replace('library-', ''));
    const entry = libraryData?.items?.find((e) => e.id === entryId);
    if (entry) {
      selectedPaper = {
        title: entry.paper.title,
        abstract: entry.paper.abstract,
        year: entry.paper.year,
        citation_count: entry.paper.citation_count,
        venue: entry.paper.venue,
        authors: entry.paper.authors,
        source: entry.source,
        external_id: entry.paper.doi,
        pdf_url: entry.paper.pdf_url,
      };
      libraryTags = entry.tags;
      downloadStatus = entry.download_status;
      filePath = entry.file_path;
      errorMessage = entry.error_message;
      libraryEntryId = entry.id;
    }
  } else {
    selectedPaper = searchResults.find(
      (p, index) => (p.external_id || `paper-${index}`) === selectedPaperId
    );
  }

  const isFromSearch = activeTab === 'search' && selectedPaper && !selectedPaperId?.startsWith('library-');

  const buildPdfEmbedUrl = (path: string | null): string | null => {
    if (!path) return null;

    // Eski kayitlarda absolute path (/data/library/...) gelebilir.
    // StaticFiles mount'u /files oldugu icin relative path'e normalize et.
    let normalizedPath = path.trim();
    const dataPrefix = '/data/library/';
    if (normalizedPath.startsWith(dataPrefix)) {
      normalizedPath = normalizedPath.slice(dataPrefix.length);
    } else if (normalizedPath.startsWith('/')) {
      normalizedPath = normalizedPath.slice(1);
    }

    // URL-safe segment encoding
    normalizedPath = normalizedPath
      .split('/')
      .filter(Boolean)
      .map((segment) => encodeURIComponent(segment))
      .join('/');

    if (!normalizedPath) return null;

    // Ayni-origin /files proxy kullanimi (nginx/vite proxy ile backend'e gider)
    return `/files/${normalizedPath}`;
  };

  // PDF embed URL - sadece kutuphane makalesi + status completed + file_path varsa
  const pdfEmbedUrl = downloadStatus === 'completed' && filePath
    ? buildPdfEmbedUrl(filePath)
    : null;

  // Dis kaynak linki - DOI veya pdf_url
  const externalUrl = selectedPaper?.external_id
    ? `https://doi.org/${selectedPaper.external_id}`
    : selectedPaper?.pdf_url || null;

  const handleSave = () => {
    if (!selectedPaper) return;
    ingestMutation.mutate({
      paper: selectedPaper,
      search_query: lastSearchQuery,
    });
  };

  const handleStartEditTags = () => {
    setTagInput(libraryTags.map((t) => t.name).join(', '));
    setIsEditingTags(true);
  };

  const handleSaveTags = () => {
    if (!libraryEntryId) return;
    const tags = tagInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
    tagMutation.mutate({ entryId: libraryEntryId, tags });
  };

  const handleCancelEditTags = () => {
    setIsEditingTags(false);
    setTagInput('');
  };

  // Makale secimi degistiginde PDF viewer'i ve tag edit modunu kapat.
  useEffect(() => {
    setIsPdfViewerVisible(false);
    setIsEditingTags(false);
  }, [selectedPaperId, activeTab]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 border-b flex items-center px-4 shrink-0">
        <h2 className="font-medium">Makale Detayi</h2>
      </div>

      {/* Content Area */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {/* Bos detay placeholder */}
          {!selectedPaper && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <BookOpen className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm text-center">
                Detaylari gormek icin<br />bir makale secin
              </p>
            </div>
          )}

          {/* Secili makale detaylari */}
          {selectedPaper && (
            <div className="space-y-4">
              {/* 1. Header: Baslik */}
              <h3 className="text-lg font-semibold leading-tight">
                {selectedPaper.title}
              </h3>

              {/* Meta bilgiler: Yil, Atif, Kaynak, Dergi */}
              <div className="flex flex-wrap gap-2">
                {selectedPaper.year && (
                  <Badge variant="outline" className="gap-1">
                    <Calendar className="h-3 w-3" />
                    {selectedPaper.year}
                  </Badge>
                )}
                {selectedPaper.citation_count > 0 && (
                  <Badge className="gap-1">
                    <Quote className="h-3 w-3" />
                    {selectedPaper.citation_count} atif
                  </Badge>
                )}
                <Badge variant="secondary">{selectedPaper.source}</Badge>
                {downloadStatus && (
                  <Badge variant={downloadStatus === 'completed' ? 'default' : 'outline'} className="gap-1"
                    title={downloadStatus === 'failed' && errorMessage ? errorMessage : undefined}>
                    {downloadStatus === 'completed' ? 'Hazir' : downloadStatus === 'pending' ? 'Bekliyor' : downloadStatus === 'downloading' ? 'Indiriliyor' : 'Hata'}
                  </Badge>
                )}
              </div>

              {/* Venue / Dergi */}
              {selectedPaper.venue && (
                <p className="text-sm text-muted-foreground">
                  {selectedPaper.venue}
                </p>
              )}

              {/* Yazarlar */}
              {selectedPaper.authors.length > 0 && (
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Users className="h-4 w-4" />
                    Yazarlar
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {selectedPaper.authors.map((a) => a.name).join(', ')}
                  </p>
                </div>
              )}

              {/* Etiketler */}
              {libraryEntryId && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Tag className="h-4 w-4" />
                    <span className="text-sm font-medium">Etiketler</span>
                    {!isEditingTags && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={handleStartEditTags}
                        title="Etiketleri Duzenle"
                      >
                        <Pencil className="h-3 w-3" />
                      </Button>
                    )}
                  </div>

                  {isEditingTags ? (
                    <div className="space-y-2">
                      <Input
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        placeholder="Etiketleri virgul ile ayirin (orn: makine ogrenmesi, derin ogrenme)"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveTags();
                          if (e.key === 'Escape') handleCancelEditTags();
                        }}
                        autoFocus
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={handleSaveTags}
                          disabled={tagMutation.isPending}
                        >
                          {tagMutation.isPending ? (
                            <Loader2 className="h-3 w-3 animate-spin mr-1" />
                          ) : (
                            <Check className="h-3 w-3 mr-1" />
                          )}
                          Kaydet
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleCancelEditTags}
                        >
                          Vazgec
                        </Button>
                      </div>
                    </div>
                  ) : libraryTags.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {libraryTags.map((tag) => (
                        <Badge key={tag.id} variant="secondary" className="gap-1 text-xs">
                          <Tag className="h-3 w-3" />
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Henuz etiket eklenmemis. Kalem ikonuna tiklayarak ekleyin.
                    </p>
                  )}
                </div>
              )}

              {/* Etiketler - search tab'inda (read-only) */}
              {!libraryEntryId && libraryTags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {libraryTags.map((tag) => (
                    <Badge key={tag.id} variant="secondary" className="gap-1 text-xs">
                      <Tag className="h-3 w-3" />
                      {tag.name}
                    </Badge>
                  ))}
                </div>
              )}

              <Separator />

              {/* 2. Abstract - Scroll edilebilir */}
              {selectedPaper.abstract && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Ozet</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {selectedPaper.abstract}
                  </p>
                </div>
              )}

              <Separator />

              {/* 3. Aksiyonlar */}
              <div className="space-y-2">
                {/* Kutuphaneme Kaydet - sadece search tabinda */}
                {isFromSearch && (
                  <Button
                    className="w-full gap-2"
                    onClick={handleSave}
                    disabled={ingestMutation.isPending || ingestMutation.isSuccess}
                  >
                    {ingestMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Kaydediliyor...
                      </>
                    ) : ingestMutation.isSuccess ? (
                      <>
                        <Check className="h-4 w-4" />
                        Kaydedildi
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4" />
                        Kutuphaneme Kaydet
                      </>
                    )}
                  </Button>
                )}

                {/* Projeye Ekle - sadece library'den secilmis makalelerde */}
                {libraryEntryId && (
                  <Button
                    variant="outline"
                    className="w-full gap-2"
                    onClick={() => setShowCollectionDialog(true)}
                  >
                    <FolderOpen className="h-4 w-4" />
                    Projeye Ekle / Yonet
                  </Button>
                )}

                {/* PDF Ac - status completed ise */}
                {pdfEmbedUrl && (
                  <Button
                    variant="outline"
                    className="w-full gap-2"
                    onClick={() => setIsPdfViewerVisible((v) => !v)}
                  >
                    <ExternalLink className="h-4 w-4" />
                    {isPdfViewerVisible ? 'PDF\'i Gizle' : 'PDF\'i Goruntule'}
                  </Button>
                )}

                {/* Dis Kaynaga Git - DOI veya pdf_url */}
                {externalUrl && (
                  <Button
                    variant="outline"
                    className="w-full gap-2"
                    onClick={() => window.open(externalUrl, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4" />
                    Dis Kaynaga Git
                  </Button>
                )}

                {/* DOI bilgisi */}
                {selectedPaper.external_id && (
                  <p className="text-xs text-muted-foreground text-center">
                    DOI: {selectedPaper.external_id}
                  </p>
                )}
              </div>

              <Separator />

              {/* 4. PDF Viewer (Embed) */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  PDF Goruntuleyici
                </h4>
                {pdfEmbedUrl && isPdfViewerVisible ? (
                  <iframe
                    src={pdfEmbedUrl}
                    className="w-full h-[500px] border rounded-md"
                    title={`PDF: ${selectedPaper.title}`}
                  />
                ) : pdfEmbedUrl ? (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground border rounded-md bg-muted/30">
                    <FileText className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">PDF hazir</p>
                    <p className="text-xs mt-1">
                      Sagdaki "PDF&apos;i Goruntule" butonu ile acabilirsiniz
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground border rounded-md bg-muted/30">
                    <FileText className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">PDF Bulunamadi</p>
                    <p className="text-xs mt-1">
                      {downloadStatus === 'pending'
                        ? 'PDF indirme bekliyor...'
                        : downloadStatus === 'downloading'
                          ? 'PDF indiriliyor...'
                          : downloadStatus === 'failed'
                            ? 'PDF indirme basarisiz oldu'
                            : 'Bu makale icin PDF mevcut degil'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Collection Picker Dialog */}
      {libraryEntryId && (
        <CollectionPickerDialog
          open={showCollectionDialog}
          onOpenChange={setShowCollectionDialog}
          entryIds={[libraryEntryId]}
          mode="single"
        />
      )}
    </div>
  );
}
