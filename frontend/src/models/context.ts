import React from 'react'

export type GlobalStateType = {
  showDrawer: boolean
}

export const GLOBAL_INITIAL_STATE: GlobalStateType = {
  showDrawer: false,
}

export const GlobalContext = React.createContext<{
  state: GlobalStateType
  dispatch: React.Dispatch<React.SetStateAction<GlobalStateType>>
}>({
  state: GLOBAL_INITIAL_STATE,
  dispatch: () => { },
})
