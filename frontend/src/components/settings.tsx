import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Archive,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Download,
  HardDrive,
  Key,
  Loader2,
  Info,
  RefreshCw,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '@/lib/api';
import { enrichMetadata, fetchDownloadStats, retryDownloads } from '@/services/library';
import { fetchSettings, updateSettings } from '@/services/settings';
import type { UserSettingsResponse } from '@/types/api';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { APP_NAME, APP_VERSION } from '@/constants/app';

const PROVIDER_OPTIONS = [
  {
    id: 'semantic',
    label: 'Semantic Scholar',
    hint: 'API Key',
    field: 'semantic_scholar_api_key',
    placeholder: 'Semantic Scholar API key',
  },
  {
    id: 'openalex',
    label: 'OpenAlex',
    hint: 'E-posta',
    field: 'openalex_email',
    placeholder: 'ornek@kurum.edu.tr',
  },
  {
    id: 'arxiv',
    label: 'arXiv',
    hint: 'Kimlik gerekmiyor',
    field: null,
    placeholder: '',
  },
  {
    id: 'crossref',
    label: 'Crossref',
    hint: 'E-posta',
    field: 'openalex_email',
    placeholder: 'ornek@kurum.edu.tr',
  },
  {
    id: 'core',
    label: 'CORE',
    hint: 'API Key',
    field: 'core_api_key',
    placeholder: 'CORE API key',
  },
] as const;

interface SettingsFormState {
  openai_api_key: string;
  semantic_scholar_api_key: string;
  core_api_key: string;
  openalex_email: string;
  enabled_providers: string[];
  proxy_url: string;
  proxy_enabled: boolean;
}

function toFormState(settings: UserSettingsResponse): SettingsFormState {
  return {
    openai_api_key: settings.openai_api_key ?? '',
    semantic_scholar_api_key: settings.semantic_scholar_api_key ?? '',
    core_api_key: settings.core_api_key ?? '',
    openalex_email: settings.openalex_email ?? '',
    enabled_providers: settings.enabled_providers ?? [],
    proxy_url: settings.proxy_url ?? '',
    proxy_enabled: settings.proxy_enabled,
  };
}

export default function Settings() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [form, setForm] = useState<SettingsFormState | null>(null);
  const [initialFormJson, setInitialFormJson] = useState('');
  const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  const { data: settingsData, isLoading: isSettingsLoading } = useQuery({
    queryKey: ['system-settings'],
    queryFn: fetchSettings,
  });

  const { data: downloadStats, isLoading: isStatsLoading } = useQuery({
    queryKey: ['download-stats'],
    queryFn: fetchDownloadStats,
    refetchInterval: 10000,
  });

  useEffect(() => {
    if (!settingsData) return;
    const next = toFormState(settingsData);
    setForm(next);
    setInitialFormJson(JSON.stringify(next));
  }, [settingsData]);

  const saveSettingsMutation = useMutation({
    mutationFn: () => {
      if (!form) throw new Error('Ayar formu yuklenemedi');
      return updateSettings({
        openai_api_key: form.openai_api_key.trim() || null,
        semantic_scholar_api_key: form.semantic_scholar_api_key.trim() || null,
        core_api_key: form.core_api_key.trim() || null,
        openalex_email: form.openalex_email.trim() || null,
        enabled_providers: form.enabled_providers,
        proxy_enabled: form.proxy_enabled,
        proxy_url: form.proxy_url.trim() || null,
      });
    },
    onSuccess: (result) => {
      const next = toFormState(result);
      setForm(next);
      setInitialFormJson(JSON.stringify(next));
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      toast.success('Ayarlar kaydedildi');
    },
    onError: () => {
      toast.error('Ayarlar kaydedilemedi');
    },
  });

  const retryMutation = useMutation({
    mutationFn: () => retryDownloads('all'),
    onSuccess: (result) => {
      toast.success(result.message);
      queryClient.invalidateQueries({ queryKey: ['download-stats'] });
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: () => {
      toast.error('Indirmeler tekrar denenemedi');
    },
  });

  const enrichMutation = useMutation({
    mutationFn: () => enrichMetadata(20),
    onSuccess: (result) => {
      toast.success(
        `Metadata tamamlandi: ${result.updated} guncellendi, ${result.skipped} atlandi, ${result.failed} hata`
      );
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
    onError: () => {
      toast.error('Metadata tamamlama islemi basarisiz');
    },
  });

  const updateForm = (patch: Partial<SettingsFormState>) => {
    setForm((prev) => (prev ? { ...prev, ...patch } : prev));
  };

  const toggleProvider = (provider: string, checked: boolean) => {
    if (!form) return;
    if (checked) {
      updateForm({
        enabled_providers: form.enabled_providers.includes(provider)
          ? form.enabled_providers
          : [...form.enabled_providers, provider],
      });
      return;
    }
    updateForm({
      enabled_providers: form.enabled_providers.filter((item) => item !== provider),
    });
  };

  const handleReset = async () => {
    if (confirmationCode !== 'DELETE-ALL-DATA') {
      toast.error('Gecersiz onay kodu');
      return;
    }
    setIsResetting(true);
    try {
      await api.post('/system/reset', { confirmation: confirmationCode });
      toast.success('Sistem Sifirlandi', {
        description: 'Tum veriler temizlendi. Kalem - Kasghar baslangic durumuna donuyor...',
        duration: 5000,
      });
      setIsResetDialogOpen(false);
      setConfirmationCode('');
      setTimeout(() => {
        navigate('/');
        window.location.reload();
      }, 3500);
    } catch (error: unknown) {
      let message = 'Sistem sifirlama islemi basarisiz oldu';
      const maybeError = error as {
        response?: { data?: { error?: { message?: string } } };
      };
      const backendMessage = maybeError.response?.data?.error?.message;
      if (backendMessage) {
        message = backendMessage;
      }
      toast.error('Sifirlama Basarisiz', {
        description: message,
        duration: 5000,
      });
    } finally {
      setIsResetting(false);
    }
  };

  const handleExportXlsx = () => window.open('/api/v2/library/export?format=xlsx', '_blank');
  const handleExportCsv = () => window.open('/api/v2/library/export?format=csv', '_blank');
  const handleExportZip = () => window.open('/api/v2/library/download-zip', '_blank');

  const isSettingsChanged = form !== null && JSON.stringify(form) !== initialFormJson;

  return (
    <div className="min-h-screen bg-background">
      <header className="h-16 border-b flex items-center px-4 gap-4">
        <Link to="/">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-semibold">Ayarlar</h1>
      </header>

      <div className="max-w-4xl mx-auto p-6">
        {isSettingsLoading || !form ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Ayarlar yukleniyor...
          </div>
        ) : (
          <Tabs defaultValue="providers" className="space-y-4">
            <TabsList>
              <TabsTrigger value="providers">Kaynaklar</TabsTrigger>
              <TabsTrigger value="network">Ag/Proxy</TabsTrigger>
              <TabsTrigger value="system">Sistem</TabsTrigger>
            </TabsList>

            <TabsContent value="providers" className="space-y-6">
              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Kaynak ve Kimlik Ayarlari</h2>
                </div>
                <p className="text-sm text-muted-foreground">
                  Her kaynak icin aktif/pasif secimi yapin ve gerekiyorsa API key veya e-posta girin.
                </p>

                <div className="space-y-3">
                  <div className="border rounded-md p-4 space-y-2">
                    <Label htmlFor="openai-key">OpenAI API Key</Label>
                    <Input
                      id="openai-key"
                      type="password"
                      placeholder="sk-..."
                      value={form.openai_api_key}
                      onChange={(e) => updateForm({ openai_api_key: e.target.value })}
                    />
                  </div>

                  {PROVIDER_OPTIONS.map((provider) => (
                    <div key={provider.id} className="border rounded-md p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">{provider.label}</p>
                          <p className="text-xs text-muted-foreground">{provider.hint}</p>
                        </div>
                        <Switch
                          checked={form.enabled_providers.includes(provider.id)}
                          onCheckedChange={(checked) => toggleProvider(provider.id, checked)}
                          aria-label={`${provider.label} aktif`}
                        />
                      </div>
                      {provider.field && (
                        <Input
                          type={provider.field.includes('api_key') ? 'password' : 'email'}
                          placeholder={provider.placeholder}
                          value={form[provider.field]}
                          onChange={(e) =>
                            updateForm({
                              [provider.field]: e.target.value,
                            } as Partial<SettingsFormState>)
                          }
                        />
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end">
                  <Button
                    onClick={() => saveSettingsMutation.mutate()}
                    disabled={!isSettingsChanged || saveSettingsMutation.isPending}
                  >
                    {saveSettingsMutation.isPending ? 'Kaydediliyor...' : 'Kaydet'}
                  </Button>
                </div>
              </section>
            </TabsContent>

            <TabsContent value="network" className="space-y-6">
              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Ag ve Enstitu Ayarlari</h2>
                </div>

                <div className="border rounded-md p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Proxy Kullan</p>
                      <p className="text-xs text-muted-foreground">
                        Enstitu abonelikleri uzerinden PDF indirmek icin buraya kurum proxy adresini giriniz.
                      </p>
                    </div>
                    <Switch
                      checked={form.proxy_enabled}
                      onCheckedChange={(checked) => updateForm({ proxy_enabled: checked })}
                      aria-label="Proxy kullan"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="proxy-url">Proxy URL</Label>
                    <Input
                      id="proxy-url"
                      placeholder="http://user:pass@proxy.univ.edu:8080"
                      value={form.proxy_url}
                      onChange={(e) => updateForm({ proxy_url: e.target.value })}
                      disabled={!form.proxy_enabled}
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    onClick={() => saveSettingsMutation.mutate()}
                    disabled={!isSettingsChanged || saveSettingsMutation.isPending}
                  >
                    {saveSettingsMutation.isPending ? 'Kaydediliyor...' : 'Kaydet'}
                  </Button>
                </div>
              </section>
            </TabsContent>

            <TabsContent value="system" className="space-y-8">
              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Kutuphanemi Indir</h2>
                </div>
                <p className="text-sm text-muted-foreground">
                  Kutuphanenizdeki tum makaleleri disa aktarabilirsiniz.
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleExportXlsx}>Excel (.xlsx)</Button>
                  <Button variant="outline" onClick={handleExportCsv}>CSV</Button>
                  <Button variant="outline" onClick={handleExportZip} className="gap-2">
                    <Archive className="h-4 w-4" />
                    PDF Arsivi Indir (.zip)
                  </Button>
                </div>
              </section>

              <Separator />

              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Indirme Yonetimi</h2>
                </div>
                <p className="text-sm text-muted-foreground">
                  PDF kuyruk durumunu izleyebilir ve tamamlanmayan indirmeleri tekrar deneyebilirsiniz.
                </p>

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

                    {(downloadStats.pending > 0 ||
                      downloadStats.downloading > 0 ||
                      downloadStats.failed > 0) && (
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

                    {downloadStats.failed_entries.length > 0 && (
                      <div className="space-y-2">
                        <h3 className="text-sm font-medium text-destructive">
                          Basarisiz Indirmeler ({downloadStats.failed_entries.length})
                        </h3>
                        <ScrollArea className="max-h-60">
                          <div className="space-y-2">
                            {downloadStats.failed_entries.map((entry) => (
                              <div key={entry.id} className="border rounded-md p-3 space-y-1">
                                <p className="text-sm font-medium leading-tight line-clamp-2">
                                  {entry.title}
                                </p>
                                <div className="flex items-center gap-2">
                                  <Badge variant="destructive" className="text-xs">
                                    Basarisiz
                                  </Badge>
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

              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Metadata Tamamlama</h2>
                </div>
                <p className="text-sm text-muted-foreground">
                  Kutuphanedeki eksik abstract, yil, venue, atif, yazar ve PDF alanlarini dis kaynaklarla tamamlar.
                </p>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() => enrichMutation.mutate()}
                  disabled={enrichMutation.isPending}
                >
                  <Sparkles className={`h-4 w-4 ${enrichMutation.isPending ? 'animate-pulse' : ''}`} />
                  {enrichMutation.isPending ? 'Metadata Tamamlaniyor...' : 'Eksik Verileri Tamamla'}
                </Button>
              </section>

              <Separator />

              <section className="space-y-4">
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Hakkinda</h2>
                </div>
                <div className="border rounded-lg p-4 space-y-2">
                  <p className="text-sm">
                    <span className="font-medium">Uygulama:</span> {APP_NAME}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Surum:</span> {APP_VERSION}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Akademik arama, kutuphane yonetimi, PDF indirme ve disa aktarma aracidir.
                  </p>
                </div>
              </section>

              <Separator />

              <section className="space-y-4">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  <h2 className="text-lg font-semibold">Tehlikeli Bolge</h2>
                </div>
                <div className="border border-destructive rounded-lg p-4 space-y-3">
                  <p className="text-sm font-medium">Fabrika Ayarlarina Don</p>
                  <p className="text-sm text-muted-foreground">
                    Tum veriler (makaleler, etiketler, indirilen PDF&apos;ler) kalici olarak silinir.
                    Bu islem geri alinamaz.
                  </p>
                  <Button variant="destructive" onClick={() => setIsResetDialogOpen(true)}>
                    Fabrika Ayarlarina Don
                  </Button>
                </div>
              </section>
            </TabsContent>
          </Tabs>
        )}
      </div>

      <Dialog open={isResetDialogOpen} onOpenChange={setIsResetDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Sistemi Sifirla
            </DialogTitle>
            <DialogDescription>
              Bu islem tum verileri kalici olarak silecektir. Devam etmek icin kutuya
              <strong> DELETE-ALL-DATA </strong>
              yazin.
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
                  Sifirlaniyor...
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
