import { Outlet } from "react-router-dom"
import TransformImages from "./TransformImages"
import styles from './HomePage.module.css'
function HomePage() {
    return (
      <div className={styles.body}>
        <div className={styles.container}>
          <TransformImages />
          <Outlet />
        </div>
      </div>
    );
}

export default HomePage
