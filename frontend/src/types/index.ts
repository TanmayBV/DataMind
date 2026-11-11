export interface ForeignKey {
  constrained: string[];
  referred_table: string;
  referred_columns: string[];
}

export interface ColumnMeta {
  name: string;
  type: string;
  is_primary?: boolean;
  is_foreign?: boolean;
  is_sensitive?: boolean;
}

export interface TableMeta {
  name: string;
  columns: string[];
  column_types: Record<string, string>;
  primary_keys: string[];
  foreign_keys: ForeignKey[];
  row_count: number;
  sample_columns: string[];
  sample_rows: (string | number | boolean | null)[][];
}

export interface QueryTelemetry {
  retrieval_latency_ms: number;
  llm_latency_ms: number;
  exec_latency_ms: number;
  total_latency_ms: number;
  retrieved_examples_count: number;
}

export type QueryStatus = 'ready' | 'refused' | 'invalid' | 'error';

export interface QueryTurn {
  query_id: string;
  question: string;
  timestamp: string;
  status: QueryStatus;
  is_valid: boolean;
  generated_sql: string;
  columns: string[] | null;
  rows: (string | number | boolean | null)[][] | null;
  error_message: string | null;
  telemetry: QueryTelemetry;
}

export interface AuditLogEntry {
  query_id: string;
  timestamp: string;
  question: string;
  status: string;
  generated_sql: string;
  is_valid: number;
  rows_returned: number;
  retrieval_latency_ms: number;
  llm_latency_ms: number;
  exec_latency_ms: number;
  total_latency_ms: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  llm_provider: string;
  llm_model: string;
  database_connected: boolean;
  dialect: string;
}

export interface ConnectionState {
  mode: 'demo' | 'upload' | 'custom';
  status: 'connected' | 'connecting' | 'error' | 'disconnected';
  dialect: string;
  displayName: string;
  tableCount: number;
  databaseUrl?: string | null;
}
