import React, { useState, useEffect } from 'react';
import { MessageSquare, Network, FileText, AlertCircle, X } from 'lucide-react';
import { Topbar } from './Topbar';
import { GovernanceSidebar } from './GovernanceSidebar';
import { Tabs, TabsList, TabsTrigger, TabsContent, Button } from '../ui/Primitives';
import { useStore } from '../../context/StoreContext';

// Feature Components
import { ChatFeed } from '../query/ChatFeed';
import { QueryInput } from '../query/QueryInput';
import { TableList } from '../schema/TableList';
import { SchemaGraph } from '../schema/SchemaGraph';
import { TelemetryKpis } from '../audit/TelemetryKpis';
import { LatencyChart } from '../audit/LatencyChart';
import { AuditTable } from '../audit/AuditTable';
import { TraceDrawer } from '../audit/TraceDrawer';

export const AppShell: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'query' | 'schema' | 'audit'>('query');
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  const {
    connection,
    tablesMeta,
    isSchemaLoading,
    refreshSchema,
    history,
    isQuerying,
    activeQuestion,
    setActiveQuestion,
    showSql,
    askQuestion,
    clearHistory,
    auditLogs,
    auditTotal,
    selectedTrace,
    setSelectedTrace,
    fetchAuditLogs,
    errorMessage,
    clearError,
  } = useStore();

  // Set default selected table when tablesMeta load
  useEffect(() => {
    if (!selectedTable && tablesMeta.length > 0) {
      setSelectedTable(tablesMeta[0].name);
    }
  }, [tablesMeta, selectedTable]);

  // Fetch fresh audit logs when entering Audit tab
  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, fetchAuditLogs]);

  const handleSelectPrompt = (prompt: string) => {
    setActiveQuestion(prompt);
    askQuestion(prompt);
  };

  return (
    <div className="min-h-screen bg-app text-primary flex flex-col transition-colors overflow-hidden">
      {/* Sticky Topbar */}
      <Topbar />

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="bg-status-error-bg border-b border-status-error/30 px-space-4 py-2 flex items-center justify-between text-xs text-status-error shrink-0 z-30">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="font-semibold">Error:</span>
            <span>{errorMessage}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearError}
            className="text-status-error hover:bg-status-error/10 min-h-[32px] min-w-[32px] p-1"
          >
            <X className="w-3.5 h-3.5 mr-1" />
            Dismiss Alert
          </Button>
        </div>
      )}

      {/* Body: Sidebar + Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Governance Sidebar */}
        <GovernanceSidebar />

        {/* Main Active Workspace View */}
        <main className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden">
          <Tabs
            value={activeTab}
            onValueChange={(val) => setActiveTab(val as 'query' | 'schema' | 'audit')}
            className="h-full flex flex-col"
          >
            {/* View Navigation Tabs Header */}
            <div className="px-space-6 pt-space-4 pb-space-3 border-b border-border-subtle bg-canvas/30 shrink-0">
              <TabsList>
                <TabsTrigger value="query">
                  <MessageSquare className="w-4 h-4" />
                  <span>Query Console</span>
                </TabsTrigger>
                <TabsTrigger value="schema">
                  <Network className="w-4 h-4" />
                  <span>Schema Explorer</span>
                </TabsTrigger>
                <TabsTrigger value="audit">
                  <FileText className="w-4 h-4" />
                  <span>Audit Telemetry</span>
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Tab 1: Query Console */}
            <TabsContent value="query" className="flex-1 flex flex-col overflow-hidden m-0 p-0">
              <div className="flex-1 flex flex-col overflow-hidden">
                <ChatFeed
                  history={history}
                  isQuerying={isQuerying}
                  activeQuestion={activeQuestion}
                  showSql={showSql}
                  dialect={connection.dialect}
                  onSelectPrompt={handleSelectPrompt}
                />
                <QueryInput
                  value={activeQuestion}
                  onChangeValue={setActiveQuestion}
                  onExecute={(q) => askQuestion(q)}
                  onClearHistory={clearHistory}
                  isLoading={isQuerying}
                  hasHistory={history.length > 0}
                />
              </div>
            </TabsContent>

            {/* Tab 2: Schema Explorer & ER Graph */}
            <TabsContent value="schema" className="flex-1 overflow-hidden m-0 p-space-6">
              <div className="h-full flex flex-col md:flex-row gap-space-6 overflow-hidden">
                {/* Left Subpanel: Discovered Tables Accordion */}
                <div className="w-full md:w-[360px] lg:w-[400px] h-full shrink-0 flex flex-col">
                  <TableList
                    tables={tablesMeta}
                    selectedTable={selectedTable}
                    onSelectTable={setSelectedTable}
                    onRefreshSchema={refreshSchema}
                    isRefreshing={isSchemaLoading}
                  />
                </div>

                {/* Right Subpanel: React ER Diagram Canvas */}
                <div className="flex-1 h-full min-w-0">
                  <SchemaGraph
                    tables={tablesMeta}
                    selectedTable={selectedTable}
                    onSelectTable={setSelectedTable}
                  />
                </div>
              </div>
            </TabsContent>

            {/* Tab 3: Audit Telemetry */}
            <TabsContent value="audit" className="flex-1 overflow-y-auto m-0 p-space-6">
              <div className="max-w-6xl mx-auto space-y-space-6 pb-space-8">
                {/* KPI Metrics */}
                <TelemetryKpis logs={auditLogs} totalLogs={auditTotal} />

                {/* Latency Stage Breakdown */}
                <LatencyChart logs={auditLogs} />

                {/* Paginated Audit Log Table */}
                <AuditTable
                  logs={auditLogs}
                  onSelectTrace={(entry) => setSelectedTrace(entry)}
                />
              </div>
            </TabsContent>
          </Tabs>
        </main>
      </div>

      {/* Slide-out Trace Drawer */}
      <TraceDrawer
        trace={selectedTrace}
        onClose={() => setSelectedTrace(null)}
      />
    </div>
  );
};
