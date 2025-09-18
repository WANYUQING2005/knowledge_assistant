import { useState, useEffect, useCallback } from "react";
import KnowledgePicker from "./KnowledgePicker";
import { listKnowledge } from "./api/user";
import styles from "./KnowledgeSelector.module.css";

function KnowledgeSelector({
  selectedKBs = [],
  onKBChange,
  onClose,
  className = "",
}) {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tempSelectedIds, setTempSelectedIds] = useState(
    selectedKBs.map((kb) => kb.id)
  ); 
  const loadKnowledgeBases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const user_id = localStorage.getItem("user_id");
      if (!user_id) {
        setError("用户未登录");
        return;
      }
      const response = await listKnowledge(user_id);
      const kbs = response.data || [];
      const formattedKBs = kbs.map((kb) => ({
        id: kb.id,
        name: kb.name || "未命名知识库",
        description: kb.description || "",
        updated: kb.updated_at
          ? new Date(kb.updated_at).toLocaleDateString()
          : "",
        size: kb.document_count ? `${kb.document_count}个文档` : "0个文档",
        create_at: kb.create_at,
        user_id: kb.user_id,
      }));
      setKnowledgeBases(formattedKBs);
    } catch (err) {
      console.error("Failed to load knowledge bases:", err);
      setError("加载知识库失败");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    loadKnowledgeBases();
  }, [loadKnowledgeBases]);
  const handleKBSelectionChange = (selectedIds) => {
    setTempSelectedIds(selectedIds);
  };
  const handleKBConfirm = (selectedIds, dbValue) => {
    console.log("Confirming selection:", selectedIds, knowledgeBases);
    const selected = knowledgeBases.filter((kb) => selectedIds.includes(kb.id));
    console.log("Selected KBs:", selected);
    onKBChange?.(selected);
    onClose?.();
  };

  const handleCreateKB = () => {
    console.log("创建新知识库");
  };

  if (loading) {
    return (
      <div className={`${styles.container} ${className}`}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <span>加载知识库中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${styles.container} ${className}`}>
        <div className={styles.error}>
          <span>{error}</span>
          <button onClick={loadKnowledgeBases} className={styles.retryBtn}>
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`}>
      <KnowledgePicker
        kbs={knowledgeBases}
        value={tempSelectedIds} 
        onChange={handleKBSelectionChange}
        dbOptions={["默认数据库"]} 
        dbValue="默认数据库"
        onDBChange={() => {}}
        onCreate={handleCreateKB}
        onConfirm={handleKBConfirm} 
        className={styles.picker}
      />
    </div>
  );
}

export default KnowledgeSelector;
