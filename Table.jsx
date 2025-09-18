import { useNavigate } from "react-router-dom";
import { useState } from "react";
import styles from "./Table.module.css";
import { deleteKnowledgeBase } from "./api/user";
function Table({ pages, setPages }) {
  const nav = useNavigate();
  const [deletingId, setDeletingId] = useState(null);
  const handleDelete = async (id, name) => {
    if (!window.confirm(`确定要删除知识库"${name}"吗？此操作不可撤销。`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteKnowledgeBase(id);
      setPages(pages.filter((page) => page.id !== id));
    } catch (error) {
      console.error("删除失败:", error);
      alert("删除失败，请重试");
    } finally {
      setDeletingId(null);
    }
  };
  if (pages.length === 0) {
    return <div className={styles.empty}>暂无数据，请创建新知识库</div>;
  }

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <colgroup>
          <col style={{ width: "18%" }} />
          <col style={{ width: "36%" }} />
          <col style={{ width: "16%" }} />
          <col style={{ width: "16%" }} />
          <col style={{ width: "10%" }} />
          <col style={{ width: "4%" }} />
        </colgroup>
        <thead>
          <tr className={styles.headerRow}>
            <th className={`${styles.item} ${styles.thead} ${styles.left}`}>
              知识库名称
            </th>
            <th className={`${styles.item} ${styles.thead}`}>简介</th>
            <th className={`${styles.item} ${styles.thead}`}>创建时间</th>
            <th className={`${styles.item} ${styles.thead}`}>嵌入维度</th>
            <th className={`${styles.item} ${styles.thead}`}>使用空间</th>
            <th className={`${styles.item} ${styles.thead} ${styles.right}`}>
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          {pages.map((r) => (
            <tr key={r.id} className={styles.row}>
              <td
                className={`${styles.item} ${styles.left} ${styles.name}`}
                onClick={() => nav(`${r.id}`)}
                title={r.name}
              >
                {r.name}
              </td>
              <td
                className={`${styles.item} ${styles.truncate}`}
                title={r.description}
              >
                {r.description}
              </td>
              <td className={styles.item}>
                {new Date(r.create_at)
                  .toLocaleString("zh-CN", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  })
                  .replace(/\//g, "-")
                  .replace(",", "T")}
              </td>
              <td className={styles.item}>{256}</td>
              <td className={styles.item}>{r.storage_size} B</td>
              <td className={`${styles.item} ${styles.right}`}>
                <button
                  className={styles.op}
                  onClick={() => handleDelete(r.id, r.name)}
                  disabled={deletingId === r.id}
                  title="删除知识库"
                >
                  {deletingId === r.id ? "删除中..." : "×"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export default Table;
