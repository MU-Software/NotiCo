import { ChevronLeft, Menu } from '@mui/icons-material'
import { Box, Button, CssBaseline, Divider, IconButton, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Tooltip, styled, useTheme } from '@mui/material'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { SnackbarProvider } from 'notistack'
import React from 'react'
import { createRoot } from 'react-dom/client'
import { ErrorBoundary } from 'react-error-boundary'
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import * as R from 'remeda'

import { MiniVariantAppBar, MiniVariantDrawer } from './components/sidebar'
import { MSIcon, MSName } from './consts/application'
import { GLOBAL_INITIAL_STATE, GlobalContext, GlobalStateType } from './models/context'
import { HomeRoute, ROUTES, RouteDef, useRouteInfo } from './pages'

import '@fontsource/roboto/300.css'
import '@fontsource/roboto/400.css'
import '@fontsource/roboto/500.css'
import '@fontsource/roboto/700.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      gcTime: 24 * 60 * 60 * 1000, // 24 hours
      staleTime: 3 * 1000, // 3 seconds
      refetchOnWindowFocus: false,
    }
  },
})

const CenteredFlexStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
}

const PageOuterContainer = styled(Box)(() => ({
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}))

const PageMidContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  height: '100%',
  overflowY: 'scroll',
  backgroundColor: theme.palette.grey[200],
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
}))

const PageInnerContainer = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(4),
  width: '95%',
  height: 'fit-content',
  minHeight: `calc(100% - ${theme.spacing(4)})`,
  // 'xs' | 'sm' | 'md' | 'lg' | 'xl',
  [theme.breakpoints.up('sm')]: { width: '95%' },
  [theme.breakpoints.up('md')]: { width: '800px' },
  [theme.breakpoints.up('lg')]: { width: '1024px' },
  [theme.breakpoints.up('xl')]: { width: '1200px' },
}))

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
}))

export const App: React.FC = () => {
  const theme = useTheme()
  const routeInfo = useRouteInfo()
  const navigate = useNavigate()
  const location = useLocation()
  const [state, dispatch] = React.useState<GlobalStateType>(GLOBAL_INITIAL_STATE)
  const toggleDrawer = () => dispatch((ps) => ({ ...ps, showDrawer: !ps.showDrawer }))

  const ErrorInfo: React.FC<{ error: unknown }> = ({ error }) => <pre>{R.isObjectType(error) ? error.toLocaleString() : '에러 발생, 새로고침 해주세요.'}</pre>
  const SidebarItem: React.FC<{ routeInfo: RouteDef }> = ({ routeInfo }) => <ListItem key={routeInfo.path} disablePadding>
    <ListItemButton
      sx={{ minHeight: 48, px: 2.5, justifyContent: state.showDrawer ? 'initial' : 'center' }}
      onClick={() => navigate(routeInfo.path)}>
      <ListItemIcon sx={{ minWidth: 0, justifyContent: 'center', mr: state.showDrawer ? 3 : 'auto' }}><routeInfo.icon /></ListItemIcon>
      {state.showDrawer && <ListItemText primary={routeInfo.title} />}
    </ListItemButton>
  </ListItem>

  return <ErrorBoundary fallbackRender={({ error }) => <ErrorInfo error={error} />}>
    <GlobalContext.Provider value={{ state, dispatch }}>
      <Box sx={{ height: '100%' }}>
        <CssBaseline />
        <MiniVariantAppBar position='fixed' open={state.showDrawer}>
          <Toolbar disableGutters>
            <Box sx={[
              CenteredFlexStyle,
              state.showDrawer && { display: 'none' },
              { width: `calc(${theme.spacing(7)} + 1px)`, [theme.breakpoints.up('sm')]: { width: `calc(${theme.spacing(8)} + 1px)` } },
            ]}>
              <Tooltip title='Menu'>
                <IconButton color='inherit' onClick={toggleDrawer}>
                  <Menu />
                </IconButton>
              </Tooltip>
            </Box>
            {state.showDrawer && <>&nbsp;&nbsp;&nbsp;</>}
            <Button color="inherit" onClick={() => navigate(HomeRoute.path)} startIcon={<MSIcon />}>
              <b>{MSName} Admin</b>
            </Button>
            &nbsp;&rsaquo;&nbsp;
            <Button color="inherit" onClick={() => navigate(routeInfo.path === "/*" ? location.pathname : routeInfo.path)} startIcon={<routeInfo.icon />}>
              <b>{routeInfo.title}</b>
            </Button>
          </Toolbar>
        </MiniVariantAppBar>

        <Box component='main' sx={{ display: 'flex', flexDirection: 'row', width: '100%', height: '100%' }}>
          <MiniVariantDrawer variant='permanent' open={state.showDrawer}>
            <DrawerHeader>
              <IconButton onClick={toggleDrawer}>
                <ChevronLeft />
              </IconButton>
            </DrawerHeader>
            <Divider />
            <List>{ROUTES.filter(r => r.showInSidebar).map(r => <SidebarItem key={r.key} routeInfo={r} />)}</List>
          </MiniVariantDrawer>
          <PageOuterContainer>
            <Toolbar />
            <PageMidContainer>
              <PageInnerContainer>
                <Routes>{ROUTES.map((r) => <Route key={r.key} element={r.element} path={r.path} />)}</Routes>
              </PageInnerContainer>
            </PageMidContainer>
          </PageOuterContainer>
        </Box>
      </Box>
    </GlobalContext.Provider>
  </ErrorBoundary>
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SnackbarProvider>
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ReactQueryDevtools initialIsOpen={false} />
          <App />
        </QueryClientProvider>
      </BrowserRouter>
    </SnackbarProvider>
  </React.StrictMode >
)
