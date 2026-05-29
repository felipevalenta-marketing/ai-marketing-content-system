import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { JsonViewer } from "../components/JsonViewer";
import { LoadingState } from "../components/LoadingState";
import { SectionHeader } from "../components/SectionHeader";
import type { StorageRecord } from "../types/api";
import { STORAGE_RECORD_TYPES } from "../utils/storageTypes";
import { useLocalState } from "../hooks/useLocalState";
import type { WorkspaceProps } from "./shared";

interface StorageExplorerProps extends WorkspaceProps {}

export function StorageExplorer({ client }: StorageExplorerProps) {
  const [recordType, setRecordType] = useLocalState<string>("amcs:storage-record-type", "");
  const [records, setRecords] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadRecords = async () => {
    setLoading(true);
    setError("");
    const response = await client.listStorageRecords(recordType || undefined);
    if (response.success && response.data) {
      const data = response.data as any;
      const items = data.records ?? [];
      setRecords(items);
      setSelected(items[0] ?? null);
    } else {
      setRecords([]);
      setSelected(null);
      setError(response.errors?.[0] ?? "Unable to load storage records.");
    }
    setLoading(false);
  };

  useEffect(() => {
    void loadRecords();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client.baseUrl, recordType]);

  const loadSelected = async (record: StorageRecord) => {
    if (!record.record_type || !record.record_id) {
      setSelected(record);
      return;
    }
    setLoading(true);
    const response = await client.getStorageRecord(record.record_type, record.record_id);
    if (response.success && response.data) {
      setSelected(response.data as any);
    } else {
      setError(response.errors?.[0] ?? "Unable to load record.");
    }
    setLoading(false);
  };

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader title="Storage Explorer" description="Browse structured local records safely by type or identifier." />
        <div className="form-grid">
          <div className="field field--full">
            <label htmlFor="recordType">Record Type</label>
            <select id="recordType" className="select" value={recordType} onChange={(event) => setRecordType(event.target.value)}>
              <option value="">All record types</option>
              {STORAGE_RECORD_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={loadRecords} disabled={loading}>
            {loading ? "Loading..." : "Refresh Records"}
          </Button>
        </div>
        {loading ? <LoadingState label="Loading storage records..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {records.length > 0 ? (
          <div className="section">
            {records.map((record) => (
              <button
                key={`${record.record_type}-${record.record_id}`}
                type="button"
                className={`sidebar__button ${selected?.record_id === record.record_id ? "is-active" : ""}`.trim()}
                onClick={() => loadSelected(record)}
              >
                <div>
                  <strong>{String(record.record_type ?? "record")}</strong>
                </div>
                <span>{String(record.record_id ?? "-")}</span>
              </button>
            ))}
          </div>
        ) : (
          <EmptyState title="No records found" description="Storage records appear after persistence is enabled or actions have been stored." />
        )}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Selected Record" description="Safe JSON preview of the currently selected storage record." />
        {selected ? <JsonViewer data={selected} title="Storage Record" /> : <EmptyState title="Nothing selected" description="Choose a record to preview it here." />}
      </Card>
    </div>
  );
}
