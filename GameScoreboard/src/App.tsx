import Scoreboard from "./pages/scoreboard/Scoreboard.tsx";
import {BrowserRouter, Route, Routes} from "react-router";
import Game from "./pages/game/Game.tsx";
import MarsvilleLogo from "./components/marsville-logo/Logo.tsx";

import './App.css'

function App() {
    return (
        <main>
            <MarsvilleLogo/>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Scoreboard/>}/>
                    <Route path="/game" element={<Game/>}/>
                </Routes>
            </BrowserRouter>
        </main>
    )
}

export default App