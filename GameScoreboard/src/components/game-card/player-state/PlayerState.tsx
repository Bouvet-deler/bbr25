import {GameState, Phases, PlayerStateData} from "../../../types/GameState.ts";

import "./player-state.css"
import ScoreWithIcon from "../../score-with-icon/ScoreWithIcon.tsx";
import Clock from "../../clock/Clock.tsx";
import {addMilliseconds} from "date-fns";

interface Props {
    gameState: GameState,
    player?: PlayerStateData
}

const PlayerState = ({gameState, player}: Props) => {
    const currentPlayer = () => {
        return gameState.currentPlayer === player?.name
    }

    if (player === undefined) {
        return (
            <div className="player-state player-state--open">
                <p>Open</p>
            </div>
        )
    }

    if (player?.isActive === false) {
        return (
            <div className="player-state player-state--open">
                <p>{player.name} not active</p>
            </div>
        )
    }


    const addTimeLeftToDate = (timeLeft: string, date: Date): Date => {
        const [hours, minutes, seconds] = timeLeft.split(':');
        const [secs] = seconds.split('.');

        const totalMilliseconds =
            parseInt(hours) * 3600000 +
            parseInt(minutes) * 60000 +
            parseInt(secs) * 1000

        return addMilliseconds(date, totalMilliseconds);
    };

    return (
        <div>
            {!currentPlayer() && (
                <div className="player-state player-state--not-active">
                    <p>{player.name}</p>
                    <ScoreWithIcon score={player.coins} />
                </div>
            )}
            {currentPlayer() && (
                <div className="player-state player-state--active">
                    <div className="player-state-timer">
                        <div>
                            <p>{player.name}</p>
                            <ScoreWithIcon score={player.coins} />
                        </div>
                        <Clock timestamp={addTimeLeftToDate(gameState.phaseTimeLeft, new Date())}/>
                    </div>
                    <div className="phases">
                        <div
                            className={`phase ${gameState.currentPhase === Phases.PLANTING ? "phase--active" : ""}`}>
                            Fase 1
                        </div>
                        <div
                            className={`phase ${gameState.currentPhase === Phases.PLANTING_OPTIONAL ? "phase--active" : ""}`}>
                            Fase 2
                        </div>
                        <div
                            className={`phase ${gameState.currentPhase === Phases.TRADING ? "phase--active" : ""}`}>
                            Fase 3
                        </div>
                        <div
                            className={`phase ${gameState.currentPhase === Phases.TRADE_PLANTING ? "phase--active" : ""}`}>
                            Fase 4
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
export default PlayerState