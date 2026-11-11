import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  TableMeta,
  QueryTurn,
  AuditLogEntry,
  ConnectionState,
} from '../types';
import { api } from '../services/api';

const DEFAULT_BLOCKED_COLUMNS = [
  'salary',
  'bonus',
  'compensation',
  'wage',
  'premium',
  'adines_number',
  'national_id',
  'ssn',
];

interface StoreContextType {
  // Connection state
  connection: ConnectionState;
  tablesMeta: TableMeta[];
  isSchemaLoading: boolean;
  refreshSchema: () => Promise<void>;
  connectDemo: () => Promise<void>;
  connectCustom: (uri: string) => Promise<void>;
  uploadSqlite: (file: File) => Promise<void>;

  // Query state
  history: QueryTurn[];
  isQuerying: boolean;
  activeQuestion: string;
  useFewShot: boolean;
  showSql: boolean;
  setActiveQuestion: (q: string) => void;
  setUseFewShot: (val: boolean) => void;
  setShowSql: (val: boolean) => void;
  askQuestion: (question: string) => Promise<QueryTurn>;
  clearHistory: () => void;

  // Policy & Governance state
  blockedColumns: string[];
  customRules: string;
  setBlockedColumns: (cols: string[]) => void;
  setCustomRules: (rules: string) => void;

  // Audit state
  auditLogs: AuditLogEntry[];
  auditTotal: number;
  selectedTrace: AuditLogEntry | null;
  setSelectedTrace: (entry: AuditLogEntry | null) => void;
  fetchAuditLogs: () => Promise<void>;

  // System latency & health
  apiLatencyMs: number | null;
  backendConnected: boolean;
  errorMessage: string | null;
  clearError: () => void;
}

const StoreContext = createContext<StoreContextType | undefined>(undefined);

export const StoreProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Connection state
  const [connection, setConnection] = useState<ConnectionState>({
    mode: 'demo',
    status: 'connected',
    dialect: 'SQLITE',
    displayName: 'Local HR ERP (Demo)',
    tableCount: 4,
    databaseUrl: null,
  });
  const [tablesMeta, setTablesMeta] = useState<TableMeta[]>([]);
  const [isSchemaLoading, setIsSchemaLoading] = useState(false);

  // Query state
  const [history, setHistory] = useState<QueryTurn[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const [activeQuestion, setActiveQuestion] = useState('');
  const [useFewShot, setUseFewShot] = useState(false);
  const [showSql, setShowSql] = useState(true);

  // Policy state
  const [blockedColumns, setBlockedColumns] = useState<string[]>(DEFAULT_BLOCKED_COLUMNS);
  const [customRules, setCustomRules] = useState('');

  // Audit state
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [selectedTrace, setSelectedTrace] = useState<AuditLogEntry | null>(null);

  // System health & error
  const [apiLatencyMs, setApiLatencyMs] = useState<number | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const clearError = () => setErrorMessage(null);

  // Schema refresher
  const refreshSchema = useCallback(async () => {
    setIsSchemaLoading(true);
    try {
      const data = await api.getSchema(true);
      setTablesMeta(data.tables || []);
      setConnection((prev) => ({
        ...prev,
        tableCount: data.tables?.length || prev.tableCount,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reflect schema';
      setErrorMessage(msg);
    } finally {
      setIsSchemaLoading(false);
    }
  }, []);

  // Health probe & initial bootstrap
  useEffect(() => {
    let isMounted = true;
    const probeHealth = async () => {
      const start = performance.now();
      try {
        const health = await api.getHealth();
        const duration = Math.round(performance.now() - start);
        if (!isMounted) return;
        setApiLatencyMs(duration);
        setBackendConnected(true);
        setConnection((prev) => ({
          ...prev,
          status: health.database_connected ? 'connected' : 'error',
          dialect: (health.dialect || prev.dialect).toUpperCase(),
        }));
      } catch {
        if (!isMounted) return;
        setBackendConnected(false);
        setApiLatencyMs(null);
      }
    };

    probeHealth();
    refreshSchema();

    const interval = setInterval(probeHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [refreshSchema]);

  // Connect demo database
  const connectDemo = async () => {
    setConnection((prev) => ({ ...prev, status: 'connecting' }));
    try {
      const res = await api.connectDatabase({ mode: 'demo' });
      setConnection({
        mode: 'demo',
        status: 'connected',
        dialect: (res.dialect || 'SQLITE').toUpperCase(),
        displayName: res.display_name || 'Local HR ERP (Demo)',
        tableCount: res.table_count || 4,
        databaseUrl: null,
      });
      await refreshSchema();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Demo connection failed';
      setConnection((prev) => ({ ...prev, status: 'error' }));
      setErrorMessage(msg);
    }
  };

  // Connect custom database URI
  const connectCustom = async (uri: string) => {
    setConnection((prev) => ({ ...prev, status: 'connecting' }));
    try {
      const res = await api.connectDatabase({ mode: 'custom', custom_uri: uri });
      setConnection({
        mode: 'custom',
        status: 'connected',
        dialect: (res.dialect || 'SQL').toUpperCase(),
        displayName: res.display_name || 'Custom Database',
        tableCount: res.table_count || 0,
        databaseUrl: uri,
      });
      await refreshSchema();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connection failed to database URI';
      setConnection((prev) => ({ ...prev, status: 'error' }));
      setErrorMessage(msg);
      throw err;
    }
  };

  // Upload SQLite database file
  const uploadSqlite = async (file: File) => {
    setConnection((prev) => ({ ...prev, status: 'connecting' }));
    try {
      const res = await api.uploadSqliteDatabase(file);
      setConnection({
        mode: 'upload',
        status: 'connected',
        dialect: 'SQLITE',
        displayName: res.display_name || file.name,
        tableCount: res.table_count || 0,
        databaseUrl: null,
      });
      await refreshSchema();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'SQLite upload failed';
      setConnection((prev) => ({ ...prev, status: 'error' }));
      setErrorMessage(msg);
      throw err;
    }
  };

  // Ask question
  const askQuestion = async (question: string): Promise<QueryTurn> => {
    setIsQuerying(true);
    try {
      const turn = await api.askQuery({
        question,
        use_few_shot: useFewShot,
        blocked_columns: blockedColumns,
        custom_rules: customRules,
      });
      setHistory((prev) => [...prev, turn]);
      return turn;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to query database';
      setErrorMessage(msg);
      throw err;
    } finally {
      setIsQuerying(false);
    }
  };

  const clearHistory = () => {
    setHistory([]);
  };

  // Fetch audit logs
  const fetchAuditLogs = async () => {
    try {
      const res = await api.getAuditLogs(50, 0, 'all');
      setAuditLogs(res.logs || []);
      setAuditTotal(res.total || 0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load audit logs';
      setErrorMessage(msg);
    }
  };

  return (
    <StoreContext.Provider
      value={{
        connection,
        tablesMeta,
        isSchemaLoading,
        refreshSchema,
        connectDemo,
        connectCustom,
        uploadSqlite,
        history,
        isQuerying,
        activeQuestion,
        useFewShot,
        showSql,
        setActiveQuestion,
        setUseFewShot,
        setShowSql,
        askQuestion,
        clearHistory,
        blockedColumns,
        customRules,
        setBlockedColumns,
        setCustomRules,
        auditLogs,
        auditTotal,
        selectedTrace,
        setSelectedTrace,
        fetchAuditLogs,
        apiLatencyMs,
        backendConnected,
        errorMessage,
        clearError,
      }}
    >
      {children}
    </StoreContext.Provider>
  );
};

export function useStore() {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error('useStore must be used within a StoreProvider');
  }
  return context;
}
