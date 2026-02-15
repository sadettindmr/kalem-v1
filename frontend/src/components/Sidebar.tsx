/**
 * Sidebar - Navigasyon ve Arama Formu
 * Search ve Library sekmeleri + SearchForm + Sonuc Istatistikleri + Filtreler
 */

import { useMemo } from 'react';
import { Search, Library, Tag, Filter, BarChart3, Calendar, BookOpen } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';
import SearchForm from '@/components/SearchForm';
import { fetchLibrary } from '@/services/library';

interface NavItem {
  id: 'search' | 'library';
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    id: 'search',
    label: 'Arama',
    icon: <Search className="h-4 w-4" />,
  },
  {
    id: 'library',
    label: 'Kutuphanem',
    icon: <Library className="h-4 w-4" />,
  },
];

const statusFilters = [
  { value: '', label: 'Tumu' },
  { value: 'pending', label: 'Bekliyor' },
  { value: 'downloading', label: 'Indiriliyor' },
  { value: 'completed', label: 'Hazir' },
  { value: 'failed', label: 'Hata' },
];

export default function Sidebar() {
  const {
    activeTab,
    setActiveTab,
    searchResults,
    searchMeta,
    libraryFilterTag,
    setLibraryFilterTag,
    libraryFilterStatus,
    setLibraryFilterStatus,
    libraryFilterMinCitations,
    setLibraryFilterMinCitations,
    libraryFilterYearStart,
    setLibraryFilterYearStart,
    libraryFilterYearEnd,
    setLibraryFilterYearEnd,
    libraryFilterSearch,
    setLibraryFilterSearch,
    searchFilterMinCitations,
    setSearchFilterMinCitations,
    searchFilterOpenAccess,
    setSearchFilterOpenAccess,
    searchFilterSource,
    setSearchFilterSource,
  } = useUIStore();

  // Library'deki tag'leri almak icin library verisi
  const { data: libraryData } = useQuery({
    queryKey: ['library', null, null],
    queryFn: () => fetchLibrary({ limit: 100 }),
    enabled: activeTab === 'library',
  });

  // Tag listesini library verilerinden cikar
  const allTags = libraryData?.items
    ? [...new Map(
        libraryData.items.flatMap((entry) => entry.tags).map((tag) => [tag.id, tag])
      ).values()]
    : [];

  // Kaynak istatistikleri (dedup sonrasi - client-side)
  const sourceStats = useMemo(() => {
    if (searchResults.length === 0) return null;
    const semantic = searchResults.filter((p) => p.source === 'semantic').length;
    const openalex = searchResults.filter((p) => p.source === 'openalex').length;
    const arxiv = searchResults.filter((p) => p.source === 'arxiv').length;
    const crossref = searchResults.filter((p) => p.source === 'crossref').length;
    const core = searchResults.filter((p) => p.source === 'core').length;
    return { semantic, openalex, arxiv, crossref, core, total: searchResults.length };
  }, [searchResults]);

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-4">
        {/* Navigasyon */}
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Navigasyon
          </h2>
          {navItems.map((item) => (
            <Button
              key={item.id}
              variant={activeTab === item.id ? 'secondary' : 'ghost'}
              className={cn(
                'w-full justify-start gap-3',
                activeTab === item.id && 'bg-secondary'
              )}
              onClick={() => setActiveTab(item.id)}
            >
              {item.icon}
              {item.label}
            </Button>
          ))}
        </div>

        {/* Arama Formu - Sadece search tabinda goster */}
        {activeTab === 'search' && (
          <>
            <Separator />
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-muted-foreground">
                Arama Filtresi
              </h2>
              <SearchForm />
            </div>
          </>
        )}

        {/* Kaynak Istatistikleri - Arama sonuclari varken */}
        {activeTab === 'search' && sourceStats && (
          <>
            <Separator />
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <BarChart3 className="h-3.5 w-3.5" />
                Arama Sonuclari
              </div>
              <div className="space-y-1 text-xs">
                {/* Ham sonuclar (API'den gelen) */}
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Semantic Scholar</span>
                  <Badge variant="outline" className="text-xs h-5">
                    {searchMeta ? searchMeta.raw_semantic : sourceStats.semantic}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">OpenAlex</span>
                  <Badge variant="outline" className="text-xs h-5">
                    {searchMeta ? searchMeta.raw_openalex : sourceStats.openalex}
                  </Badge>
                </div>
                {searchMeta && searchMeta.raw_arxiv > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">arXiv</span>
                    <Badge variant="outline" className="text-xs h-5">{searchMeta.raw_arxiv}</Badge>
                  </div>
                )}
                {searchMeta && searchMeta.raw_crossref > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Crossref</span>
                    <Badge variant="outline" className="text-xs h-5">{searchMeta.raw_crossref}</Badge>
                  </div>
                )}
                {searchMeta && searchMeta.raw_core > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">CORE</span>
                    <Badge variant="outline" className="text-xs h-5">{searchMeta.raw_core}</Badge>
                  </div>
                )}
                {searchMeta && searchMeta.relevance_removed > 0 && (
                  <div className="flex items-center justify-between text-amber-600">
                    <span>Alaka disi elenen</span>
                    <Badge variant="outline" className="text-xs h-5 text-amber-600 border-amber-300">
                      -{searchMeta.relevance_removed}
                    </Badge>
                  </div>
                )}
                {/* Mukerrer bilgisi */}
                {searchMeta && searchMeta.duplicates_removed > 0 && (
                  <div className="flex items-center justify-between text-orange-500">
                    <span>Mukerrer elenen</span>
                    <Badge variant="outline" className="text-xs h-5 text-orange-500 border-orange-300">
                      -{searchMeta.duplicates_removed}
                    </Badge>
                  </div>
                )}
                <Separator className="my-1" />
                <div className="flex items-center justify-between font-medium">
                  <span>Toplam</span>
                  <Badge className="text-xs h-5">{sourceStats.total}</Badge>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Sonuc Filtresi - Arama sonuclari varken */}
        {activeTab === 'search' && sourceStats && (
          <>
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Filter className="h-3.5 w-3.5" />
                Sonuc Filtresi
              </div>

              {/* Kaynak filtresi */}
              <div className="space-y-1.5">
                <span className="text-xs text-muted-foreground">Kaynak</span>
                <div className="flex flex-wrap gap-1.5">
                  <Badge
                    variant={!searchFilterSource ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setSearchFilterSource(null)}
                  >
                    Tumu
                  </Badge>
                  <Badge
                    variant={searchFilterSource === 'semantic' ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setSearchFilterSource('semantic')}
                  >
                    Semantic Scholar
                  </Badge>
                  <Badge
                    variant={searchFilterSource === 'openalex' ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setSearchFilterSource('openalex')}
                  >
                    OpenAlex
                  </Badge>
                  <Badge
                    variant={searchFilterSource === 'arxiv' ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setSearchFilterSource('arxiv')}
                  >
                    arXiv
                  </Badge>
                  <Badge
                    variant={searchFilterSource === 'crossref' ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setSearchFilterSource('crossref')}
                  >
                    Crossref
                  </Badge>
                  <Badge
                    variant={searchFilterSource === 'core' ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setSearchFilterSource('core')}
                  >
                    CORE
                  </Badge>
                </div>
              </div>

              {/* Min. Atif */}
              <div className="space-y-1.5">
                <span className="text-xs text-muted-foreground">Min. Atif</span>
                <Input
                  type="number"
                  placeholder="ornek: 100"
                  min={0}
                  className="h-8 text-xs"
                  value={searchFilterMinCitations ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    setSearchFilterMinCitations(val ? parseInt(val) : null);
                  }}
                />
              </div>

              {/* Acik Erisim */}
              <div className="flex items-center gap-2">
                <Checkbox
                  id="open-access"
                  checked={searchFilterOpenAccess}
                  onCheckedChange={(checked) => setSearchFilterOpenAccess(checked === true)}
                />
                <label htmlFor="open-access" className="text-xs cursor-pointer">
                  Sadece Acik Erisim
                </label>
              </div>
            </div>
          </>
        )}

        {/* Library Filtreleri - Sadece library tabinda goster */}
        {activeTab === 'library' && (
          <>
            <Separator />

            {/* Durum Filtresi */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Filter className="h-3.5 w-3.5" />
                Durum
              </div>
              <div className="flex flex-wrap gap-1.5">
                {statusFilters.map((sf) => (
                  <Badge
                    key={sf.value}
                    variant={(libraryFilterStatus || '') === sf.value ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setLibraryFilterStatus(sf.value || null)}
                  >
                    {sf.label}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Tag Filtresi */}
            {allTags.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Tag className="h-3.5 w-3.5" />
                  Etiketler
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge
                    variant={!libraryFilterTag ? 'default' : 'outline'}
                    className="cursor-pointer text-xs"
                    onClick={() => setLibraryFilterTag(null)}
                  >
                    Tumu
                  </Badge>
                  {allTags.map((tag) => (
                    <Badge
                      key={tag.id}
                      variant={libraryFilterTag === tag.name ? 'default' : 'outline'}
                      className="cursor-pointer text-xs"
                      onClick={() => setLibraryFilterTag(tag.name)}
                    >
                      {tag.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Anahtar Kelime Arama */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Search className="h-3.5 w-3.5" />
                Arama
              </div>
              <Input
                type="text"
                placeholder="Baslik, yazar veya etiket..."
                className="h-8 text-xs"
                value={libraryFilterSearch}
                onChange={(e) => setLibraryFilterSearch(e.target.value)}
              />
            </div>

            {/* Yil Araligi */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" />
                Yil Araligi
              </div>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  placeholder="Baslangic"
                  min={1900}
                  max={2100}
                  className="h-8 text-xs"
                  value={libraryFilterYearStart ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    setLibraryFilterYearStart(val ? parseInt(val) : null);
                  }}
                />
                <span className="text-xs text-muted-foreground">-</span>
                <Input
                  type="number"
                  placeholder="Bitis"
                  min={1900}
                  max={2100}
                  className="h-8 text-xs"
                  value={libraryFilterYearEnd ?? ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    setLibraryFilterYearEnd(val ? parseInt(val) : null);
                  }}
                />
              </div>
            </div>

            {/* Min. Atif */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <BookOpen className="h-3.5 w-3.5" />
                Min. Atif
              </div>
              <Input
                type="number"
                placeholder="ornek: 50"
                min={0}
                className="h-8 text-xs"
                value={libraryFilterMinCitations ?? ''}
                onChange={(e) => {
                  const val = e.target.value;
                  setLibraryFilterMinCitations(val ? parseInt(val) : null);
                }}
              />
            </div>
          </>
        )}
      </div>
    </ScrollArea>
  );
}
