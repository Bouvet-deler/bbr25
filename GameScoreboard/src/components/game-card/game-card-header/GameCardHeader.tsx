import "./game-card-header.css"
import {CurrentState, GameState} from "../../../types/GameState.ts";

interface Props {
    header: string,
    subheader: string,
    gameState: GameState
}

const GameCardHeader = ({ gameState, header, subheader }: Props) => {

    const getGameCardHeaderColor = () => {
        if(gameState.currentState === CurrentState.REGISTRERING) {
            return "#333333"
        }
        switch (header) {
            case "Game 1":
                return "#A3EAFF";
            case "Game 2":
                return "#FF5F00";
            case "Game 3":
                return "#FF9BF5";
            case "Game 4":
                return "#F3D35E";
            case "Game 5":
                return "#00FF00";
            default:
                return "#FF5F00"
        }
    }

    return (
        <div className="game-card-header" style={{background: getGameCardHeaderColor(), color: gameState.currentState === CurrentState.REGISTRERING ? "#C1C1C1" : "#000000"}}>
            <h3>
                {header}
            </h3>
            <h4>
                {subheader}
            </h4>
        </div>
    )
}
export default GameCardHeader