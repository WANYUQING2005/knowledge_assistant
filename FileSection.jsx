import styles from "./FileSection.module.css";

function FileSection({ files }) {
  return (
    <section className={styles.block}>
      <header className={styles.header}>
        <div className={styles.title}>文件 （共{files.length}个）</div>
      </header>
      <div className={styles.scroller}>
        {files.length === 0 && <div className={styles.empty}>暂无文件</div>}
        {files.map((file, i) => (
          <div key={file.name + i} className={styles.row}>
            <div className={styles.left}>
              <svg
                className={styles.icon}
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path
                  d="M14 2v6h6"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
              </svg>
              <span className={styles.name} title={file.name}>
                {file.name}
              </span>
            </div>
            <span className={styles.size}>{Math.ceil(file.size/1024)}KB</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export default FileSection;
