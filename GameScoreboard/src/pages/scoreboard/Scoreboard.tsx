import {useEffect, useState} from "react";
import {differenceInMilliseconds, parseISO} from "date-fns";

import Leaderboard from "../../components/leaderboard/Leaderboard.tsx";
import ProgressBar from "@ramonak/react-progress-bar";
import Clock from "../../components/clock/Clock.tsx";
import {apiClient} from "../../client/client.ts";

import "./scoreboard.css"


const Scoreboard = () => {
    const [data, setData] = useState<{ name?: number }>({});

    useEffect(() => {
        fetchData()
        const intervalId = setInterval(() => {
            fetchData()
        }, 5000);

        return () => clearInterval(intervalId); // Cleanup on component unmount
    }, []);

    const fetchData = () => {
        apiClient
            .get<{ name?: number }>("api/score/get")
            .json()
            .then(setData)
    }

    const getTimeLeftInPercentage = (startTimeTimestamp: string, deadLineTimestamp: string): number => {
        const start = parseISO(startTimeTimestamp);
        const deadline = parseISO(deadLineTimestamp);
        const now = new Date();
        const totalDuration = differenceInMilliseconds(deadline, start);
        const timeLeft = differenceInMilliseconds(deadline, now);
        return (timeLeft / totalDuration) * 100;
    };

    const startTimeTimestamp = import.meta.env.VITE_START_BBR_TIMESTAMP
    const deadlineTimestamp = import.meta.env.VITE_END_BBR_TIMESTAMP


    const sortedLeaderboardData = Object.entries(data).map(d => ({
        name: d[0],
        score: d[1]
    }))
        .sort((a, b) => a.score - b.score)
        .reverse()
        .map((d, i) => ({...d, placement: i + 1}));

    return (
        <main className="container">
            <div className="leaderboard-container">
                <Leaderboard
                    className="leaderboard"
                    data={sortedLeaderboardData.slice(0, 10)}
                />
                {sortedLeaderboardData.length > 10 &&
                    <Leaderboard
                        className="leaderboard"
                        data={sortedLeaderboardData.slice(10, 20)}
                    />
                }
            </div>
            <div className="countdown">
                <ProgressBar className="progress-bar"
                             customLabelStyles={{display: "none"}}
                             completed={100 - getTimeLeftInPercentage(startTimeTimestamp, deadlineTimestamp)}/>
                <Clock timestamp={deadlineTimestamp}/>
            </div>
        </main>
    )
}
export default Scoreboard