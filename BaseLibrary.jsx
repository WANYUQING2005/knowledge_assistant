import Header from "./Header"
import styles from './BaseLibrary.module.css'
import Allknowledge from "./allknowledge"
import Modal from "./Modal"
function BaseLibrary() {
    return (
        <div className={styles.background}>
            <Header/>
            <Allknowledge/>
        </div>
    )
}

export default BaseLibrary
