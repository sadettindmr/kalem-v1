import { test, expect } from '@playwright/test'

// Arama islemleri uzun surebilir (5 provider'dan paralel veri cekilir)
test.setTimeout(120_000)

test.describe('Main Flow: Search and Add to Library', () => {
  test('search for papers and add first result to library', async ({ page }) => {
    // 1. Ana sayfaya git
    await page.goto('/')
    await expect(page).toHaveTitle(/.+/)

    // 2. Arama kutusunu bul ve "Machine Learning" yaz
    const searchInput = page.getByPlaceholder('ornek: machine learning')
    await expect(searchInput).toBeVisible()
    await searchInput.fill('Machine Learning')

    // 3. Arama butonuna tikla
    const searchButton = page.getByRole('button', { name: 'Ara', exact: true })
    await searchButton.click()

    // 4. Sonuclarin yuklenmesini bekle (sonuc sayisi gorunene kadar)
    await expect(page.getByText(/\d+-\d+ \/ \d+ sonuc/)).toBeVisible({ timeout: 90_000 })

    // 5. Ilk sonucun "Kutuphaneme Ekle" butonuna tikla
    const addButton = page.locator('button[title="Kutuphaneme Ekle"]').first()
    await expect(addButton).toBeVisible()
    await addButton.click()

    // 6. Basari toast bildirimini dogrula
    await expect(page.getByText('Makale kutuphaneme eklendi')).toBeVisible({ timeout: 15_000 })
  })
})
