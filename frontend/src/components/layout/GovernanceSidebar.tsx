import React, { useState, useRef } from 'react';
import {
  Database,
  Upload,
  Link as LinkIcon,
  RotateCw,
  Shield,
  Sliders,
  Sparkles,
  Code2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { useStore } from '../../context/StoreContext';
import { Button, Input, Badge } from '../ui/Primitives';
import { PolicyModal } from '../modals/Modals';

export const GovernanceSidebar: React.FC = () => {
  const {
    connection,
    connectDemo,
    connectCustom,
    uploadSqlite,
    refreshSchema,
    isSchemaLoading,
    blockedColumns,
    useFewShot,
    setUseFewShot,
    showSql,
    setShowSql,
  } = useStore();

  const [activeTab, setActiveTab] = useState<'demo' | 'upload' | 'custom'>('demo');
  const [customUri, setCustomUri] = useState('');
  const [uriError, setUriError] = useState('');
  const [isSubmittingUri, setIsSubmittingUri] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Validate custom URI format
  const handleConnectCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    setUriError('');

    const trimmed = customUri.trim();
    if (!trimmed) {
      setUriError('Database URI is required');
      return;
    }

    const uriRegex = /^(postgresql|mysql|sqlite)(\+[^:]+)?:\/\//i;
    if (!uriRegex.test(trimmed)) {
      setUriError('URI must start with postgresql://, mysql://, or sqlite:///');
      return;
    }

    setIsSubmittingUri(true);
    try {
      await connectCustom(trimmed);
      setCustomUri('');
    } catch {
      setUriError('Connection failed. Check network or credentials.');
    } finally {
      setIsSubmittingUri(false);
    }
  };

  // Handle SQLite file selection
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.db') && !file.name.endsWith('.sqlite')) {
      setUploadStatus('File must be a .db or .sqlite SQLite database');
      return;
    }

    setUploadStatus('Uploading database...');
    try {
      await uploadSqlite(file);
      setUploadStatus(`Connected: ${file.name}`);
    } catch {
      setUploadStatus('Upload failed. Invalid SQLite file.');
    }
  };

  return (
    <aside className="w-80 min-w-[320px] max-w-[320px] h-[calc(100vh-3.5rem)] bg-sidebar border-r border-border-subtle p-space-4 flex flex-col justify-between overflow-y-auto select-none transition-colors">
      <div className="space-y-space-6">
        {/* Section 1: Database Switcher */}
        <div>
          <div className="flex items-center gap-2 mb-space-2 text-xs font-semibold text-secondary uppercase tracking-wider">
            <Database className="w-4 h-4 text-accent-primary" />
            <span>Database Connection</span>
          </div>

          {/* Mode Switcher Buttons */}
          <div className="grid grid-cols-3 gap-1 p-1 bg-canvas rounded-lg mb-space-4 border border-border-subtle">
            <button
              type="button"
              onClick={() => setActiveTab('demo')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'demo'
                  ? 'bg-card text-accent-primary shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Demo HR
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('upload')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'upload'
                  ? 'bg-card text-accent-primary shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Upload
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('custom')}
              className={`py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'custom'
                  ? 'bg-card text-accent-primary shadow-xs'
                  : 'text-secondary hover:text-primary'
              }`}
            >
              Custom URI
            </button>
          </div>

          {/* Tab 1: Demo HR ERP */}
          {activeTab === 'demo' && (
            <div className="p-space-4 bg-card border border-border-subtle rounded-xl space-y-space-2">
              <p className="text-xs text-secondary leading-relaxed">
                Preloaded HR ERP SQLite database with 4 relational tables (employees, departments, projects, salaries).
              </p>
              <Button
                variant={connection.mode === 'demo' ? 'secondary' : 'primary'}
                size="sm"
                onClick={connectDemo}
                isLoading={connection.status === 'connecting' && connection.mode === 'demo'}
                className="w-full justify-center"
              >
                {connection.mode === 'demo' ? 'Reload Demo DB' : 'Connect Demo DB'}
              </Button>
            </div>
          )}

          {/* Tab 2: Upload SQLite */}
          {activeTab === 'upload' && (
            <div className="p-space-4 bg-card border border-border-subtle rounded-xl space-y-space-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".db,.sqlite"
                onChange={handleFileUpload}
                className="hidden"
              />
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-border-prominent hover:border-accent-primary rounded-lg p-space-4 text-center cursor-pointer transition-colors"
              >
                <Upload className="w-6 h-6 mx-auto mb-1 text-secondary" />
                <span className="text-xs font-semibold text-primary block">
                  Select SQLite File
                </span>
                <span className="text-[10px] text-muted">.db or .sqlite files</span>
              </div>
              {uploadStatus && (
                <p className="text-xs text-secondary mt-1 flex items-center gap-1">
                  {uploadStatus.includes('Connected') ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                  ) : uploadStatus.includes('failed') ? (
                    <AlertCircle className="w-3.5 h-3.5 text-status-error shrink-0" />
                  ) : null}
                  <span>{uploadStatus}</span>
                </p>
              )}
            </div>
          )}

          {/* Tab 3: Custom Database URI */}
          {activeTab === 'custom' && (
            <form onSubmit={handleConnectCustom} className="p-space-4 bg-card border border-border-subtle rounded-xl space-y-space-2">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-secondary flex items-center gap-1">
                  <LinkIcon className="w-3.5 h-3.5" />
                  <span>Connection String</span>
                </label>
                <Input
                  type="password"
                  placeholder="postgresql://user:pass@host:5432/db"
                  value={customUri}
                  onChange={(e) => {
                    setCustomUri(e.target.value);
                    if (uriError) setUriError('');
                  }}
                  error={Boolean(uriError)}
                  className="font-mono text-xs"
                />
                {uriError && (
                  <p className="text-xs text-status-error">{uriError}</p>
                )}
              </div>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isSubmittingUri}
                className="w-full justify-center"
              >
                Connect Database
              </Button>
            </form>
          )}
        </div>

        {/* Section 2: Schema & Governance Summary */}
        <div>
          <div className="flex items-center justify-between mb-space-2">
            <span className="text-xs font-semibold text-secondary uppercase tracking-wider flex items-center gap-1">
              <Shield className="w-4 h-4 text-status-warning" />
              <span>Governance & Schema</span>
            </span>
            <button
              type="button"
              onClick={refreshSchema}
              disabled={isSchemaLoading}
              title="Refresh Schema"
              aria-label="Refresh Schema"
              className="p-1 rounded-md text-secondary hover:text-primary hover:bg-card cursor-pointer transition-colors"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isSchemaLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="p-space-4 bg-card border border-border-subtle rounded-xl space-y-space-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-secondary">Reflected Tables</span>
              <Badge variant="neutral">{connection.tableCount} tables</Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-secondary">Sensitive Columns</span>
              <Badge variant="warning">{blockedColumns.length} restricted</Badge>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPolicyModalOpen(true)}
              className="w-full justify-center"
            >
              <Sliders className="w-3.5 h-3.5 mr-1" />
              Configure Governance
            </Button>
          </div>
        </div>

        {/* Section 3: Query Controls */}
        <div>
          <div className="flex items-center gap-2 mb-space-2 text-xs font-semibold text-secondary uppercase tracking-wider">
            <Sliders className="w-4 h-4 text-accent-primary" />
            <span>Query Pipeline</span>
          </div>

          <div className="p-space-4 bg-card border border-border-subtle rounded-xl space-y-space-4">
            {/* Few-Shot Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent-primary" />
                <span className="text-xs font-semibold text-primary">FAISS Retrieval</span>
              </div>
              <input
                type="checkbox"
                id="few-shot-toggle"
                checked={useFewShot}
                onChange={(e) => setUseFewShot(e.target.checked)}
                className="w-4 h-4 accent-accent-primary cursor-pointer rounded"
              />
            </div>

            {/* Show SQL Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-accent-primary" />
                <span className="text-xs font-semibold text-primary">Show SQL & AST</span>
              </div>
              <input
                type="checkbox"
                id="show-sql-toggle"
                checked={showSql}
                onChange={(e) => setShowSql(e.target.checked)}
                className="w-4 h-4 accent-accent-primary cursor-pointer rounded"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-space-4 border-t border-border-subtle text-center">
        <p className="text-[11px] text-muted">
          AST Security Engine active &bull; sqlglot 26.x
        </p>
      </div>

      {/* Governance Policy Modal */}
      <PolicyModal
        open={isPolicyModalOpen}
        onOpenChange={setIsPolicyModalOpen}
      />
    </aside>
  );
};
