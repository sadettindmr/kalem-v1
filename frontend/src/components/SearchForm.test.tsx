import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SearchForm from './SearchForm'
import { vi } from 'vitest'

// Mock search service
vi.mock('@/services/search', () => ({
  searchPapers: vi.fn().mockResolvedValue({
    results: [],
    meta: {
      total: 0,
      raw_semantic: 0,
      raw_openalex: 0,
      raw_arxiv: 0,
      raw_crossref: 0,
      raw_core: 0,
    },
  }),
}))

// Mock library service
vi.mock('@/services/library', () => ({
  checkLibraryPapers: vi.fn().mockResolvedValue({ saved_ids: [] }),
}))

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <SearchForm />
    </QueryClientProvider>,
  )
}

describe('SearchForm', () => {
  it('renders the form with input fields and search button', () => {
    renderWithProviders()

    expect(screen.getByLabelText('Anahtar Kelimeler')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('ornek: machine learning')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Min')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Max')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ara/i })).toBeInTheDocument()
  })

  it('allows typing into the search input', async () => {
    renderWithProviders()
    const user = userEvent.setup()

    const input = screen.getByPlaceholderText('ornek: machine learning')
    await user.type(input, 'deep learning')

    expect(input).toHaveValue('deep learning')
  })

  it('disables the search button when query is empty', () => {
    renderWithProviders()

    const button = screen.getByRole('button', { name: /ara/i })
    expect(button).toBeDisabled()
  })

  it('enables the search button when query has text', async () => {
    renderWithProviders()
    const user = userEvent.setup()

    const input = screen.getByPlaceholderText('ornek: machine learning')
    await user.type(input, 'test')

    const button = screen.getByRole('button', { name: /ara/i })
    expect(button).toBeEnabled()
  })

  it('submits the form and calls searchPapers', async () => {
    const { searchPapers } = await import('@/services/search')
    renderWithProviders()
    const user = userEvent.setup()

    const input = screen.getByPlaceholderText('ornek: machine learning')
    await user.type(input, 'machine learning')

    const button = screen.getByRole('button', { name: /ara/i })
    await user.click(button)

    expect(searchPapers).toHaveBeenCalledWith({
      query: 'machine learning',
      year_start: null,
      year_end: null,
    })
  })

  it('allows setting year range filters', async () => {
    renderWithProviders()
    const user = userEvent.setup()

    const minYear = screen.getByPlaceholderText('Min')
    const maxYear = screen.getByPlaceholderText('Max')

    await user.type(minYear, '2020')
    await user.type(maxYear, '2025')

    expect(minYear).toHaveValue(2020)
    expect(maxYear).toHaveValue(2025)
  })
})
