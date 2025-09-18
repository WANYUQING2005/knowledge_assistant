import { useState } from "react";
import styles from "./SessionRenameModal.module.css";

function SessionRenameModal({ session, isOpen, onClose, onConfirm }) {
  const [newTitle, setNewTitle] = useState(session?.title || "");
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      setLoading(true);
      await onConfirm(session.session_id || session.id, newTitle.trim());
      onClose();
    } catch (error) {
      console.error("重命名失败:", error);
    } finally {
      setLoading(false);
    }
  };
  if (!isOpen) return null;
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>重命名对话</h3>
          <button className={styles.closeBtn} onClick={onClose}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="输入新的对话标题"
            className={styles.input}
            autoFocus
            maxLength={50}
          />
          <div className={styles.actions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelBtn}
              disabled={loading}
            >
              取消
            </button>
            <button
              type="submit"
              className={styles.confirmBtn}
              disabled={loading || !newTitle.trim()}
            >
              {loading ? "保存中..." : "确定"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SessionRenameModal;
