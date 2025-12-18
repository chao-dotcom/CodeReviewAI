type ReviewDashboardProps = {
  reviews: { status: string }[];
};

const ReviewDashboard = ({ reviews }: ReviewDashboardProps) => {
  const counts = reviews.reduce(
    (acc, review) => {
      const key = review.status;
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
  return (
    <section className="card dashboard">
      <div className="card-header">
        <h2>Review Dashboard</h2>
        <span className="chip">{reviews.length} total</span>
      </div>
      <div className="dashboard-grid">
        <div>
          <p>Pending</p>
          <h3>{counts.pending ?? 0}</h3>
        </div>
        <div>
          <p>In progress</p>
          <h3>{counts.in_progress ?? 0}</h3>
        </div>
        <div>
          <p>Completed</p>
          <h3>{counts.completed ?? 0}</h3>
        </div>
        <div>
          <p>Failed</p>
          <h3>{counts.failed ?? 0}</h3>
        </div>
      </div>
    </section>
  );
};

export default ReviewDashboard;
