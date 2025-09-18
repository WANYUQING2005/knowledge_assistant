// src/components/Modal/Modal.jsx
import { useEffect } from "react";
import styles from "./Modal.module.css";
import { createKnowledgeLibrary } from "./api/user";
export default function Modal({ open, title = "", onClose, children ,name,description,setOpen,refresh}) {
  if (!open) return null;
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const onBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose?.();
  };
  return (
    <div className={styles.backdrop} onMouseDown={onBackdropClick}>
      <div className={styles.dialog} onMouseDown={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3 className={styles.title}>{title}</h3>
          <button className={styles.close} onClick={onClose} >
            ×
          </button>
        </div>
        <div className={styles.body}>{children}</div>
        <div className={styles.footer}>
          <button className={styles.ghost} onClick={onClose}>
            取消
          </button>
          <button className={styles.primary } onClick={async ()=>{
            await createKnowledgeLibrary({"name":name,"description":description,"embed_model":"256"})
            refresh()
            onClose()
          }}>创建</button>
        </div>
      </div>
    </div>
  );
}
