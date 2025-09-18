import { useRef, useState } from "react";
import Back from "./Back";
import Header from "./Header";
import styles from "./NewKnowledge.module.css";
import FileSection from "./FileSection";
import SetNewKnowledge from "./SetNewKnowledge";

function NewKnowledge() {
  const inputRef = useRef(null);
  const [step, setStep] = useState(1);
  const [files, setFiles] = useState([]);
  const [dragging, setDragging] = useState(false);

  const handleFileChange = (e) => {
    const f = Array.from(e.target.files || []);
    if (!f) return;
    setFiles(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = Array.from(e.dataTransfer.files || []);
    if (!f) return;
    setFiles(f);
  };

  return (
    <div className={styles.background}>
      <Header />
      <div className={styles.main}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <Back func={setStep} />
            <h2>导入知识</h2>
          </div>
          <button className={styles.btn}>+ 添加新知识</button>
        </div>

        <div className={styles.mainpage}>
          <div className={styles.left}>
            <div className={styles.stepRow}>
              <div className={`${styles.circle} ${styles.active}`}>1</div>
              <span className={styles.textactive}>上传知识</span>
            </div>
            <div className={`${styles.line} ${styles.activeLine}`}></div>
            <div className={styles.stepRow}>
              <div
                className={`${step > 1 ? styles.active : ""} ${styles.circle}`}
              >
                2
              </div>
              <span className={step > 1 ? styles.textactive : styles.textMuted}>
                知识设置
              </span>
            </div>
          </div>

          {step > 1 ? (
            <SetNewKnowledge files={files} />
          ) : (
            <div className={styles.right}>
              <div className={styles.sectionTitle}>导入类型</div>

              <div
                className={`${styles.box} ${
                  dragging ? styles.boxDragging : ""
                }`}
                role="button"
                tabIndex={0}
                onClick={() => inputRef.current?.click()}
                onKeyDown={(e) =>
                  (e.key === "Enter" || e.key === " ") &&
                  inputRef.current?.click()
                }
                onDragEnter={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragOver={(e) => e.preventDefault()}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
              >
                <input
                  ref={inputRef}
                  className={styles.input}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.xlsx,.xls,.csv"
                  onChange={handleFileChange}
                />
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
                  <path
                    d="M12 16V9m0 0l-2.5 2.5M12 9l2.5 2.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className={styles.lines}>
                  <span className={styles.link}>点击上传</span>
                  ，或拖放文件到此处
                </div>
                <div className={styles.tip}>
                  支持
                  pdf、docx、doc、pptx、ppt、txt、md、xlsx、xls、csv，单个≤100M
                </div>
              </div>

              <FileSection files={files} />

              <div className={styles.actions}>
                <button className={styles.btn} onClick={() => setStep(2)}>
                  下一步
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default NewKnowledge;
