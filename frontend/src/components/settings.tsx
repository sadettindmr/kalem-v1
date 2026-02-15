/**
 * Settings - Ayarlar sayfasi
 * API Key yonetimi, Disa Aktar, Tehlikeli Bolge (Sistem Sifirlama)
 */

import { useState, useEffect } from 'react';
import { ArrowLeft, Key, Download, AlertTriangle, Loader2, RefreshCw, HardDrive, CheckCircle2, Clock, XCircle, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import api from '@/lib/api';
import { fetchDownloadStats, retryDownloads } from '@/services/library';

const API_KEY_STORAGE_KEY = 'semantic_scholar_api_key';

export default function Settings() {
  // API Key state
  const [apiKey, setApiKey] = useState('');
  const [savedKey, setSavedKey] = useState('');

  // Reset dialog state
  const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  // LocalStorage'dan kaydedilmis key'i yukle
  useEffect(() => {
    const stored = localStorage.getItem(API_KEY_STORAGE_KEY);
    if (stored) {
      setApiKey(stored);
      setSavedKey(stored);
    }
  }, []);

  // API Key kaydet
  const handleSaveApiKey = () => {
    const trimmed = apiKey.trim();
    if (trimmed) {
      localStorage.setItem(API_KEY_STORAGE_KEY, trimmed);
      setSavedKey(trimmed);
      toast.success('API Key kaydedildi');
    } else {
      localStorage.removeItem(API_KEY_STORAGE_KEY);
      setSavedKey('');
      toast.success('API Key silindi');
    }
  };

  // Export - Excel
  const handleExportXlsx = () => {
    window.open('/api/v2/library/export?format=xlsx', '_blank');
  };

  // Export - CSV
  const handleExportCsv = () => {
    window.open('/api/v2/library/export?format=csv', '_blank');
  };

  // Sistem sifirlama
  const handleReset = async () => {
    if (confirmationCode !== 'DELETE-ALL-DATA') {
      toast.error('Gecersiz onay kodu');
      return;
    }

    setIsResetting(true);
    try {
      await api.post('/system/reset', { confirmation: confirmationCode });
      toast.success('Sistem basariyla sifirlandi');
      setIsResetDialogOpen(false);
      setConfirmationCode('');
      // Sayfayi yenile
      window.location.reload();
    } catch {
      // Interceptor zaten toast gosteriyor
    } finally {
      setIsResetting(false);
    }
  };

  // Download stats
  const queryClient = useQueryClient();
  const { data: downloadStats, isLoading: isStatsLoading } = useQuery({
    queryKey: ['download-stats'],
    queryFn: fetchDownloadStats,
    refetchInterval: 10000,
  });

  const retryMutation = useMutation({
    mutationFn: retryDownloads,
    onSuccess: (result) => {
      toast.success(result.message);
      queryClient.invalidateQueries({ queryKey: ['download-stats'] });
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: () => {
      toast.error('Indirmeler tekrar denenemedi');
    },
  });

  const isKeyChanged = apiKey.trim() !== savedKey;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="h-16 border-b flex items-center px-4 gap-4">
        <Link to="/">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-semibold">Ayarlar</h1>
      </header>

      {/* Content */}
      <div className="max-w-2xl mx-auto p-6 space-y-8">
        {/* 1. API Ayarlari */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            <h2 className="text-lg font-semibold">API Ayarlari</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Semantic Scholar API Key girildiginde arama istemlerinde rate limit artirilir.
          </p>

          <div className="space-y-2">
            <Label htmlFor="api-key">Semantic Scholar API Key</Label>
            <div className="flex gap-2">
              <Input
                id="api-key"
                type="password"
                placeholder="API Key girin..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <Button
                onClick={handleSaveApiKey}
                disabled={!isKeyChanged}
              >
                Kaydet
              </Button>
            </div>
            {savedKey && (
              <p className="text-xs text-muted-foreground">
                Kaydedilmis key: {savedKey.slice(0, 8)}...
              </p>
            )}
          </div>
        </section>

        <Separator />

        {/* 2. Disa Aktar (Export) */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Kutuphanemi Indir</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Kutuphanenizdeki tum makaleleri disa aktarin.
          </p>

          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExportXlsx}>
              Excel (.xlsx)
            </Button>
            <Button variant="outline" onClick={handleExportCsv}>
              CSV
            </Button>
          </div>
        </section>

        <Separator />

        {/* 3. Indirme Yonetimi */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Indirme Yonetimi</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            PDF indirme kuyrugunun durumunu goruntuleyebilir ve basarisiz indirmeleri tekrar deneyebilirsiniz.
          </p>

          {/* Stats Cards */}
          {isStatsLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Yukleniyor...
            </div>
          ) : downloadStats ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="border rounded-lg p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <Clock className="h-3.5 w-3.5" />
                    <span className="text-xs">Bekliyor</span>
                  </div>
                  <p className="text-2xl font-bold">{downloadStats.pending}</p>
                </div>
                <div className="border rounded-lg p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-blue-500">
                    <Activity className="h-3.5 w-3.5" />
                    <span className="text-xs">Indiriliyor</span>
                  </div>
                  <p className="text-2xl font-bold">{downloadStats.downloading}</p>
                </div>
                <div className="border rounded-lg p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-green-500">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span className="text-xs">Tamamlandi</span>
                  </div>
                  <p className="text-2xl font-bold">{downloadStats.completed}</p>
                </div>
                <div className="border rounded-lg p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-destructive">
                    <XCircle className="h-3.5 w-3.5" />
                    <span className="text-xs">Basarisiz</span>
                  </div>
                  <p className="text-2xl font-bold">{downloadStats.failed}</p>
                </div>
              </div>

              {/* Retry Button */}
              {(downloadStats.pending > 0 || downloadStats.downloading > 0 || downloadStats.failed > 0) && (
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() => retryMutation.mutate()}
                  disabled={retryMutation.isPending}
                >
                  <RefreshCw className={`h-4 w-4 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
                  {retryMutation.isPending ? 'Kuyruga Ekleniyor...' : 'Tumunu Tekrar Dene'}
                </Button>
              )}

              {/* Failed Entries List */}
              {downloadStats.failed_entries.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-destructive">
                    Basarisiz Indirmeler ({downloadStats.failed_entries.length})
                  </h3>
                  <ScrollArea className="max-h-60">
                    <div className="space-y-2">
                      {downloadStats.failed_entries.map((entry) => (
                        <div key={entry.id} className="border rounded-md p-3 space-y-1">
                          <p className="text-sm font-medium leading-tight line-clamp-2">{entry.title}</p>
                          <div className="flex items-center gap-2">
                            <Badge variant="destructive" className="text-xs">Basarisiz</Badge>
                            {entry.updated_at && (
                              <span className="text-xs text-muted-foreground">
                                {new Date(entry.updated_at).toLocaleString('tr-TR')}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </>
          ) : null}
        </section>

        <Separator />

        {/* 4. Tehlikeli Bolge (Danger Zone) */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Tehlikeli Bolge</h2>
          </div>

          <div className="border border-destructive rounded-lg p-4 space-y-3">
            <p className="text-sm font-medium">Fabrika Ayarlarina Don</p>
            <p className="text-sm text-muted-foreground">
              Tum veriler (makaleler, etiketler, indirilen PDF'ler) kalici olarak silinir.
              Bu islem geri alinamaz!
            </p>
            <Button
              variant="destructive"
              onClick={() => setIsResetDialogOpen(true)}
            >
              Fabrika Ayarlarina Don
            </Button>
          </div>
        </section>
      </div>

      {/* Reset Onay Dialog */}
      <Dialog open={isResetDialogOpen} onOpenChange={setIsResetDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Sistemi Sifirla
            </DialogTitle>
            <DialogDescription>
              Bu islem tum verileri kalici olarak silecektir. Devam etmek icin
              asagidaki kutuya <strong>DELETE-ALL-DATA</strong> yazin.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 py-2">
            <Label htmlFor="confirmation">Onay Kodu</Label>
            <Input
              id="confirmation"
              placeholder="DELETE-ALL-DATA"
              value={confirmationCode}
              onChange={(e) => setConfirmationCode(e.target.value)}
              disabled={isResetting}
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsResetDialogOpen(false);
                setConfirmationCode('');
              }}
              disabled={isResetting}
            >
              Iptal
            </Button>
            <Button
              variant="destructive"
              onClick={handleReset}
              disabled={confirmationCode !== 'DELETE-ALL-DATA' || isResetting}
            >
              {isResetting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sifirlanıyor...
                </>
              ) : (
                'Onayla ve Sifirla'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
