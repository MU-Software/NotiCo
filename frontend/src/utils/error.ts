import { RequestError } from "../hooks/useAPIs"

export const getErrorString = (error: unknown): string => {
  if (error instanceof RequestError) {
    return error.toAlertString()
  } else if (error instanceof Error) {
    return error.stack ?? error.message ?? `${error}`
  } else {
    return `${error}`
  }
}
