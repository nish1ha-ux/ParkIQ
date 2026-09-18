const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// Simple state management for auth tokens
export const getAuthToken = (): string | null => {
  return localStorage.getItem("parkiq_jwt_token");
};

export const setAuthToken = (token: string | null) => {
  if (token) {
    localStorage.setItem("parkiq_jwt_token", token);
  } else {
    localStorage.removeItem("parkiq_jwt_token");
  }
};

export const getUserRole = (): string | null => {
  return localStorage.getItem("parkiq_user_role");
};

export const setUserRole = (role: string | null) => {
  if (role) {
    localStorage.setItem("parkiq_user_role", role);
  } else {
    localStorage.removeItem("parkiq_user_role");
  }
};

// Generic fetch wrapper with Authorization header
async function request<T>(
  endpoint: string,
  method: string = "GET",
  body: any = null,
  customHeaders: any = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: any = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    method,
    headers,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Authentication
  auth: {
    login: async (email: string, password: string): Promise<any> => {
      const data = await request<any>("/auth/login", "POST", { email, password });
      setAuthToken(data.access_token);
      setUserRole(data.user.role);
      return data;
    },
    register: async (payload: any): Promise<any> => {
      return request<any>("/auth/register", "POST", payload);
    },
    logout: () => {
      setAuthToken(null);
      setUserRole(null);
    }
  },

  // Vehicles
  vehicles: {
    list: async (): Promise<any[]> => {
      return request<any[]>("/vehicles");
    },
    create: async (payload: { license_plate: string; vehicle_type: string }): Promise<any> => {
      return request<any>("/vehicles", "POST", payload);
    }
  },

  // Sessions & Lots
  sessions: {
    lots: async (): Promise<any[]> => {
      return request<any[]>("/sessions/lots");
    },
    slots: async (lotId: string): Promise<any[]> => {
      return request<any[]>(`/sessions/lots/${lotId}/slots`);
    },
    start: async (payload: { qr_token: string; slot_id: string; expected_duration_minutes: number }): Promise<any> => {
      return request<any>("/sessions/start", "POST", payload);
    },
    end: async (payload: { qr_token: string }): Promise<any> => {
      return request<any>("/sessions/end", "POST", payload);
    },
    extend: async (sessionId: string, payload: { additional_minutes: number }): Promise<any> => {
      return request<any>(`/sessions/${sessionId}/extend`, "POST", payload);
    },
    active: async (): Promise<any[]> => {
      return request<any[]>("/sessions/active");
    },
    history: async (): Promise<any[]> => {
      return request<any[]>("/sessions/history");
    }
  },

  // QR Engine
  qr: {
    verify: async (payload: { qr_token: string }): Promise<any> => {
      return request<any>("/qr/verify", "POST", payload);
    },
    publicStatus: async (qrToken: string): Promise<any> => {
      return request<any>(`/qr/public-status/${encodeURIComponent(qrToken)}`);
    }
  },

  // AI Predict endpoints
  ai: {
    predict: async (payload: { lot_id: string; time_offset_hours: number }): Promise<any> => {
      return request<any>("/ai/predict", "POST", payload);
    },
    departure: async (payload: { entry_time?: string; vehicle_type?: string; floor_level?: number }): Promise<any> => {
      return request<any>("/ai/predict/departure", "POST", payload);
    },
    occupancy: async (payload: { lot_id: string; current_occupancy_pct: number; time_offset_hours?: number }): Promise<any> => {
      return request<any>("/ai/predict/occupancy", "POST", payload);
    },
    recommendSlot: async (payload: { lot_id: string; vehicle_type?: string }): Promise<any> => {
      return request<any>("/ai/recommend-slot", "POST", payload);
    },
    detectFraud: async (payload: { time_delta_sec: number; distance_km: number }): Promise<any> => {
      return request<any>("/ai/detect-fraud", "POST", payload);
    },
    train: async (): Promise<any> => {
      return request<any>("/ai/train", "POST");
    }
  },

  // RAG Chat Assistant
  rag: {
    chat: async (question: string): Promise<any> => {
      return request<any>("/rag/chat", "POST", { question });
    }
  }
};
