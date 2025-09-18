import styles from "./DetailTable.module.css";
import { useState } from "react";
import { deleteDocument } from "./api/user";
function extFromName(n) {
  if (!n || typeof n !== "string") return "-";
  const i = n.lastIndexOf(".");
  if (i < 0) return "-";
  return n.slice(i + 1).toLowerCase();
}
function formatPlus8ToMinute(iso) {
  if (!iso) return "-";
  const t = new Date(iso);
  if (isNaN(t.getTime())) return "-";
  const plus = new Date(t.getTime() + 8 * 60 * 60 * 1000);
  const y = plus.getFullYear();
  const m = String(plus.getMonth() + 1).padStart(2, "0");
  const d = String(plus.getDate()).padStart(2, "0");
  const hh = String(plus.getHours()).padStart(2, "0");
  const mm = String(plus.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${d} ${hh}:${mm}`;
}
function cut(s, n) {
  if (!s || typeof s !== "string") return "-";
  if (s.length <= n) return s;
  return s.slice(0, n) + "...";
}
function DetailTable({ pages = [], onDeleteSuccess }) {
  const [deletingId, setDeletingId] = useState(null);
  const handleDelete = async (id, name) => {
    if (!window.confirm(`确定要删除文档"${name}"吗？此操作不可撤销。`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteDocument(id);
      onDeleteSuccess && onDeleteSuccess();
    } catch (error) {
      console.error("删除失败:", error);
      alert("删除失败，请重试");
    } finally {
      setDeletingId(null);
    }
  };
  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <colgroup>
          <col style={{ width: "28%" }} />
          <col style={{ width: "12%" }} />
          <col style={{ width: "16%" }} />
          <col style={{ width: "32%" }} />
          <col style={{ width: "8%" }} />
          <col style={{ width: "4%" }} />
        </colgroup>
        <thead>
          <tr className={styles.item}>
            <th className={`${styles.item} ${styles.thead} ${styles.left}`}>
              文件名
            </th>
            <th className={`${styles.item} ${styles.thead}`}>文件类型</th>
            <th className={`${styles.item} ${styles.thead}`}>创建时间</th>
            <th className={`${styles.item} ${styles.thead}`}>内容</th>
            <th className={`${styles.item} ${styles.thead}`}>文本分段</th>
            <th className={`${styles.item} ${styles.thead} ${styles.right}`}>
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          {pages.map((r) => {
            const name = r.title || r.name || r.id;
            const createTime = formatPlus8ToMinute(r.create_at);
            const content = r.content ? cut(r.content, 80) : "-";
            const ext = extFromName(r.title || r.name || "");
            const chunk = r.chunk_count ?? r.chunk ?? "-";
            return (
              <tr key={r.id} className={`${styles.item} ${styles.row}`}>
                <td
                  className={`${styles.item} ${styles.left} ${styles.name}`}
                  title={name}
                >
                  {name}
                </td>
                <td className={styles.item}>{ext}</td>
                <td className={styles.item}>{createTime}</td>
                <td className={styles.item}>{content}</td>
                <td className={styles.item}>{chunk}</td>
                <td className={`${styles.item} ${styles.right}`}>
                  <button
                    className={styles.op}
                    onClick={() => handleDelete(r.id, name)}
                    disabled={deletingId === r.id}
                    title="删除文档"
                  >
                    {deletingId === r.id ? "删除中..." : "×"}
                  </button>
                </td>
              </tr>
            );
          })}
          {pages.length === 0 && (
            <tr className={`${styles.item} ${styles.row}`}>
              <td className={`${styles.item} ${styles.left}`} colSpan={6}>
                暂无数据
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default DetailTable;
