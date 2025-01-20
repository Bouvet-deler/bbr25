export interface PlayerStateData {
    name: string,
    coins: number,
    fields: Array<unknown>,
    hand: number,
    drawnCards: Array<unknown>,
    tradedCards: Array<unknown>,
    isActive: boolean
}

export enum CurrentState {
    REGISTRERING = "Registering",
}

export enum Phases {
    PLANTING = "Planting",
    PLANTING_OPTIONAL = "PlantingOptional",
    TRADING = "Trading",
    TRADE_PLANTING = "TradePlanting"
}

export interface GameState {
    round: number,
    currentPlayer: string,
    currentPhase: Phases,
    currentState: CurrentState,
    "phaseTimeLeft": "",
    "players": Array<PlayerStateData>
}

