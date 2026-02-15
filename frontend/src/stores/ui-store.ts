import { create } from 'zustand';
import type { PaperResponse, PaperSource, SearchMeta } from '@/types/api';

type State = {
  isSidebarOpen: boolean;
  activeTab: 'search' | 'library';
  selectedPaperId: string | null;
  searchResults: PaperResponse[];
  isSearching: boolean;
  lastSearchQuery: string;
  // Pagination
  currentPage: number;
  itemsPerPage: number;
  // Selection (bulk save)
  selectedPaperIds: Set<string>;
  // Saved papers tracking
  savedPaperIds: Set<string>;
  // Search meta (raw counts + dedup stats)
  searchMeta: SearchMeta | null;
  // Search result filters
  searchFilterMinCitations: number | null;
  searchFilterOpenAccess: boolean;
  searchFilterSource: PaperSource | null;
  // Library filters
  libraryFilterTag: string | null;
  libraryFilterStatus: string | null;
  libraryFilterMinCitations: number | null;
  libraryFilterYearStart: number | null;
  libraryFilterYearEnd: number | null;
  libraryFilterSearch: string;
};

type Actions = {
  toggleSidebar: () => void;
  setActiveTab: (tab: State['activeTab']) => void;
  setSelectedPaperId: (id: string | null) => void;
  setSearchResults: (results: PaperResponse[]) => void;
  setIsSearching: (isSearching: boolean) => void;
  setLastSearchQuery: (query: string) => void;
  setSearchMeta: (meta: SearchMeta | null) => void;
  setCurrentPage: (page: number) => void;
  togglePaperSelection: (id: string) => void;
  selectAllOnPage: () => void;
  clearSelection: () => void;
  setSavedPaperIds: (ids: string[]) => void;
  addSavedPaperIds: (ids: string[]) => void;
  setSearchFilterMinCitations: (value: number | null) => void;
  setSearchFilterOpenAccess: (value: boolean) => void;
  setSearchFilterSource: (value: PaperSource | null) => void;
  setLibraryFilterTag: (tag: string | null) => void;
  setLibraryFilterStatus: (status: string | null) => void;
  setLibraryFilterMinCitations: (value: number | null) => void;
  setLibraryFilterYearStart: (value: number | null) => void;
  setLibraryFilterYearEnd: (value: number | null) => void;
  setLibraryFilterSearch: (value: string) => void;
};

export const useUIStore = create<State & Actions>((set) => ({
  isSidebarOpen: true,
  activeTab: 'search',
  selectedPaperId: null,
  searchResults: [],
  isSearching: false,
  lastSearchQuery: '',
  currentPage: 1,
  itemsPerPage: 100,
  selectedPaperIds: new Set(),
  savedPaperIds: new Set(),
  searchMeta: null,
  searchFilterMinCitations: null,
  searchFilterOpenAccess: false,
  searchFilterSource: null,
  libraryFilterTag: null,
  libraryFilterStatus: null,
  libraryFilterMinCitations: null,
  libraryFilterYearStart: null,
  libraryFilterYearEnd: null,
  libraryFilterSearch: '',
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setActiveTab: (tab) => set({ activeTab: tab, selectedPaperId: null }),
  setSelectedPaperId: (id) => set({ selectedPaperId: id }),
  setSearchResults: (results) => set({
    searchResults: results,
    currentPage: 1,
    selectedPaperIds: new Set(),
    searchMeta: null,
    searchFilterMinCitations: null,
    searchFilterOpenAccess: false,
    searchFilterSource: null,
  }),
  setIsSearching: (isSearching) => set({ isSearching }),
  setLastSearchQuery: (query) => set({ lastSearchQuery: query }),
  setSearchMeta: (meta) => set({ searchMeta: meta }),
  setCurrentPage: (page) => set({ currentPage: page }),
  togglePaperSelection: (id) => set((state) => {
    const next = new Set(state.selectedPaperIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return { selectedPaperIds: next };
  }),
  selectAllOnPage: () => set((state) => {
    const start = (state.currentPage - 1) * state.itemsPerPage;
    const pageResults = state.searchResults.slice(start, start + state.itemsPerPage);
    const ids = new Set(pageResults.map((p, i) => p.external_id || `paper-${start + i}`));
    return { selectedPaperIds: ids };
  }),
  clearSelection: () => set({ selectedPaperIds: new Set() }),
  setSavedPaperIds: (ids) => set({ savedPaperIds: new Set(ids) }),
  addSavedPaperIds: (ids) => set((state) => {
    const next = new Set(state.savedPaperIds);
    ids.forEach((id) => next.add(id));
    return { savedPaperIds: next };
  }),
  setSearchFilterMinCitations: (value) => set({ searchFilterMinCitations: value, currentPage: 1 }),
  setSearchFilterOpenAccess: (value) => set({ searchFilterOpenAccess: value, currentPage: 1 }),
  setSearchFilterSource: (value) => set({ searchFilterSource: value, currentPage: 1 }),
  setLibraryFilterTag: (tag) => set({ libraryFilterTag: tag }),
  setLibraryFilterStatus: (status) => set({ libraryFilterStatus: status }),
  setLibraryFilterMinCitations: (value) => set({ libraryFilterMinCitations: value }),
  setLibraryFilterYearStart: (value) => set({ libraryFilterYearStart: value }),
  setLibraryFilterYearEnd: (value) => set({ libraryFilterYearEnd: value }),
  setLibraryFilterSearch: (value) => set({ libraryFilterSearch: value }),
}));
