import styles from "./KnowledgeDisplay.module.css";
function KnowledgeDisplay({ selectedKBs, onRemove, onOpenPicker }) {
  if (selectedKBs.length === 0) {
    return (
      <div className={styles.empty}>
        <span className={styles.emptyText}>未选择知识库</span>
        <button className={styles.selectBtn} onClick={onOpenPicker}>
          选择知识库
        </button>
      </div>
    );
  }
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.label}>已选知识库 ({selectedKBs.length})</span>
        <button className={styles.editBtn} onClick={onOpenPicker}>
          编辑
        </button>
      </div>
      <div className={styles.kbList}>
        {selectedKBs.map((kb) => (
          <div key={kb.id} className={styles.kbItem}>
            <div className={styles.kbInfo}>
              <span className={styles.kbName}>{kb.name}</span>
              {kb.size && <span className={styles.kbSize}>{kb.size}</span>}
            </div>
            {onRemove && (
              <button
                className={styles.removeBtn}
                onClick={() => onRemove(kb)}
                title="移除此知识库"
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default KnowledgeDisplay;
