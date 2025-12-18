type ReviewSummaryProps = {
  comments: { severity: string; content: string; file_path: string }[];
  feedback: { up: number; down: number; neutral: number };
};

const ReviewSummary = ({ comments, feedback }: ReviewSummaryProps) => {
  const severityCounts = comments.reduce(
    (acc, comment) => {
      const key = comment.severity.toLowerCase();
      if (key in acc) {
        acc[key] += 1;
      }
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 }
  );
  const topComments = comments.slice(0, 3);
  return (
    <section className="card summary">
      <div className="card-header">
        <h2>Review Summary</h2>
        <span className="chip">{comments.length} findings</span>
      </div>
      <div className="summary-grid">
        <div>
          <p className="summary-label">Critical</p>
          <h3>{severityCounts.critical}</h3>
        </div>
        <div>
          <p className="summary-label">High</p>
          <h3>{severityCounts.high}</h3>
        </div>
        <div>
          <p className="summary-label">Medium</p>
          <h3>{severityCounts.medium}</h3>
        </div>
        <div>
          <p className="summary-label">Low</p>
          <h3>{severityCounts.low}</h3>
        </div>
      </div>
      <div className="summary-feedback">
        <span className="chip ghost">👍 {feedback.up}</span>
        <span className="chip ghost">👎 {feedback.down}</span>
        <span className="chip ghost">• {feedback.neutral}</span>
      </div>
      <div className="summary-list">
        {topComments.length === 0 ? (
          <p className="empty">No comments yet.</p>
        ) : (
          topComments.map((comment, index) => (
            <div key={`${comment.file_path}-${index}`}>
              <strong>{comment.file_path}</strong>
              <p>{comment.content}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
};

export default ReviewSummary;
