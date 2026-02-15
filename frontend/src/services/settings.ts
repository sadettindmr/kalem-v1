import api from '@/lib/api';
import type { UserSettingsResponse, UserSettingsUpdateRequest } from '@/types/api';

export async function fetchSettings(): Promise<UserSettingsResponse> {
  return api.get<never, UserSettingsResponse>('/system/settings');
}

export async function updateSettings(
  payload: UserSettingsUpdateRequest
): Promise<UserSettingsResponse> {
  return api.put<never, UserSettingsResponse>('/system/settings', payload);
}

// Backward-compatible aliases
export const fetchSystemSettings = fetchSettings;
export const updateSystemSettings = updateSettings;
