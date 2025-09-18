import { useNavigate } from "react-router-dom";
import { FiArrowLeft } from "react-icons/fi";
import styles from "./Back.module.css";

function Back({ func = (a) => {} }) {
  const nav = useNavigate();
  return (
    <button
      onClick={() => {
        nav(-1);
      }}
      className={styles.backButton}
    >
      <FiArrowLeft className={styles.icon} />
    </button>
  );
}

export default Back;
