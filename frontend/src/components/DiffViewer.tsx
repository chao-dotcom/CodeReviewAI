type DiffViewerProps = {
  diffText: string;
  comments: { id: string; file_path: string; line_number: number | null; content: string }[];
  onFeedback: (commentId: string, rating: number) => void;
};

const DiffViewer = ({ diffText, comments, onFeedback }: DiffViewerProps) => {
  const lines = diffText.split(/\r?\n/);
  const grouped = comments.reduce<Record<string, typeof comments>>((acc, comment) => {
    acc[comment.file_path] ??= [];
    acc[comment.file_path].push(comment);
    return acc;
  }, {});

  return (
    <section className="card diff-card">
      <div className="card-header">
        <h2>Diff Viewer</h2>
        <span className="chip ghost">{comments.length} comments</span>
      </div>
      {diffText.trim() ? (
        <div className="diff-scroll">
          {lines.map((line, index) => {
            let className = "diff-line";
            if (line.startsWith("+") && !line.startsWith("+++")) {
              className += " added";
            } else if (line.startsWith("-") && !line.startsWith("---")) {
              className += " removed";
            }
            return (
              <div key={`${index}-${line}`} className={className}>
                <span className="line-number">{index + 1}</span>
                <span className="line-content">{line || " "}</span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="empty">No diff loaded yet.</p>
      )}
      <div className="comment-list">
        {comments.length === 0 ? (
          <p className="empty">No inline comments available.</p>
        ) : (
          Object.entries(grouped).map(([filePath, fileComments]) => (
            <div key={filePath} className="comment-group">
              <span className="chip">{filePath}</span>
              {fileComments.map((comment, index) => (
                <div key={`${filePath}-${index}`} className="comment-item">
                  <span className="chip ghost">Line {comment.line_number ?? "?"}</span>
                  <p>{comment.content}</p>
                  <div className="feedback">
                    <button onClick={() => onFeedback(comment.id, 1)}>👍</button>
                    <button onClick={() => onFeedback(comment.id, -1)}>👎</button>
                  </div>
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </section>
  );
};

export default DiffViewer;
