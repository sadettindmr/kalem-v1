/**
 * PaperCard - Makale karti
 * Title, Authors, Year, Venue, Citation Badge, Kutuphaneme Ekle butonu
 */

import { Plus, Loader2, Check } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { ingestPaper } from '@/services/library';
import { useUIStore } from '@/stores/ui-store';
import type { PaperResponse } from '@/types/api';

interface PaperCardProps {
  paper: PaperResponse;
  isSelected: boolean;
  onClick: () => void;
  isChecked?: boolean;
  onToggleSelect?: () => void;
}

export default function PaperCard({ paper, isSelected, onClick, isChecked, onToggleSelect }: PaperCardProps) {
  const { lastSearchQuery, savedPaperIds, addSavedPaperIds } = useUIStore();
  const queryClient = useQueryClient();

  // Ilk 3 yazar
  const displayAuthors = paper.authors.slice(0, 3);
  const hasMoreAuthors = paper.authors.length > 3;

  // Kutuphanede kayitli mi?
  const isSaved = paper.external_id ? savedPaperIds.has(paper.external_id) : false;

  // Ingest mutation
  const ingestMutation = useMutation({
    mutationFn: ingestPaper,
    onSuccess: () => {
      toast.success('Makale kutuphaneme eklendi');
      queryClient.invalidateQueries({ queryKey: ['library'] });
      // Saved state'i guncelle
      if (paper.external_id) {
        addSavedPaperIds([paper.external_id]);
      }
    },
    onError: () => {
      toast.error('Makale eklenirken hata olustu');
    },
  });

  const handleAdd = (e: React.MouseEvent) => {
    e.stopPropagation();
    ingestMutation.mutate({
      paper,
      search_query: lastSearchQuery,
    });
  };

  const isAlreadySaved = isSaved || ingestMutation.isSuccess;

  return (
    <Card
      className={cn(
        'cursor-pointer transition-colors hover:bg-accent',
        isSelected && 'border-primary bg-accent'
      )}
      onClick={onClick}
    >
      <CardContent className="p-4 space-y-2">
        {/* Baslik - 2 satir truncate */}
        <div className="flex items-start gap-2">
          {onToggleSelect && (
            <Checkbox
              checked={isChecked}
              onCheckedChange={() => onToggleSelect()}
              onClick={(e) => e.stopPropagation()}
              className="mt-1 shrink-0"
            />
          )}
          <h3 className="font-medium leading-tight line-clamp-2 flex-1">
            {paper.title}
          </h3>
          {/* Kutuphaneme Ekle butonu */}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={handleAdd}
            disabled={isAlreadySaved || ingestMutation.isPending}
            title={isAlreadySaved ? 'Kutuphanede kayitli' : 'Kutuphaneme Ekle'}
          >
            {ingestMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : isAlreadySaved ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Yazarlar - ilk 3 */}
        {displayAuthors.length > 0 && (
          <p className="text-sm text-muted-foreground line-clamp-1">
            {displayAuthors.map((a) => a.name).join(', ')}
            {hasMoreAuthors && ' et al.'}
          </p>
        )}

        {/* Alt bilgiler */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Yil */}
          {paper.year && (
            <Badge variant="outline" className="text-xs">
              {paper.year}
            </Badge>
          )}

          {/* Venue */}
          {paper.venue && (
            <Badge variant="secondary" className="text-xs max-w-32 truncate">
              {paper.venue}
            </Badge>
          )}

          {/* Citation Count */}
          {paper.citation_count > 0 && (
            <Badge className="text-xs">
              {paper.citation_count} atif
            </Badge>
          )}

          {/* Kaynak */}
          <Badge
            variant="outline"
            className={cn(
              'text-xs ml-auto',
              paper.source === 'semantic' && 'border-blue-300 text-blue-600',
              paper.source === 'openalex' && 'border-orange-300 text-orange-600',
              paper.source === 'arxiv' && 'bg-red-100 text-red-800 border-red-200',
              paper.source === 'crossref' && 'bg-cyan-100 text-cyan-800 border-cyan-200',
              paper.source === 'core' && 'bg-purple-100 text-purple-600 border-purple-200',
            )}
          >
            {paper.source === 'semantic' ? 'SS' : paper.source === 'openalex' ? 'OA' : paper.source === 'arxiv' ? 'arXiv' : paper.source === 'crossref' ? 'CR' : paper.source === 'core' ? 'CORE' : paper.source}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
