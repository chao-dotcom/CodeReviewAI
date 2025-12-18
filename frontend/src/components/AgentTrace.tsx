const AgentTrace = () => {
  return (
    <section className="card">
      <div className="card-header">
        <h2>Agent Trace</h2>
        <span className="chip ghost">Live run</span>
      </div>
      <ol className="trace">
        <li>
          <span className="trace-time">00:00.4s</span>
          <div>
            <strong>Code Reviewer</strong>
            <p>2 findings, 1 suggestion for missing validation.</p>
          </div>
        </li>
        <li>
          <span className="trace-time">00:00.7s</span>
          <div>
            <strong>Security Reviewer</strong>
            <p>Flagged potential secret exposure in config change.</p>
          </div>
        </li>
        <li>
          <span className="trace-time">00:01.0s</span>
          <div>
            <strong>Style Reviewer</strong>
            <p>Line length warning on auth module.</p>
          </div>
        </li>
      </ol>
    </section>
  );
};

export default AgentTrace;
