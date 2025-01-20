import "./leaderboard.css"

interface Props {
    className: string;
    data: Array<{
        name: string,
        score: number
        placement: number
    }>
}

const Leaderboard = ({data, className}: Props) => {
    return (
        <table className={className}>
            <tbody>
            {data.map((rowData) => (
                <tr key={rowData.name}>
                    <td>{rowData.placement}</td>
                    <td>{rowData.name}</td>
                    <td>{rowData.score}</td>
                </tr>
            ))}
            </tbody>
        </table>
)
}
export default Leaderboard