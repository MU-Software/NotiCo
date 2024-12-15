import { Notifications } from "@mui/icons-material"
import { SvgIcon } from "@mui/material"

export const MSName: string = import.meta.env.VITE_MICROSERVICE_NAME ?? 'NotiCo'
export const MSDomain: string = import.meta.env.VITE_MICROSERVICE_DOMAIN ?? ''
export const MSIcon: typeof SvgIcon = Notifications
