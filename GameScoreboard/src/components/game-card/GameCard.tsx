import PlayerState from "./player-state/PlayerState.tsx";
import GameCardHeader from "./game-card-header/GameCardHeader.tsx";
import {GameState} from "../../types/GameState.ts";

import "./game-card.css"

interface Props {
    title: string,
    gameState: GameState
}

const GameCard = ({title, gameState}: Props) => {
    const {players} = gameState;


    return (
        <div className="game-card">
            <GameCardHeader header={title} subheader={`Runde ${gameState.round} / 3`} gameState={gameState}/>
            <div className="player-state-container">
                <PlayerState
                    gameState={gameState}
                    player={players[0]}
                />
                <PlayerState
                    gameState={gameState}
                    player={players[1]}
                />
                <PlayerState
                    gameState={gameState}
                    player={players[2]}
                />
                <PlayerState
                    gameState={gameState}
                    player={players[3]}
                />
                <PlayerState
                    gameState={gameState}
                    player={players[4]}
                />
            </div>
        </div>
    )
}
export default GameCard