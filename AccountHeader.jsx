import img1 from './assets/nahidaimg/8.png'
import styles from './AccountHeader.module.css'
function AccountHeader() {
    return (
        <div>
            <img className={styles.img} src={img1} alt='personal avator'/>
        </div>
    )
}

export default AccountHeader
