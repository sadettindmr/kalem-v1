/**
 * LibraryItem - Kütüphane makale kartı
 * Başlık, Yazar, Durum Rozeti (Badge), Sil ikonu, Projeden Çıkar ikonu
 */

import { useState } from 'react';
import { Loader2, Check, Clock, AlertCircle, Trash2, Quote, X } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import type { LibraryEntry } from '@/types/api';

interface LibraryItemProps {
  entry: LibraryEntry;
  isSelected: boolean;
  onClick: () => void;
  onDelete?: (id: number) => void;
  onRemoveFromCollection?: (entryId: number) => void;
  isChecked?: boolean;
  onToggleSelect?: () => void;
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

export default function LibraryItem({
  entry,
  isSelected,
  onClick,
  onDelete,
  onRemoveFromCollection,
  isChecked,
  onToggleSelect,
}: LibraryItemProps) {
  const { paper } = entry;
  const status = statusConfig[entry.download_status];
  const StatusIcon = status.icon;
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // İlk 3 yazar
  const displayAuthors = paper.authors.slice(0, 3);
  const hasMoreAuthors = paper.authors.length > 3;

  return (
    <>
      <Card
        className={cn(
          'cursor-pointer transition-colors hover:bg-accent group',
          isSelected && 'border-primary bg-accent'
        )}
        onClick={onClick}
      >
        <CardContent className="p-4 space-y-2">
          {/* Üst kısım: Başlık + Aksiyon butonları */}
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
            <div className="flex items-center gap-1 shrink-0">
              {/* Projeden Çıkar butonu */}
              {onRemoveFromCollection && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 text-xs text-orange-600 border-orange-200 hover:bg-orange-50 hover:text-orange-700"
                  title="Bu Projeden Cikar"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFromCollection(entry.id);
                  }}
                >
                  <X className="h-3.5 w-3.5 mr-1" />
                  Cikar
                </Button>
              )}
              {/* Sil butonu */}
              {onDelete && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 text-xs text-destructive border-destructive/30 hover:bg-destructive/10"
                  title="Kutuphaneden Sil"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowDeleteDialog(true);
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1" />
                  Sil
                </Button>
              )}
            </div>
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

      {/* Silme Onay Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Makaleyi Sil</DialogTitle>
            <DialogDescription>
              &quot;{paper.title.slice(0, 80)}{paper.title.length > 80 ? '...' : ''}&quot;
              {' '}makalesi kutuphaneden kalici olarak silinecek.
              {entry.file_path && ' PDF dosyasi da diskten kaldirilacak.'}
              {' '}Bu islem geri alinamaz.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Vazgec
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setShowDeleteDialog(false);
                onDelete?.(entry.id);
              }}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Sil
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
