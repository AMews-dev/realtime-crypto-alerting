import type { AlertResponse } from "./alertsApi"

export async function customFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const fetchOptions: RequestInit = {
    ...options,
    credentials: "include"
    }

    let response = await fetch(url, fetchOptions)

    if (response.status == 401) {
        console.log("acces token abgelaufen")

        const refreshRespone = await fetch("http/localhost:8000/api/auth/refresh", {
            method:"POST",
            credentials: "include"
        })
        if  (refreshRespone.ok) {
            response = await fetch(url, fetchOptions)
        } else {
            console.error("refresh token ungültig")
            window.location.href = "/login"
        }
    }
    return response
} 

 export async function getAlerts(): Promise<AlertResponse[]> {
  const res = await customFetch('http://localhost:8000/api/alerts');
  if (!res.ok) throw new Error('Fehler beim Laden');
  return res.json();
}