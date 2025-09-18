import Header from "./Header"
import styles from './DetailLibrary.module.css'
import SelectedLibrary from "./SelectedLibrary";
import Back from "./Back";
function DetailLibrary() {
    return (
      <div className={styles.background}>
        
        <Header />
        <SelectedLibrary/>
      </div>
    );
}

export default DetailLibrary
