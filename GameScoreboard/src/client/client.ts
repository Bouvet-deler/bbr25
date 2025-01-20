import ky from "ky";

export const apiClient = ky.create({
    prefixUrl: import.meta.env.VITE_BACKEND_URL,
    throwHttpErrors: true,
    timeout: 20_000,
})