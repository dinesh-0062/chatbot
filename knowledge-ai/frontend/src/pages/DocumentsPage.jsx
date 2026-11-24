import { useEffect, useState } from "react";
import Layout from "../components/layout/Layout";
import api from "../api/axios";

function formatBytes(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function DocumentsPage() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [addingUrl, setAddingUrl] = useState(false);
  const [url, setUrl] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadSources = async () => {
    setLoading(true);
    try {
      const response = await api.get("/sources/");
      setSources(response.data.sources || []);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load knowledge sources.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    api.get("/sources/")
      .then((response) => {
        if (active) {
          setSources(response.data.sources || []);
          setError("");
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.response?.data?.detail || "Could not load knowledge sources.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const uploadPdf = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessage("");
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      await api.post("/documents/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessage("PDF uploaded and indexed successfully.");
      await loadSources();
    } catch (err) {
      setError(err.response?.data?.detail || "PDF upload failed.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const addWebsite = async (event) => {
    event.preventDefault();
    if (!url.trim()) return;
    setAddingUrl(true);
    setMessage("");
    setError("");
    try {
      const response = await api.post("/sources/url", { url: url.trim() });
      if (!response.data.success) throw new Error(response.data.detail || "Website indexing failed.");
      setUrl("");
      setMessage("Website source indexed successfully.");
      await loadSources();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Website indexing failed.");
    } finally {
      setAddingUrl(false);
    }
  };

  const deleteSource = async (source) => {
    if (!window.confirm(`Delete "${source.title}"?`)) return;
    try {
      await api.delete(`/sources/${source.source_id}`);
      setSources((items) => items.filter((item) => item.source_id !== source.source_id));
      setMessage("Source deleted successfully.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not delete source.");
    }
  };

  const refreshSource = async (source) => {
    setError("");
    setMessage("");
    try {
      await api.post(`/sources/${source.source_id}/refresh`);
      setMessage(source.source_type === "pdf"
        ? "PDF re-indexed successfully."
        : "Website source refreshed successfully.");
      await loadSources();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not refresh source.");
    }
  };

  const visibleSources = sources.filter((source) => {
    const matchesType = filter === "all" || source.source_type === filter;
    const matchesSearch = (source.title || "").toLowerCase().includes(search.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <Layout>
      <div className="documents-page">
        <div className="documents-actions">
          <label className={`upload-card ${uploading ? "disabled" : ""}`}>
            <input type="file" accept=".pdf,application/pdf" onChange={uploadPdf} disabled={uploading} />
            <i className="bi bi-cloud-arrow-up"></i>
            <strong>{uploading ? "Processing PDF..." : "Upload PDF"}</strong>
            <small>PDF, maximum 20 MB</small>
          </label>

          <form className="website-card" onSubmit={addWebsite}>
            <i className="bi bi-globe2"></i>
            <strong>Add website source</strong>
            <div className="website-input">
              <input
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://docs.example.com/"
                type="url"
                disabled={addingUrl}
              />
              <button type="submit" disabled={!url.trim() || addingUrl}>
                {addingUrl ? <span className="spinner-border spinner-border-sm"></span> : "Add"}
              </button>
            </div>
          </form>
        </div>

        {message && <div className="alert alert-success py-2">{message}</div>}
        {error && <div className="alert alert-danger py-2">{error}</div>}

        <div className="source-toolbar">
          <div className="source-search">
            <i className="bi bi-search"></i>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search sources" />
          </div>
          <div className="source-filter">
            {["all", "pdf", "web"].map((type) => (
              <button key={type} className={filter === type ? "active" : ""} onClick={() => setFilter(type)}>
                {type === "all" ? "All sources" : type === "pdf" ? "PDFs" : "Websites"}
              </button>
            ))}
          </div>
        </div>

        <div className="source-table-card">
          {loading ? (
            <div className="source-empty"><span className="spinner-border"></span></div>
          ) : visibleSources.length === 0 ? (
            <div className="source-empty">
              <i className="bi bi-journals"></i>
              <strong>No sources found</strong>
              <small>Upload a PDF or add a public documentation URL.</small>
            </div>
          ) : (
            visibleSources.map((source) => (
              <div className="source-row" key={source.source_id}>
                <div className={`source-icon ${source.source_type}`}>
                  <i className={source.source_type === "pdf" ? "bi bi-file-earmark-pdf" : "bi bi-globe2"}></i>
                </div>
                <div className="source-details">
                  <strong>{source.title}</strong>
                  {source.original_url
                    ? <a href={source.original_url} target="_blank" rel="noreferrer">{source.original_url}</a>
                    : <small>{formatBytes(source.file_size)} · {source.total_pages ? `${source.total_pages} pages · ` : ""}{source.total_chunks} chunks</small>}
                  {source.error_message && <small className="source-error">{source.error_message}</small>}
                </div>
                <span className={`status-pill ${source.status}`}>{source.status}</span>
                <div className="source-actions">
                  <button title="Refresh or re-index" onClick={() => refreshSource(source)}>
                    <i className="bi bi-arrow-clockwise"></i>
                  </button>
                  <button title="Delete" onClick={() => deleteSource(source)}>
                    <i className="bi bi-trash3"></i>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}

export default DocumentsPage;
