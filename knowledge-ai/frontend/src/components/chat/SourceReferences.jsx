
function SourceReferences({ sources = [] }) {
  if (!sources.length) return null;

  return (
    <div className="source-references">
      <div className="source-heading">
        <i className="bi bi-journal-text"></i>
        Sources used
      </div>

      <div className="source-list">
        {sources.map((source, index) => (
          <div
            className="source-item"
            key={`${source.source_id || source.document_id}-${source.page}-${index}`}
          >
            <span className="source-number">
              {source.reference || `[${index + 1}]`}
            </span>

            <div>
              {source.source_type === "web" && (source.page_url || source.original_url) ? (
                <>
                  <strong>{source.source_title || "Web documentation"}</strong>
                  <a
                    href={source.page_url || source.original_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open source
                  </a>
                </>
              ) : (
                <>
                  <strong>{source.source_title || "Document reference"}</strong>
                  {source.page ? <small>Page {source.page}</small> : null}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SourceReferences;
