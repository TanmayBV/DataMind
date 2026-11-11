import React, { useState, useMemo } from 'react';
import {
  Download,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ShieldAlert,
  AlertTriangle,
  Info,
  Clock,
  Database,
  FileSpreadsheet,
  FileCode,
} from 'lucide-react';
import { Card, Badge, Button, Input } from '../ui/Primitives';
import { QueryStatus } from '../../types';

interface DataTableProps {
  columns: string[] | null;
  rows: (string | number | boolean | null)[][] | null;
  status: QueryStatus;
  errorMessage: string | null;
  latencyMs?: number;
}

type SortDirection = 'asc' | 'desc' | null;

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  status,
  errorMessage,
  latencyMs,
}) => {
  // Local state for searching, sorting, and pagination
  const [filterText, setFilterText] = useState('');
  const [sortColumnIndex, setSortColumnIndex] = useState<number | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [pageSize, setPageSize] = useState<number>(10);
  const [pageIndex, setPageIndex] = useState<number>(0);

  // 1. Policy Refusal Banner
  if (status === 'refused') {
    return (
      <div className="w-full rounded-xl bg-status-warning-bg border border-status-warning/30 p-space-4 my-space-3">
        <div className="flex items-start gap-space-3">
          <div className="p-2 rounded-lg bg-status-warning/10 text-status-warning shrink-0 mt-0.5">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-status-warning mb-1">
              Blocked by Business Safety Policy
            </h4>
            <p className="text-xs text-primary leading-relaxed mb-2">
              {errorMessage ||
                'Query Refused: Your question requests sensitive financial or personal data (salary, SSN, bonus) restricted by policy.'}
            </p>
            <div className="text-xs text-secondary bg-canvas/60 rounded-lg p-space-2 border border-border-subtle inline-block">
              <span className="font-semibold text-primary">Remediation: </span>
              Rephrase question to request non-sensitive operational attributes (e.g. employee count, department, job roles).
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2. AST Validation Rejection Banner
  if (status === 'invalid' || (status === 'error' && !rows)) {
    return (
      <div className="w-full rounded-xl bg-status-error-bg border border-status-error/30 p-space-4 my-space-3">
        <div className="flex items-start gap-space-3">
          <div className="p-2 rounded-lg bg-status-error/10 text-status-error shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-status-error mb-1">
              AST Validation Error
            </h4>
            <p className="text-xs text-primary leading-relaxed font-mono">
              {errorMessage || 'Generated query violated safety rules or referenced unknown schema objects.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 3. Empty Set Callout
  if (!rows || rows.length === 0) {
    return (
      <div className="w-full rounded-xl bg-canvas border border-border-subtle p-space-6 text-center my-space-3">
        <div className="w-10 h-10 rounded-full bg-status-info/10 text-status-info flex items-center justify-center mx-auto mb-space-2">
          <Info className="w-5 h-5" />
        </div>
        <h4 className="text-sm font-semibold text-primary mb-1">No Records Found</h4>
        <p className="text-xs text-secondary max-w-sm mx-auto">
          The query executed safely{latencyMs ? ` in ${(latencyMs / 1000).toFixed(2)}s` : ''}, but returned 0 rows matching your filter criteria.
        </p>
      </div>
    );
  }

  // 4. Scalar KPI Metric Card (Single Column, Single Row)
  const isScalar = columns && columns.length === 1 && rows.length === 1;
  if (isScalar) {
    const rawVal = rows[0][0];
    const displayVal = rawVal !== null && rawVal !== undefined ? String(rawVal) : '0';
    const label = columns[0].replace(/_/g, ' ').toUpperCase();

    return (
      <Card className="my-space-3 bg-card border-border-subtle hover:border-border-prominent transition-all">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-secondary uppercase tracking-wider mb-1">
              {label}
            </div>
            <div className="text-2xl font-bold text-primary tracking-tight">
              {displayVal}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge variant="success">Result Ready</Badge>
            {latencyMs !== undefined && (
              <span className="text-[11px] text-muted flex items-center gap-1 font-mono">
                <Clock className="w-3 h-3" />
                {(latencyMs / 1000).toFixed(2)}s
              </span>
            )}
          </div>
        </div>
      </Card>
    );
  }

  // 5. Multi-Row Tabular View
  // Filter rows based on search input
  const filteredRows = useMemo(() => {
    if (!filterText.trim()) return rows;
    const query = filterText.toLowerCase();
    return rows.filter((row) =>
      row.some((cell) => cell !== null && String(cell).toLowerCase().includes(query))
    );
  }, [rows, filterText]);

  // Sort rows based on sort column & direction
  const sortedRows = useMemo(() => {
    if (sortColumnIndex === null || !sortDirection) return filteredRows;

    return [...filteredRows].sort((a, b) => {
      const valA = a[sortColumnIndex];
      const valB = b[sortColumnIndex];

      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      // Numeric comparison
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDirection === 'asc' ? valA - valB : valB - valA;
      }

      // String comparison
      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      if (strA < strB) return sortDirection === 'asc' ? -1 : 1;
      if (strA > strB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredRows, sortColumnIndex, sortDirection]);

  // Paginate rows
  const totalPages = Math.ceil(sortedRows.length / pageSize) || 1;
  const currentRows = useMemo(() => {
    const start = pageIndex * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, pageIndex, pageSize]);

  const handleHeaderClick = (colIdx: number) => {
    if (sortColumnIndex !== colIdx) {
      setSortColumnIndex(colIdx);
      setSortDirection('asc');
    } else if (sortDirection === 'asc') {
      setSortDirection('desc');
    } else {
      setSortColumnIndex(null);
      setSortDirection(null);
    }
  };

  // Threat T-ui-10 mitigation: Sanitize CSV values
  const sanitizeCsvCell = (val: unknown): string => {
    if (val === null || val === undefined) return '';
    let str = String(val);
    // Formula injection mitigation: prefix =, +, -, @ with single quote '
    if (/^[=+\-@]/.test(str)) {
      str = `'${str}`;
    }
    // Escape quotes and wrap in quotes if contains comma, quote, or newline
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      str = `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const handleExportCsv = () => {
    if (!columns || !rows) return;
    const headerRow = columns.map(sanitizeCsvCell).join(',');
    const bodyRows = rows.map((r) => r.map(sanitizeCsvCell).join(',')).join('\n');
    const csvContent = `${headerRow}\n${bodyRows}`;

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `datamind_query_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJson = () => {
    if (!columns || !rows) return;
    const records = rows.map((row) => {
      const obj: Record<string, unknown> = {};
      columns.forEach((col, idx) => {
        obj[col] = row[idx];
      });
      return obj;
    });

    const jsonContent = JSON.stringify(records, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `datamind_query_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full my-space-3 rounded-xl bg-card border border-border-subtle overflow-hidden">
      {/* Table Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-space-3 p-space-4 border-b border-border-subtle bg-canvas/40">
        <div className="flex items-center gap-space-2 flex-1 min-w-[240px]">
          <div className="relative w-full max-w-xs">
            <Search className="w-4 h-4 text-secondary absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <Input
              placeholder="Search result rows..."
              value={filterText}
              onChange={(e) => {
                setFilterText(e.target.value);
                setPageIndex(0);
              }}
              className="pl-9 h-9 text-xs"
            />
          </div>
          <Badge variant="neutral" className="font-mono text-[11px] whitespace-nowrap">
            <Database className="w-3 h-3 mr-1" />
            {rows.length} {rows.length === 1 ? 'row' : 'rows'}
          </Badge>
        </div>

        <div className="flex items-center gap-space-2">
          {/* Export CSV CTA */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            className="h-9 min-h-[36px] px-space-3 text-xs gap-1"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </Button>

          {/* Export JSON CTA */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJson}
            className="h-9 min-h-[36px] px-space-3 text-xs gap-1"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </Button>
        </div>
      </div>

      {/* Tabular Data View */}
      <div className="overflow-x-auto max-h-[440px]">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-canvas sticky top-0 z-10 border-b border-border-subtle select-none">
            <tr>
              {columns?.map((col, idx) => {
                const isSorted = sortColumnIndex === idx;
                return (
                  <th
                    key={col}
                    onClick={() => handleHeaderClick(idx)}
                    className="p-space-3 font-semibold text-secondary uppercase tracking-wider text-[11px] hover:bg-canvas/80 cursor-pointer transition-colors whitespace-nowrap"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>{col}</span>
                      {isSorted ? (
                        sortDirection === 'asc' ? (
                          <ArrowUp className="w-3 h-3 text-accent-primary" />
                        ) : (
                          <ArrowDown className="w-3 h-3 text-accent-primary" />
                        )
                      ) : (
                        <ArrowUpDown className="w-3 h-3 text-muted/60 opacity-60" />
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle font-mono">
            {currentRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns?.length || 1}
                  className="p-space-6 text-center text-secondary text-xs"
                >
                  No matching rows found for "{filterText}".
                </td>
              </tr>
            ) : (
              currentRows.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  className="hover:bg-canvas/60 transition-colors"
                >
                  {row.map((cell, cellIdx) => (
                    <td
                      key={cellIdx}
                      className="p-space-3 text-primary truncate max-w-[280px]"
                      title={cell !== null ? String(cell) : 'NULL'}
                    >
                      {cell === null ? (
                        <span className="text-muted italic">NULL</span>
                      ) : typeof cell === 'boolean' ? (
                        <Badge variant={cell ? 'success' : 'neutral'} className="text-[10px]">
                          {String(cell)}
                        </Badge>
                      ) : (
                        String(cell)
                      )}
                    </td>
                  ))}
                </tr>
              ))
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
            className="bg-input border border-border-subtle rounded-md px-2 py-1 text-xs text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
          <span className="text-muted text-[11px] ml-2">
            Showing {filteredRows.length > 0 ? pageIndex * pageSize + 1 : 0} to{' '}
            {Math.min((pageIndex + 1) * pageSize, filteredRows.length)} of {filteredRows.length}
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
