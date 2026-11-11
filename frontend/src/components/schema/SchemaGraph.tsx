import React, { useState, useRef, useMemo, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Database, Key, Link as LinkIcon } from 'lucide-react';
import { TableMeta } from '../../types';
import { Button, Badge } from '../ui/Primitives';

interface SchemaGraphProps {
  tables: TableMeta[];
  selectedTable: string | null;
  onSelectTable: (tableName: string) => void;
}

interface NodePosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export const SchemaGraph: React.FC<SchemaGraphProps> = ({
  tables,
  selectedTable,
  onSelectTable,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 40, y: 40 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Calculate node positions in a neat grid/dag layout
  const nodePositions = useMemo(() => {
    const positions: Record<string, NodePosition> = {};
    const nodeWidth = 260;
    const paddingX = 80;
    const paddingY = 60;
    const columnsPerRow = Math.max(2, Math.ceil(Math.sqrt(tables.length)));

    tables.forEach((table, index) => {
      const col = index % columnsPerRow;
      const row = Math.floor(index / columnsPerRow);
      const nodeHeight = 56 + Math.min(table.columns.length, 8) * 26;

      positions[table.name] = {
        x: col * (nodeWidth + paddingX) + 50,
        y: row * (320 + paddingY) + 50,
        width: nodeWidth,
        height: nodeHeight,
      };
    });

    return positions;
  }, [tables]);

  // Extract FK edges
  const edges = useMemo(() => {
    const list: {
      id: string;
      fromTable: string;
      toTable: string;
      fromCol: string;
      toCol: string;
    }[] = [];

    tables.forEach((table) => {
      table.foreign_keys?.forEach((fk) => {
        if (nodePositions[table.name] && nodePositions[fk.referred_table]) {
          list.push({
            id: `${table.name}-${fk.referred_table}-${fk.constrained[0]}`,
            fromTable: table.name,
            toTable: fk.referred_table,
            fromCol: fk.constrained[0],
            toCol: fk.referred_columns[0] || 'id',
          });
        }
      });
    });

    return list;
  }, [tables, nodePositions]);

  // Handle Pan Dragging
  const handleMouseDown = (e: React.MouseEvent) => {
    // Only drag on canvas background
    if ((e.target as HTMLElement).tagName === 'svg' || (e.target as HTMLElement).id === 'graph-canvas') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.15, 2.0));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.15, 0.4));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 40, y: 40 });
  };
  const handleFitView = () => {
    setZoom(0.85);
    setPan({ x: 20, y: 20 });
  };

  return (
    <div
      ref={containerRef}
      id="graph-canvas"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      className="relative w-full h-full min-h-[500px] bg-canvas rounded-xl border border-border-subtle overflow-hidden select-none cursor-grab active:cursor-grabbing"
    >
      {/* Graph Floating Controls */}
      <div className="absolute top-space-4 right-space-4 z-20 flex items-center gap-1 bg-card/90 backdrop-blur-sm border border-border-subtle p-1 rounded-xl shadow-md">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          title="Zoom In"
          className="h-8 w-8 min-h-[32px] min-w-[32px] p-0 text-secondary hover:text-primary"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          title="Zoom Out"
          className="h-8 w-8 min-h-[32px] min-w-[32px] p-0 text-secondary hover:text-primary"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <div className="w-[1px] h-4 bg-border-subtle mx-1" />
        <Button
          variant="ghost"
          size="sm"
          onClick={handleFitView}
          title="Fit View"
          className="h-8 w-8 min-h-[32px] min-w-[32px] p-0 text-secondary hover:text-primary"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          title="Reset Layout"
          className="h-8 w-8 min-h-[32px] min-w-[32px] p-0 text-secondary hover:text-primary"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </Button>
        <span className="text-[10px] font-mono text-muted px-2">
          {Math.round(zoom * 100)}%
        </span>
      </div>

      {/* Canvas Viewport */}
      <div
        className="w-full h-full transform origin-top-left transition-transform duration-75"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
        }}
      >
        {/* SVG Edges Layer */}
        <svg
          className="absolute inset-0 pointer-events-none"
          style={{ width: 2500, height: 2000 }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="6"
              refX="7"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="var(--color-accent-primary, #3b82f6)" />
            </marker>
            <marker
              id="arrowhead-highlight"
              markerWidth="8"
              markerHeight="6"
              refX="7"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#10B981" />
            </marker>
          </defs>

          {edges.map((edge) => {
            const source = nodePositions[edge.fromTable];
            const target = nodePositions[edge.toTable];
            if (!source || !target) return null;

            const isHighlighted =
              selectedTable === edge.fromTable || selectedTable === edge.toTable;

            // Connect from right of source to left of target (or closest sides)
            const sx = source.x + source.width;
            const sy = source.y + 45;
            const tx = target.x;
            const ty = target.y + 45;

            const dx = Math.abs(tx - sx) * 0.5;
            const pathD = `M ${sx} ${sy} C ${sx + dx} ${sy}, ${tx - dx} ${ty}, ${tx} ${ty}`;

            return (
              <g key={edge.id}>
                <path
                  d={pathD}
                  fill="none"
                  stroke={isHighlighted ? '#10B981' : 'var(--color-border-prominent, #64748b)'}
                  strokeWidth={isHighlighted ? 2.5 : 1.5}
                  strokeDasharray={isHighlighted ? undefined : '4 3'}
                  markerEnd={isHighlighted ? 'url(#arrowhead-highlight)' : 'url(#arrowhead)'}
                  className="transition-all duration-200"
                />
              </g>
            );
          })}
        </svg>

        {/* HTML Table Nodes Layer */}
        {tables.map((table) => {
          const pos = nodePositions[table.name];
          if (!pos) return null;
          const isSelected = selectedTable === table.name;

          return (
            <div
              key={table.name}
              onClick={(e) => {
                e.stopPropagation();
                onSelectTable(table.name);
              }}
              style={{
                left: `${pos.x}px`,
                top: `${pos.y}px`,
                width: `${pos.width}px`,
              }}
              className={`absolute rounded-xl bg-card border shadow-lg cursor-pointer transition-all duration-150 hover:shadow-xl ${
                isSelected
                  ? 'border-accent-primary ring-2 ring-accent-primary/30 z-30'
                  : 'border-border-subtle hover:border-border-prominent z-10'
              }`}
            >
              {/* Table Node Header */}
              <div
                className={`flex items-center justify-between p-space-3 rounded-t-xl border-b border-border-subtle transition-colors ${
                  isSelected ? 'bg-accent-primary/15' : 'bg-canvas/80'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Database
                    className={`w-4 h-4 shrink-0 ${
                      isSelected ? 'text-accent-primary' : 'text-secondary'
                    }`}
                  />
                  <span className="font-semibold text-xs text-primary truncate font-mono">
                    {table.name}
                  </span>
                </div>
                <Badge variant="neutral" className="text-[10px] font-mono py-0 shrink-0">
                  {table.row_count}
                </Badge>
              </div>

              {/* Table Columns List */}
              <div className="p-space-2 divide-y divide-border-subtle/40 max-h-56 overflow-y-auto">
                {table.columns.slice(0, 8).map((col) => {
                  const isPk = table.primary_keys?.includes(col);
                  const fk = table.foreign_keys?.find((f) => f.constrained.includes(col));
                  const type = table.column_types?.[col] || 'TEXT';

                  return (
                    <div
                      key={col}
                      className="flex items-center justify-between py-1 px-1.5 text-[11px] font-mono"
                    >
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isPk && (
                          <span title="Primary Key" className="text-status-success shrink-0">
                            <Key className="w-3 h-3" />
                          </span>
                        )}
                        {fk && (
                          <span title={`FK to ${fk.referred_table}`} className="text-accent-primary shrink-0">
                            <LinkIcon className="w-3 h-3" />
                          </span>
                        )}
                        <span
                          className={`truncate ${
                            isPk ? 'font-semibold text-primary' : 'text-secondary'
                          }`}
                        >
                          {col}
                        </span>
                      </div>
                      <span className="text-[9px] uppercase text-muted tracking-tight ml-2">
                        {type}
                      </span>
                    </div>
                  );
                })}
                {table.columns.length > 8 && (
                  <div className="text-[10px] text-muted text-center py-1">
                    +{table.columns.length - 8} more columns
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
