import React, { useState, useMemo } from 'react';
import {
  Search,
  Database,
  Key,
  Link,
  ChevronRight,
  ChevronDown,
  RotateCw,
  Table as TableIcon,
  Eye,
  List,
} from 'lucide-react';
import { TableMeta } from '../../types';
import { Badge, Button, Input } from '../ui/Primitives';

interface TableListProps {
  tables: TableMeta[];
  selectedTable: string | null;
  onSelectTable: (tableName: string) => void;
  onRefreshSchema: () => Promise<void>;
  isRefreshing: boolean;
}

export const TableList: React.FC<TableListProps> = ({
  tables,
  selectedTable,
  onSelectTable,
  onRefreshSchema,
  isRefreshing,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({});
  const [activeTabPerTable, setActiveTabPerTable] = useState<Record<string, 'columns' | 'samples'>>({});

  // Auto-expand selected table
  React.useEffect(() => {
    if (selectedTable) {
      setExpandedTables((prev) => ({ ...prev, [selectedTable]: true }));
    }
  }, [selectedTable]);

  // Filter tables by name or columns
  const filteredTables = useMemo(() => {
    if (!searchQuery.trim()) return tables;
    const q = searchQuery.toLowerCase();
    return tables.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.columns.some((col) => col.toLowerCase().includes(q))
    );
  }, [tables, searchQuery]);

  const toggleExpand = (tableName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedTables((prev) => ({
      ...prev,
      [tableName]: !prev[tableName],
    }));
    onSelectTable(tableName);
  };

  const setTableTab = (tableName: string, tab: 'columns' | 'samples', e: React.MouseEvent) => {
    e.stopPropagation();
    setActiveTabPerTable((prev) => ({ ...prev, [tableName]: tab }));
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-xl border border-border-subtle overflow-hidden">
      {/* Search and Header Toolbar */}
      <div className="p-space-4 border-b border-border-subtle bg-canvas/40 flex flex-col gap-space-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-accent-primary" />
            <h3 className="text-sm font-semibold text-primary">Discovered Tables</h3>
            <Badge variant="neutral" className="text-[10px] font-mono">
              {tables.length}
            </Badge>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={onRefreshSchema}
            disabled={isRefreshing}
            isLoading={isRefreshing}
            className="h-8 min-h-[32px] px-2.5 text-xs gap-1"
            title="Refresh schema reflection"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh Schema</span>
          </Button>
        </div>

        <div className="relative w-full">
          <Search className="w-3.5 h-3.5 text-secondary absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <Input
            placeholder="Filter tables or columns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-xs bg-input"
          />
        </div>
      </div>

      {/* Accordion List */}
      <div className="flex-1 overflow-y-auto p-space-2 divide-y divide-border-subtle/50">
        {filteredTables.length === 0 ? (
          <div className="p-space-6 text-center text-secondary text-xs">
            No tables matching "{searchQuery}"
          </div>
        ) : (
          filteredTables.map((table) => {
            const isExpanded = !!expandedTables[table.name];
            const isSelected = selectedTable === table.name;
            const currentTab = activeTabPerTable[table.name] || 'columns';

            return (
              <div
                key={table.name}
                className={`transition-colors rounded-lg overflow-hidden my-1 ${
                  isSelected ? 'bg-canvas border border-accent-primary/40' : 'hover:bg-canvas/50'
                }`}
              >
                {/* Table Header Row */}
                <div
                  onClick={(e) => {
                    onSelectTable(table.name);
                    toggleExpand(table.name, e);
                  }}
                  className="flex items-center justify-between p-space-3 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-secondary text-xs">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-accent-primary" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </span>
                    <TableIcon className="w-4 h-4 text-accent-primary shrink-0" />
                    <span className="font-semibold text-xs text-primary truncate">
                      {table.name}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge variant="neutral" className="text-[10px] font-mono py-0">
                      {table.columns.length} cols
                    </Badge>
                    <Badge variant="info" className="text-[10px] font-mono py-0">
                      {table.row_count} rows
                    </Badge>
                  </div>
                </div>

                {/* Expanded Details Pane */}
                {isExpanded && (
                  <div className="px-space-3 pb-space-3 pt-1 border-t border-border-subtle/60 bg-card/60">
                    {/* View Switcher: Columns vs Sample Rows */}
                    <div className="flex items-center gap-1 mb-space-2 border-b border-border-subtle pb-1.5">
                      <Button
                        variant={currentTab === 'columns' ? 'primary' : 'ghost'}
                        size="sm"
                        onClick={(e) => setTableTab(table.name, 'columns', e)}
                        className="h-7 min-h-[28px] px-2 text-[11px] gap-1"
                      >
                        <List className="w-3 h-3" />
                        <span>Columns ({table.columns.length})</span>
                      </Button>
                      <Button
                        variant={currentTab === 'samples' ? 'primary' : 'ghost'}
                        size="sm"
                        onClick={(e) => setTableTab(table.name, 'samples', e)}
                        className="h-7 min-h-[28px] px-2 text-[11px] gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Sample Rows</span>
                      </Button>
                    </div>

                    {/* Columns Tab */}
                    {currentTab === 'columns' && (
                      <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
                        {table.columns.map((colName) => {
                          const colType = table.column_types?.[colName] || 'UNKNOWN';
                          const isPk = table.primary_keys?.includes(colName);
                          const fkInfo = table.foreign_keys?.find((fk) =>
                            fk.constrained.includes(colName)
                          );

                          return (
                            <div
                              key={colName}
                              className="flex items-center justify-between p-1.5 rounded-md bg-canvas/70 border border-border-subtle/40 text-[11px]"
                            >
                              <div className="flex items-center gap-1.5 min-w-0">
                                {isPk && (
                                  <span title="Primary Key" className="text-status-success shrink-0">
                                    <Key className="w-3 h-3" />
                                  </span>
                                )}
                                {fkInfo && (
                                  <span title="Foreign Key" className="text-accent-primary shrink-0">
                                    <Link className="w-3 h-3" />
                                  </span>
                                )}
                                <span className="font-mono text-primary font-medium truncate">
                                  {colName}
                                </span>
                              </div>

                              <div className="flex items-center gap-1 shrink-0">
                                {isPk && (
                                  <Badge variant="success" className="text-[9px] py-0">
                                    PK
                                  </Badge>
                                )}
                                {fkInfo && (
                                  <Badge
                                    variant="info"
                                    className="text-[9px] py-0 font-mono"
                                    title={`FK ➔ ${fkInfo.referred_table}.${fkInfo.referred_columns.join(',')}`}
                                  >
                                    FK ➔ {fkInfo.referred_table}
                                  </Badge>
                                )}
                                <Badge variant="neutral" className="text-[9px] font-mono py-0 uppercase">
                                  {colType}
                                </Badge>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Sample Rows Preview Tab */}
                    {currentTab === 'samples' && (
                      <div className="overflow-x-auto max-h-56 border border-border-subtle rounded-md bg-canvas">
                        {table.sample_rows && table.sample_rows.length > 0 ? (
                          <table className="w-full text-left text-[11px] border-collapse font-mono">
                            <thead className="bg-canvas/90 border-b border-border-subtle sticky top-0">
                              <tr>
                                {(table.sample_columns || table.columns).map((c) => (
                                  <th
                                    key={c}
                                    className="p-1.5 text-secondary uppercase font-semibold text-[10px] whitespace-nowrap"
                                  >
                                    {c}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border-subtle/50">
                              {table.sample_rows.slice(0, 3).map((row, rIdx) => (
                                <tr key={rIdx} className="hover:bg-card/50">
                                  {row.map((cell, cIdx) => (
                                    <td
                                      key={cIdx}
                                      className="p-1.5 text-primary truncate max-w-[120px]"
                                      title={cell !== null ? String(cell) : 'NULL'}
                                    >
                                      {cell !== null ? String(cell) : <span className="text-muted">NULL</span>}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          <div className="p-space-4 text-center text-muted text-xs">
                            No sample rows available.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
