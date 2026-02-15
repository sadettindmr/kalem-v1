/**
 * DashboardLayout - Zotero benzeri 3 sutunlu layout
 * TDD Bolum 3.3'e uygun tasarim
 */

import { Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useUIStore } from '@/stores/ui-store';
import Sidebar from '@/components/Sidebar';
import PaperList from '@/components/PaperList';
import LibraryList from '@/components/LibraryList';
import PaperDetail from '@/components/PaperDetail';

export default function DashboardLayout() {
  const { activeTab, setActiveTab, setSearchResults, setSelectedPaperId } = useUIStore();

  const handleLogoClick = () => {
    setActiveTab('search');
    setSearchResults([]);
    setSelectedPaperId(null);
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="h-16 border-b flex items-center justify-between px-4 shrink-0">
        {/* Sol: Logo ve Baslik */}
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={handleLogoClick}
        >
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">K</span>
          </div>
          <h1 className="text-xl font-semibold">Kalem - Kasghar</h1>
        </div>

        {/* Sag: Ayarlar */}
        <Link to="/settings">
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
          </Button>
        </Link>
      </header>

      {/* Main Container - Header haric tam ekran */}
      <div className="flex flex-1 h-[calc(100vh-64px)] overflow-hidden">
        {/* Sol Panel - Sidebar */}
        <aside className="w-64 border-r flex flex-col shrink-0">
          <Sidebar />
        </aside>

        <Separator orientation="vertical" />

        {/* Orta Panel - activeTab'e gore Paper List veya Library List */}
        <main className="flex-1 flex flex-col min-w-0">
          {activeTab === 'search' ? <PaperList /> : <LibraryList />}
        </main>

        <Separator orientation="vertical" />

        {/* Sag Panel - Paper Detail */}
        <aside className="w-80 flex flex-col shrink-0">
          <PaperDetail />
        </aside>
      </div>
    </div>
  );
}
