
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
            key={`${source.document_id}-${source.page}-${index}`}
          >
            <span className="source-number">
              {source.reference || `[${index + 1}]`}
            </span>

            <div>
              <strong>Document reference</strong>
              <small>Page {source.page}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SourceReferences;
