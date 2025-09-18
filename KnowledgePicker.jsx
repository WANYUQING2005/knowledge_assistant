import { useEffect, useMemo, useState, memo } from "react";
import styles from "./KnowledgePicker.module.css";

function KnowledgePicker({
  kbs = [],
  value = [], 
  onChange = () => {},
  dbOptions = ["默认数据库"],
  dbValue = "默认数据库",
  onDBChange = () => {},
  onCreate = () => {},
  onConfirm = () => {},
  className = "",
}) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(value);
  const[db, setDb] = useState(dbValue);
  const shallowEqualArr = (a, b) =>
    a === b ||
    (Array.isArray(a) &&
      Array.isArray(b) &&
      a.length === b.length &&
      a.every((v, i) => v === b[i]));
  useEffect(() => {
    setSelected((prev) => (shallowEqualArr(prev, value) ? prev : value));
  }, [value]);
  useEffect(() => {
    setDb((prev) => (prev === dbValue ? prev : dbValue));
  }, [dbValue]);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return kbs;
    return kbs.filter((k) => (k.name || "").toLowerCase().includes(q));
  }, [kbs, query]);
  const toggle = (id) => {
    const next = selected.includes(id)
      ? selected.filter((x) => x !== id)
      : [...selected, id];
    setSelected(next);
    onChange(next);
  };
  const selectAll = () => {
    const ids = filtered.map((k) => k.id);
    const next = Array.from(new Set([...selected, ...ids]));
    setSelected(next);
    onChange(next);
  };
  const clearAll = () => {
    const set = new Set(filtered.map((k) => k.id));
    const next = selected.filter((id) => !set.has(id));
    setSelected(next);
    onChange(next);
  };
  const handleDb = (v) => {
    setDb(v);
    onDBChange(v);
  };
  return (
    <div className={`${styles.card} ${className}`}>
      <div className={styles.head}>
        <div className={styles.title}>选择知识库</div>
        <div className={styles.count}>已选 {selected.length} 个</div>
      </div>
      <div className={styles.controls}>
        <input
          className={styles.search}
          placeholder="搜索知识库"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className={styles.select}
          value={db}
          onChange={(e) => handleDb(e.target.value)}
        >
          {dbOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>
      <div className={styles.tools}>
        <button className={styles.ghost} onClick={selectAll}>
          全选当前结果
        </button>
        <button className={styles.ghost} onClick={clearAll}>
          清空当前结果
        </button>
        <div className={styles.spacer} />
        <button className={styles.ghost} onClick={onCreate}>
          新建知识库
        </button>
      </div>
      <div className={styles.list}>
        {filtered.length === 0 && (
          <div className={styles.empty}>没有匹配的知识库</div>
        )}
        {filtered.map((k) => (
          <label key={k.id} className={styles.item} title={k.name}>
            <input
              type="checkbox"
              checked={selected.includes(k.id)}
              onChange={() => toggle(k.id)}
            />
            <div className={styles.meta}>
              <div className={styles.name}>{k.name}</div>
              {/* <div className={styles.sub}>
                {k.updated ? `更新于 ${k.updated}` : "无更新时间"}
                {k.size ? ` · ${k.size}` : ""}
              </div> */}
            </div>
          </label>
        ))}
      </div>
      <div className={styles.actions}>
        <button
          className={styles.ghost}
          onClick={() => {
            setSelected([]);
            onChange([]);
          }}
        >
          清空全部
        </button>
        <button
          className={styles.primary}
          onClick={() => onConfirm(selected, db)}
        >
          确定
        </button>
      </div>
    </div>
  );
}

export default memo(KnowledgePicker);
