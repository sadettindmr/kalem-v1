/**
 * LibraryItem - Kütüphane makale kartı
 * Başlık, Yazar, Durum Rozeti (Badge), Sil ikonu
 */

import { Loader2, Check, Clock, AlertCircle, Trash2, Quote } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { LibraryEntry } from '@/types/api';

interface LibraryItemProps {
  entry: LibraryEntry;
  isSelected: boolean;
  onClick: () => void;
  onDelete?: (id: number) => void;
}

const statusConfig = {
  pending: {
    label: 'Bekliyor',
    variant: 'outline' as const,
    icon: Clock,
    className: 'text-muted-foreground',
  },
  downloading: {
    label: 'Indiriliyor',
    variant: 'default' as const,
    icon: Loader2,
    className: 'text-blue-600 bg-blue-50 border-blue-200',
  },
  completed: {
    label: 'Hazir',
    variant: 'default' as const,
    icon: Check,
    className: 'text-green-600 bg-green-50 border-green-200',
  },
  failed: {
    label: 'Hata',
    variant: 'destructive' as const,
    icon: AlertCircle,
    className: 'text-red-600 bg-red-50 border-red-200',
  },
};

export default function LibraryItem({ entry, isSelected, onClick, onDelete }: LibraryItemProps) {
  const { paper } = entry;
  const status = statusConfig[entry.download_status];
  const StatusIcon = status.icon;

  // İlk 3 yazar
  const displayAuthors = paper.authors.slice(0, 3);
  const hasMoreAuthors = paper.authors.length > 3;

  return (
    <Card
      className={cn(
        'cursor-pointer transition-colors hover:bg-accent group',
        isSelected && 'border-primary bg-accent'
      )}
      onClick={onClick}
    >
      <CardContent className="p-4 space-y-2">
        {/* Üst kısım: Başlık + Sil butonu */}
        <div className="flex items-start gap-2">
          <h3 className="font-medium leading-tight line-clamp-2 flex-1">
            {paper.title}
          </h3>
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(entry.id);
              }}
            >
              <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
            </Button>
          )}
        </div>

        {/* Yazarlar */}
        {displayAuthors.length > 0 && (
          <p className="text-sm text-muted-foreground line-clamp-1">
            {displayAuthors.map((a) => a.name).join(', ')}
            {hasMoreAuthors && ' et al.'}
          </p>
        )}

        {/* Alt bilgiler */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Yıl */}
          {paper.year && (
            <Badge variant="outline" className="text-xs">
              {paper.year}
            </Badge>
          )}

          {/* Atıf Sayısı */}
          {paper.citation_count > 0 && (
            <Badge variant="outline" className="text-xs gap-1">
              <Quote className="h-3 w-3" />
              {paper.citation_count}
            </Badge>
          )}

          {/* Durum Rozeti */}
          <Badge variant={status.variant} className={cn('text-xs gap-1', status.className)}>
            <StatusIcon className={cn('h-3 w-3', entry.download_status === 'downloading' && 'animate-spin')} />
            {status.label}
          </Badge>

          {/* Etiketler */}
          {entry.tags.slice(0, 2).map((tag) => (
            <Badge key={tag.id} variant="secondary" className="text-xs">
              {tag.name}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
