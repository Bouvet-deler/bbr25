import {useEffect, useState} from "react";
import {apiClient} from "../../client/client.ts";
import {GameState} from "../../types/GameState.ts";
import GameCard from "../../components/game-card/GameCard.tsx";

import "./game.css"

const Game = () => {
    const [data, setData] = useState<Array<GameState>>();

    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchData()
        }, 1000);

        return () => clearInterval(intervalId); // Cleanup on component unmount
    }, []);

    const fetchData = () => {
        apiClient
            .get<Array<GameState>>("api/game/all")
            .json()
            .then(setData)
    }

    return (
        <main className="game-view-container">
            {data && data.map((game, index) => {
                const title =  `Game ${index + 1}`;
                return (
                    <GameCard key={title} title={title} gameState={game}/>
                );
            })}
        </main>
    )
}
export default Game