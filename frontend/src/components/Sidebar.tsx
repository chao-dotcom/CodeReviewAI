type SidebarProps = {
  reviews: { id: string; status: string }[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

const Sidebar = ({ reviews, selectedId, onSelect }: SidebarProps) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-card">
        <h3>Reviews</h3>
        {reviews.length === 0 ? (
          <p className="empty">No reviews yet.</p>
        ) : (
          reviews.map((review) => (
            <button
              key={review.id}
              className={`sidebar-item ${review.id === selectedId ? "active" : ""}`}
              onClick={() => onSelect(review.id)}
            >
              <div>
                <strong>{review.id.slice(0, 8)}</strong>
                <p>{review.status.replace("_", " ")}</p>
              </div>
              <span className={`chip ${review.status === "completed" ? "ghost" : ""}`}>
                {review.status}
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
