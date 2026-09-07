import { useAuthStore } from "../features/auth/authStore";
export type AlarmType = 'ABSOLUTE_PRICE' | 'DYNAMIC_PERCENTAGE' | 'TIMEFRAME_PERCENTAGE';
export type AlarmDirection = 'ABOVE' | 'BELOW' | 'BOTH';

export interface CreateAlertDTO  {
    coin_symbol: string;
    alarm_type: AlarmType;
    direction: AlarmDirection;
    target_price: number | null;
    target_percentage: number | null;
    timeframe_minutes: number | null;
    reference_price?: number | null;
}

export interface AlertResponse  {
  id: number;
  user_id: number;
  coin_symbol: string;
  alarm_type: AlarmType;
  direction: AlarmDirection;
  target_price: number | null;
  target_percentage: number | null;
  timeframe_minutes: number | null;
  reference_price: number | null;
  is_triggered: boolean;
  created_at: string;
  updated_at?: string;
}

export async function createAlert(data: CreateAlertDTO) {
    const response = await fetch("http://localhost:8000/create-alert",{
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(data)
    });

    if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Fehler beim Erstellen des Alarms');
  }

  return await response.json()

}