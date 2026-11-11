import {
  HealthResponse,
  TableMeta,
  QueryTurn,
  AuditLogEntry,
} from '../types';

export interface ConnectPayload {
  mode: 'demo' | 'custom';
  custom_uri?: string;
}

export interface ConnectResponse {
  success: boolean;
  dialect: string;
  display_name: string;
  table_count: number;
}

export interface AskPayload {
  question: string;
  use_few_shot?: boolean;
  blocked_columns?: string[];
  custom_rules?: string;
}

export interface AuditLogsResponse {
  total: number;
  logs: AuditLogEntry[];
}

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore json parse error on non-json error responses
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: async (): Promise<HealthResponse> => {
    return request<HealthResponse>('/api/health');
  },

  connectDatabase: async (payload: ConnectPayload): Promise<ConnectResponse> => {
    return request<ConnectResponse>('/api/connection/connect', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  uploadSqliteDatabase: async (file: File): Promise<ConnectResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    return request<ConnectResponse>('/api/connection/upload', {
      method: 'POST',
      body: formData,
    });
  },

  getSchema: async (refresh = false): Promise<{ tables: TableMeta[] }> => {
    const query = refresh ? '?refresh=true' : '';
    return request<{ tables: TableMeta[] }>(`/api/schema${query}`);
  },

  askQuery: async (payload: AskPayload): Promise<QueryTurn> => {
    return request<QueryTurn>('/api/query/ask', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getAuditLogs: async (
    limit = 50,
    offset = 0,
    status = 'all'
  ): Promise<AuditLogsResponse> => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
      status,
    });
    return request<AuditLogsResponse>(`/api/audit/logs?${params.toString()}`);
  },
};
