import styles from "./SetNewKnowledge.module.css";
import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { uploadDocuments } from "./api/user";

function SetNewKnowledge({ files }) {
  const { id } = useParams();
  const nav = useNavigate();
  const [pending, setPending] = useState(false);
  const [percent, setPercent] = useState(0);
  const [error, setError] = useState("");
  const [llmChoice, setLlmChoice] = useState(1);
  const modelOptions = [
    { value: 1, label: "Deepseek" },
    { value: 2, label: "ZhiPuAI" },
    { value: 3, label: "Qwen" },
  ];

  async function onConfirm() {
    if (!files || !files.length || pending) return;
    setPending(true);
    setError("");
    try {
      await uploadDocuments({
        kb_id: id,
        files,
        llm_choice: llmChoice,
        onProgress: (p) => setPercent(p.percent),
      });
      nav(`/baselibrary/${id}`, {
        replace: true,
        state: { refresh: Date.now() },
      });
    } catch (e) {
      setError(String(e));
    } finally {
      setPending(false);
      setPercent(0);
    }
  }
  return (
    <div className={styles.right}>
      <div className={styles.head}>
        <div className={styles.title}>待导入文件</div>
        <div className={styles.count}>{files.length} 个文件</div>
      </div>

      <div className={styles.modelSelector}>
        <label className={styles.modelLabel}>LLM模型</label>
        <select
          className={styles.modelSelect}
          value={llmChoice}
          onChange={(e) => setLlmChoice(Number(e.target.value))}
          disabled={pending}
        >
          {modelOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.scroller}>
        {files.map((file, i) => (
          <div key={i} className={styles.row}>
            <span className={styles.name} title={file.name}>
              {file.name}
            </span>
            <span className={styles.size}>{Math.ceil(file.size / 1024)}KB</span>
          </div>
        ))}
        {files.length === 0 && <div className={styles.empty}>暂无文件</div>}
      </div>
      <div className={styles.actions}>
        <button
          className={styles.primary}
          disabled={pending || files.length === 0}
          onClick={onConfirm}
        >
          {pending ? `上传中… ` : "确认"}
        </button>
        <button className={styles.ghost} onClick={() => nav(-1)}>
          取消
        </button>
      </div>
      {error ? <div className={styles.err}>{error}</div> : null}
    </div>
  );
}

export default SetNewKnowledge;
