import { useNavigate, useParams, useLocation } from "react-router-dom";
import Back from "./Back";
import DetailTable from "./DetailTable";
import styles from "./SelectedLibrary.module.css";
import { useEffect, useMemo, useRef, useState } from "react";
import { listDocuments, documentDetail } from "./api/user";
function SelectedLibrary() {
  const nav = useNavigate();
  const { id } = useParams();
  const location = useLocation();
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);
  const sortKey = (arr) => {
    const a = Array.isArray(arr) ? arr.slice() : [];
    a.sort((x, y) => String(x.id).localeCompare(String(y.id)));
    return JSON.stringify(
      a.map((o) => ({
        id: o.id,
        title: o.title,
        create_at: o.create_at,
        chunk_count: o.chunk_count,
        content: o.content,
        name: o.name,
      }))
    );
  };
  const currentSig = useMemo(() => sortKey(pages), [pages]);
  async function fetchAll() {
    const base = await listDocuments(id);
    const details = await Promise.all(
      base.map((item) => documentDetail(item.id).catch(() => null))
    );
    const merged = base.map((item, i) => {
      const det = details[i] || {};
      return {
        ...item,
        file_type: undefined,
        chunk_count: det.chunk_count ?? item.chunk_count,
        content: det.content ?? item.content,
      };
    });
    return merged;
  }
  const refreshData = async () => {
    setLoading(true);
    try {
      const merged = await fetchAll();
      setPages(merged);
    } catch (error) {
      console.error("加载文档失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let alive = true;
    refreshData();
    return () => {
      alive = false;
    };
  }, [id, location.key, location.state?.refresh]);

  useEffect(() => {
    clearInterval(timerRef.current);
    timerRef.current = setInterval(async () => {
      try {
        const next = await fetchAll();
        const nextSig = sortKey(next);
        if (nextSig !== currentSig) setPages(next);
      } catch {}
    }, 60 * 1000);
    return () => {
      clearInterval(timerRef.current);
    };
  }, [id, currentSig]);

  return (
    <div className={styles.main}>
      <div className={styles.header}>
        <div className={styles.first}>
          <Back />
          <h2>知识库</h2>
        </div>
        <button className={styles.btn} onClick={() => nav("upload")}>
          + 添加新知识
        </button>
      </div>
      <hr className={styles.hr} />
      <div className={styles.libraries}>
        {loading ? (
          <div>加载中...</div>
        ) : (
          <DetailTable pages={pages} onDeleteSuccess={refreshData} />
        )}
      </div>
    </div>
  );
}

export default SelectedLibrary;
