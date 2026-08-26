import { useAuthStore } from "../features/auth/authStore";

export interface CreateAlertDTO  {
    coin_symbol : string,
    activation_price: number | null, 
    is_active:boolean, 
    target_percentage: number | null, 
    target_price: number | null, 
    direction: "UP" | "DOWN"
}

export interface AlertResponse  {
    id: number;
    user_id: number;
    coin_symbol: string;
    activation_price: number | null;
    is_active: boolean;
    target_percentage: number | null;
    target_price: number | null;
    direction: 'UP' | 'DOWN';
    is_triggered: boolean;
    created_at: string;
    updated_at: string; // 👈 Neu hinzugefügt 
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