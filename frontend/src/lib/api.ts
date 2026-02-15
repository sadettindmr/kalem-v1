/**
 * Merkezi API Client
 * Axios instance ve interceptor'lar
 */

import axios, { AxiosError, type AxiosResponse } from 'axios';
import { toast } from 'sonner';
import type { ErrorResponse } from '@/types/api';

// Axios instance oluştur
const api = axios.create({
  baseURL: '/api/v2',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 180 saniye (5 kaynak paralel arama)
});

// Request Interceptor - localStorage'dan API key varsa header'a ekle
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('semantic_scholar_api_key');
  if (apiKey) {
    config.headers['x-api-key'] = apiKey;
  }
  return config;
});

// Response Interceptor
api.interceptors.response.use(
  // Başarılı yanıtlarda response.data döndür
  (response: AxiosResponse) => {
    return response.data;
  },

  // Hata durumunda (4xx, 5xx)
  (error: AxiosError<ErrorResponse>) => {
    // Backend'den gelen standart hata formatını kontrol et
    if (error.response?.data?.error) {
      const { message, suggestion } = error.response.data.error;

      // Toast ile kullanıcıya göster
      let toastMessage = `Hata: ${message}`;
      if (suggestion) {
        toastMessage += `\nOneri: ${suggestion}`;
      }

      toast.error(toastMessage, {
        duration: 5000,
        description: suggestion || undefined,
      });
    } else if (error.message === 'Network Error') {
      // Ağ hatası
      toast.error('Baglanti hatasi', {
        description: 'Sunucuya baglanilamiyor. Lutfen internet baglantinizi kontrol edin.',
        duration: 5000,
      });
    } else if (error.code === 'ECONNABORTED') {
      // Timeout
      toast.error('Istek zaman asimina ugradi', {
        description: 'Sunucu yanitlamiyor. Lutfen daha sonra tekrar deneyin.',
        duration: 5000,
      });
    } else {
      // Genel hata
      toast.error('Beklenmeyen bir hata olustu', {
        description: error.message,
        duration: 5000,
      });
    }

    return Promise.reject(error);
  }
);

export default api;
