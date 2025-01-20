import SoppIcon from "../sopp-icon/SoppIcon.tsx";
import "./score-with-icon.css"

interface Props {
    score: number
}

const ScoreWithIcon = (props: Props) => {
    return (
        <div className="score-with-icon">
            <SoppIcon/>
            <p className="score">{props.score}</p>
        </div>
    )
}
export default ScoreWithIcon