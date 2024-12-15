import React from 'react'

import { Close, Description, Home, Send } from '@mui/icons-material'
import { SvgIcon } from "@mui/material"
import { useLocation } from 'react-router-dom'

import { HomePage } from './home'
import { SendManagerPage } from './sendManager'
import { TemplateManagerPage } from './templateManager'

export type RouteDef = {
  key: string
  icon: typeof SvgIcon
  title: string
  path: string
  element: React.ReactNode
  showInSidebar: boolean
}

export const HomeRoute: RouteDef = {
  key: 'home',
  icon: Home,
  title: 'Home',
  path: '/',
  element: <HomePage />,
  showInSidebar: false,
}

export const NotFoundRoute: RouteDef = {
  key: 'not-found',
  icon: Close,
  title: 'Not Found',
  path: '/*',
  element: <div>Not Found</div>,
  showInSidebar: false,
}

export const ROUTES: RouteDef[] = [
  {
    key: 'template-manager',
    icon: Description,
    title: 'Template Manager',
    path: '/template-manager',
    element: <TemplateManagerPage />,
    showInSidebar: true,
  },
  {
    key: 'send-manager',
    icon: Send,
    title: 'Send Manager',
    path: '/send-manager',
    element: <SendManagerPage />,
    showInSidebar: true,
  },
  HomeRoute,
  NotFoundRoute,
]

export const useRouteInfo: () => RouteDef = () => {
  const l = useLocation()
  return ROUTES.find(
    r => r.path !== '*' && ((r.path === '/' && l.pathname === '/') || (r.path !== '/' && l.pathname.startsWith(r.path.replace('/*', ''))))
  ) || NotFoundRoute
}
