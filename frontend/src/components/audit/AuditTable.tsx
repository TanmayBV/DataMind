import React, { useState, useMemo } from 'react';
import { Copy, Check, Eye, Search, Filter } from 'lucide-react';
import { AuditLogEntry } from '../../types';
import { Badge, Button, Input } from '../ui/Primitives';

interface AuditTableProps {
  logs: AuditLogEntry[];
  onSelectTrace: (entry: AuditLogEntry) => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({ logs, onSelectTrace }) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [filterText, setFilterText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [pageSize, setPageSize] = useState(10);
  const [pageIndex, setPageIndex] = useState(0);

  const handleCopyId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesStatus =
        statusFilter === 'all' || log.status.toLowerCase() === statusFilter.toLowerCase();
      const q = filterText.toLowerCase();
      const matchesText =
        !q ||
        log.query_id.toLowerCase().includes(q) ||
        log.question.toLowerCase().includes(q) ||
        log.generated_sql.toLowerCase().includes(q);

      return matchesStatus && matchesText;
    });
  }, [logs, statusFilter, filterText]);

  const totalPages = Math.ceil(filteredLogs.length / pageSize) || 1;
  const currentLogs = useMemo(() => {
    const start = pageIndex * pageSize;
    return filteredLogs.slice(start, start + pageSize);
  }, [filteredLogs, pageIndex, pageSize]);

  const formatTimestamp = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="w-full rounded-xl bg-card border border-border-subtle overflow-hidden">
      {/* Table Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-space-3 p-space-4 border-b border-border-subtle bg-canvas/40">
        <div className="flex items-center gap-space-2 flex-1 min-w-[260px]">
          <div className="relative w-full max-w-xs">
            <Search className="w-4 h-4 text-secondary absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <Input
              placeholder="Search by question or SQL..."
              value={filterText}
              onChange={(e) => {
                setFilterText(e.target.value);
                setPageIndex(0);
              }}
              className="pl-9 h-9 text-xs"
            />
          </div>

          <div className="flex items-center gap-1 bg-input border border-border-subtle rounded-lg px-2 py-1">
            <Filter className="w-3.5 h-3.5 text-secondary" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPageIndex(0);
              }}
              className="bg-transparent text-xs text-primary focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="ready">Ready (Success)</option>
              <option value="refused">Refused</option>
              <option value="invalid">Invalid</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-secondary font-mono">
          {filteredLogs.length} matching {filteredLogs.length === 1 ? 'record' : 'records'}
        </div>
      </div>

      {/* Tabular Records */}
      <div className="overflow-x-auto max-h-[500px]">
        <table className="w-full text-left text-xs border-collapse font-sans">
          <thead className="bg-canvas sticky top-0 z-10 border-b border-border-subtle select-none">
            <tr>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Query ID</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Timestamp</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Question</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Status</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Generated SQL</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Rows</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px]">Latency</th>
              <th className="p-space-3 font-semibold text-secondary uppercase text-[10px] text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-xs">
            {currentLogs.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-space-8 text-center text-secondary text-xs">
                  No audit logs found.
                </td>
              </tr>
            ) : (
              currentLogs.map((log) => {
                const isCopied = copiedId === log.query_id;
                const statusVariant =
                  log.status === 'ready'
                    ? 'success'
                    : log.status === 'refused'
                    ? 'warning'
                    : 'error';

                return (
                  <tr
                    key={log.query_id}
                    onClick={() => onSelectTrace(log)}
                    className="hover:bg-canvas/60 transition-colors cursor-pointer"
                  >
                    {/* Query ID with Copy */}
                    <td className="p-space-3 font-mono text-[11px] whitespace-nowrap">
                      <div className="flex items-center gap-1">
                        <span className="text-secondary">{log.query_id.slice(0, 8)}</span>
                        <button
                          type="button"
                          onClick={(e) => handleCopyId(log.query_id, e)}
                          title="Copy full Query ID"
                          className="p-1 hover:bg-canvas rounded text-muted hover:text-primary transition-colors"
                        >
                          {isCopied ? (
                            <Check className="w-3 h-3 text-status-success" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </td>

                    {/* Timestamp */}
                    <td className="p-space-3 text-secondary text-[11px] whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </td>

                    {/* Question */}
                    <td className="p-space-3 text-primary font-medium max-w-[240px] truncate" title={log.question}>
                      {log.question}
                    </td>

                    {/* Status Badge */}
                    <td className="p-space-3 whitespace-nowrap">
                      <Badge variant={statusVariant} className="uppercase text-[10px]">
                        {log.status}
                      </Badge>
                    </td>

                    {/* SQL Snippet */}
                    <td className="p-space-3 font-mono text-muted text-[11px] max-w-[200px] truncate" title={log.generated_sql}>
                      {log.generated_sql}
                    </td>

                    {/* Rows */}
                    <td className="p-space-3 font-mono text-secondary">
                      {log.rows_returned}
                    </td>

                    {/* Total Latency */}
                    <td className="p-space-3 font-mono text-secondary whitespace-nowrap">
                      {Math.round(log.total_latency_ms)}ms
                    </td>

                    {/* Action Button */}
                    <td className="p-space-3 text-right whitespace-nowrap">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectTrace(log);
                        }}
                        className="h-7 min-h-[28px] px-2 text-[11px] gap-1 text-accent-primary hover:text-accent-hover"
                      >
                        <Eye className="w-3 h-3" />
                        <span>View Trace</span>
                      </Button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between p-space-3 border-t border-border-subtle bg-canvas/40 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-secondary">Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPageIndex(0);
            }}
            className="bg-input border border-border-subtle rounded-md px-2 py-1 text-xs text-primary focus:outline-none"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
          <span className="text-muted text-[11px] ml-2">
            Showing {filteredLogs.length > 0 ? pageIndex * pageSize + 1 : 0} to{' '}
            {Math.min((pageIndex + 1) * pageSize, filteredLogs.length)} of {filteredLogs.length}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            disabled={pageIndex === 0}
            onClick={() => setPageIndex((p) => Math.max(0, p - 1))}
            className="h-8 min-h-[32px] px-2 text-xs"
          >
            Previous
          </Button>
          <span className="text-secondary text-xs px-2">
            Page {pageIndex + 1} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={pageIndex >= totalPages - 1}
            onClick={() => setPageIndex((p) => Math.min(totalPages - 1, p + 1))}
            className="h-8 min-h-[32px] px-2 text-xs"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
};
