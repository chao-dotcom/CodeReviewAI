type FileTreeProps = {
  files: { filePath: string; lines: string[] }[];
  selectedFile: string | null;
  onSelect: (path: string | null) => void;
};

const FileTree = ({ files, selectedFile, onSelect }: FileTreeProps) => {
  return (
    <aside className="file-tree card">
      <div className="card-header">
        <h2>Files</h2>
        <span className="chip ghost">{files.length}</span>
      </div>
      <button
        className={`file-item ${selectedFile === null ? "active" : ""}`}
        onClick={() => onSelect(null)}
      >
        All files
      </button>
      {files.map((file) => (
        <button
          key={file.filePath}
          className={`file-item ${selectedFile === file.filePath ? "active" : ""}`}
          onClick={() => onSelect(file.filePath)}
        >
          {file.filePath}
        </button>
      ))}
    </aside>
  );
};

export default FileTree;
