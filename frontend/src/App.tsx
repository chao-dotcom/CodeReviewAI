import { useEffect, useState } from "react";
import AgentTrace from "./components/AgentTrace";
import DiffViewer from "./components/DiffViewer";
import ReviewSummary from "./components/ReviewSummary";
import Sidebar from "./components/Sidebar";
import {
  Comment,
  ReviewStatus,
  createReview,
  getComments,
  getFeedbackSummary,
  getAllPreferences,
  getPreferences,
  getReview,
  indexRepo,
  listReviews,
  resetStore,
  submitFeedback
} from "./api";

const App = () => {
  const [reviews, setReviews] = useState<ReviewStatus[]>([]);
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [selectedReview, setSelectedReview] = useState<ReviewStatus | null>(null);
  const [diffText, setDiffText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [repoPath, setRepoPath] = useState("");
  const [indexStatus, setIndexStatus] = useState<string | null>(null);
  const [feedbackSummary, setFeedbackSummary] = useState({
    up: 0,
    down: 0,
    neutral: 0
  });
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [resetStatus, setResetStatus] = useState<string | null>(null);
  const [showResetModal, setShowResetModal] = useState(false);

  const refreshReviews = async () => {
    const data = await listReviews();
    setReviews(data);
    if (!selectedReviewId && data.length > 0) {
      setSelectedReviewId(data[0].id);
    }
  };

  useEffect(() => {
    void refreshReviews();
  }, []);

  useEffect(() => {
    if (!selectedReviewId) {
      setComments([]);
      setSelectedReview(null);
      setFeedbackSummary({ up: 0, down: 0, neutral: 0 });
      return;
    }
    void getComments(selectedReviewId).then(setComments);
    void getReview(selectedReviewId).then(setSelectedReview);
    void getFeedbackSummary(selectedReviewId).then(setFeedbackSummary);
  }, [selectedReviewId]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void refreshReviews();
      if (selectedReviewId) {
        void getComments(selectedReviewId).then(setComments);
        void getReview(selectedReviewId).then(setSelectedReview);
        void getFeedbackSummary(selectedReviewId).then(setFeedbackSummary);
      }
    }, 3000);
    return () => window.clearInterval(interval);
  }, [selectedReviewId]);

  useEffect(() => {
    if (!showResetModal) {
      return;
    }
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setShowResetModal(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [showResetModal]);

  const handleSubmit = async () => {
    if (!diffText.trim()) {
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await createReview(diffText);
      setDiffText("");
      await refreshReviews();
      setSelectedReviewId(result.review.id);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleIndexRepo = async () => {
    if (!repoPath.trim()) {
      return;
    }
    setIndexStatus("Indexing...");
    try {
      const result = await indexRepo(repoPath.trim(), ["**/*.py"]);
      setIndexStatus(`Indexed ${result.count} chunks`);
    } catch (error) {
      setIndexStatus("Index failed");
    }
  };

  const handleFeedback = async (commentId: string, rating: number) => {
    if (!selectedReviewId) {
      return;
    }
    try {
      await submitFeedback(selectedReviewId, commentId, rating);
    } catch (error) {
      setIndexStatus("Feedback failed");
    }
  };

  const handleExportPreferences = async () => {
    if (!selectedReviewId) {
      return;
    }
    setExportStatus("Preparing...");
    try {
      const data = await getPreferences(selectedReviewId, 50);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `review-${selectedReviewId}-preferences.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      setExportStatus(`Exported ${data.length} pairs`);
    } catch (error) {
      setExportStatus("Export failed");
    }
  };

  const handleExportAllPreferences = async () => {
    setExportStatus("Preparing...");
    try {
      const data = await getAllPreferences(200);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "all-preferences.json";
      anchor.click();
      URL.revokeObjectURL(url);
      setExportStatus(`Exported ${data.length} pairs`);
    } catch (error) {
      setExportStatus("Export failed");
    }
  };

  const handleReset = async () => {
    setShowResetModal(true);
  };

  const confirmReset = async () => {
    setResetStatus("Resetting...");
    try {
      await resetStore();
      setReviews([]);
      setSelectedReviewId(null);
      setSelectedReview(null);
      setComments([]);
      setFeedbackSummary({ up: 0, down: 0, neutral: 0 });
      setResetStatus("Reset complete");
      setShowResetModal(false);
    } catch (error) {
      setResetStatus("Reset failed");
      setShowResetModal(false);
    }
  };

  const cancelReset = () => {
    setShowResetModal(false);
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">Agentic Code Review</p>
          <h1>Review orchestration for high-signal feedback</h1>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={handleReset}>
            Reset Demo
          </button>
          <span className="status">{resetStatus ?? ""}</span>
          <button className="secondary" onClick={refreshReviews}>
            Refresh
          </button>
          <button className="primary" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Trigger Review"}
          </button>
        </div>
      </header>

      <div className="layout">
        <Sidebar reviews={reviews} selectedId={selectedReviewId} onSelect={setSelectedReviewId} />
        <main className="main">
          <section className="card input-card">
            <div className="card-header">
              <h2>Paste Unified Diff</h2>
              <span className="chip ghost">API Ready</span>
            </div>
            <textarea
              placeholder="Paste a unified diff here..."
              value={diffText}
              onChange={(event) => setDiffText(event.target.value)}
            />
          </section>
          <section className="card input-card">
            <div className="card-header">
              <h2>Index Repository</h2>
              <span className="chip ghost">RAG</span>
            </div>
            <input
              type="text"
              placeholder="C:\\path\\to\\repo"
              value={repoPath}
              onChange={(event) => setRepoPath(event.target.value)}
            />
            <div className="row">
              <button className="secondary" onClick={handleIndexRepo}>
                Index Repo
              </button>
              <span className="status">{indexStatus ?? "Idle"}</span>
            </div>
          </section>
          <section className="card input-card">
            <div className="card-header">
              <h2>Export Preferences</h2>
              <span className="chip ghost">DPO</span>
            </div>
            <p className="hint">Downloads JSON preference pairs for the selected review.</p>
            <div className="row">
              <button className="secondary" onClick={handleExportPreferences}>
                Download JSON
              </button>
              <button className="secondary" onClick={handleExportAllPreferences}>
                Download All
              </button>
              <span className="status">{exportStatus ?? "Idle"}</span>
            </div>
          </section>
          <DiffViewer
            diffText={(selectedReview?.metadata?.diff as string) ?? ""}
            comments={comments}
            onFeedback={handleFeedback}
          />
          <div className="panel-grid">
            <ReviewSummary comments={comments} feedback={feedbackSummary} />
            <AgentTrace />
          </div>
        </main>
      </div>
      {showResetModal ? (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          onClick={cancelReset}
        >
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <h2>Reset demo data?</h2>
            <p>This clears all reviews, comments, feedback, and RAG index data.</p>
            <div className="row">
              <button className="secondary" onClick={cancelReset}>
                Cancel
              </button>
              <button className="primary" onClick={confirmReset}>
                Reset Now
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default App;
