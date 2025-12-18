type AgentTraceProps = {
  messages: { agent_id: string; message_type: string; timestamp: string; payload: Record<string, unknown> }[];
};

const AgentTrace = ({ messages }: AgentTraceProps) => {
  return (
    <section className="card">
      <div className="card-header">
        <h2>Agent Trace</h2>
        <span className="chip ghost">Live run</span>
      </div>
      {messages.length === 0 ? (
        <p className="empty">No agent messages yet.</p>
      ) : (
        <ol className="trace">
          {messages.map((message, index) => (
            <li key={`${message.agent_id}-${index}`}>
              <span className="trace-time">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
              <div>
                <strong>{message.agent_id}</strong>
                <p>{message.message_type}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
};

export default AgentTrace;
