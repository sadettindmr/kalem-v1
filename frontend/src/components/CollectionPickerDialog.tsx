/**
 * CollectionPickerDialog - Reusable Koleksiyon Secim Dialog'u
 * Tek veya coklu entry'leri koleksiyonlara atamak icin kullanilir
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FolderOpen, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { fetchCollections, createCollection, addEntriesToCollection, getEntryCollections } from '@/services/collections';

interface CollectionPickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entryIds: number[]; // Tek entry icin [id], bulk icin [id1, id2, ...]
  mode?: 'single' | 'bulk'; // Dialog mesajlarini farklilandirmak icin
}

export default function CollectionPickerDialog({
  open,
  onOpenChange,
  entryIds,
  mode = 'single',
}: CollectionPickerDialogProps) {
  const queryClient = useQueryClient();
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<Set<number>>(new Set());
  const [showNewCollection, setShowNewCollection] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');

  // Tum koleksiyonlari cek
  const { data: collectionsData, isLoading: collectionsLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: fetchCollections,
    enabled: open,
  });

  // Tek entry icin mevcut koleksiyonlari cek (pre-check icin)
  const { data: existingCollections, isLoading: existingLoading } = useQuery({
    queryKey: ['entry-collections', entryIds[0]],
    queryFn: () => getEntryCollections(entryIds[0]),
    enabled: open && mode === 'single' && entryIds.length === 1,
  });

  // Pre-check: Tek entry ise mevcut koleksiyonlari otomatik sec
  useEffect(() => {
    if (mode === 'single' && existingCollections?.collection_ids) {
      setSelectedCollectionIds(new Set(existingCollections.collection_ids));
    } else {
      setSelectedCollectionIds(new Set());
    }
  }, [existingCollections, mode, open]);

  // Yeni koleksiyon olusturma mutation
  const createMutation = useMutation({
    mutationFn: (name: string) => createCollection(name),
    onSuccess: (newCollection) => {
      toast.success('Koleksiyon olusturuldu');
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setSelectedCollectionIds((prev) => new Set([...prev, newCollection.id]));
      setShowNewCollection(false);
      setNewCollectionName('');
    },
    onError: () => {
      toast.error('Koleksiyon olusturulamadi');
    },
  });

  // Entry'leri koleksiyonlara ekleme mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const selectedIds = Array.from(selectedCollectionIds);
      await Promise.all(
        selectedIds.map((collectionId) => addEntriesToCollection(collectionId, entryIds))
      );
    },
    onSuccess: () => {
      const message = mode === 'bulk' ? 'Makaleler projelere eklendi' : 'Proje atamalari guncellendi';
      toast.success(message);
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['library'] });
      queryClient.invalidateQueries({ queryKey: ['entry-collections'] });
      onOpenChange(false);
    },
    onError: () => {
      toast.error('Bir hata olustu');
    },
  });

  const handleToggle = (collectionId: number) => {
    setSelectedCollectionIds((prev) => {
      const next = new Set(prev);
      if (next.has(collectionId)) {
        next.delete(collectionId);
      } else {
        next.add(collectionId);
      }
      return next;
    });
  };

  const handleCreateNew = () => {
    if (newCollectionName.trim()) {
      createMutation.mutate(newCollectionName.trim());
    }
  };

  const handleSave = () => {
    if (selectedCollectionIds.size === 0) {
      toast.error('En az bir proje secmelisiniz');
      return;
    }
    saveMutation.mutate();
  };

  const isLoading = collectionsLoading || existingLoading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            {mode === 'bulk' ? 'Makaleleri Projeye Ekle' : 'Projeye Ekle / Yonet'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'bulk'
              ? `${entryIds.length} makaleyi sectiginiz projelere ekleyin`
              : 'Bu makaleyi hangi projelerde saklamak istersiniz?'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Yeni Koleksiyon Olusturma */}
          {showNewCollection ? (
            <div className="flex gap-2">
              <Input
                placeholder="Proje adi..."
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateNew()}
                autoFocus
              />
              <Button onClick={handleCreateNew} disabled={!newCollectionName.trim() || createMutation.isPending}>
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Olustur'}
              </Button>
              <Button variant="outline" onClick={() => setShowNewCollection(false)}>
                Iptal
              </Button>
            </div>
          ) : (
            <Button variant="outline" className="w-full" onClick={() => setShowNewCollection(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Yeni Proje Olustur
            </Button>
          )}

          <Separator />

          {/* Koleksiyon Listesi */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : collectionsData?.items && collectionsData.items.length > 0 ? (
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                {collectionsData.items.map((collection) => (
                  <div
                    key={collection.id}
                    className="flex items-center gap-3 p-3 rounded-md hover:bg-accent cursor-pointer transition"
                    onClick={() => handleToggle(collection.id)}
                  >
                    <Checkbox
                      checked={selectedCollectionIds.has(collection.id)}
                      onCheckedChange={() => handleToggle(collection.id)}
                    />
                    <div className="flex-1">
                      <div className="font-medium">{collection.name}</div>
                      {collection.description && (
                        <div className="text-sm text-muted-foreground">{collection.description}</div>
                      )}
                      <div className="text-xs text-muted-foreground mt-1">
                        {collection.entry_count} makale
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <FolderOpen className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Henuz proje olusturmamissiniz</p>
              <p className="text-sm">Yukaridaki butonu kullanarak ilk projenizi olusturun</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Iptal
          </Button>
          <Button
            onClick={handleSave}
            disabled={selectedCollectionIds.size === 0 || saveMutation.isPending}
          >
            {saveMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Kaydediliyor...
              </>
            ) : (
              'Kaydet'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
