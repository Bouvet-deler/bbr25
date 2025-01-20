import Countdown from "react-countdown";
import "./clock.css"

interface Props {
    timestamp: string | Date | number
}

const Clock = (props: Props) => {
    return (
        <Countdown className="clock" date={props.timestamp} daysInHours={true}/>
    )
}
export default Clock