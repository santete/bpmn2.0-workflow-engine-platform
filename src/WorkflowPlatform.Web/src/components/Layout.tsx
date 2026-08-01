import type { ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Box, TextField
} from '@mui/material';

const DRAWER_WIDTH = 240;

const nav = [
  { label: 'Dashboard', path: '/' },
  { label: 'Thiết kế', path: '/designer' },
  { label: 'Hồ sơ', path: '/cases' },
  { label: 'Giám sát', path: '/monitor' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const loc = useLocation();
  const navi = useNavigate();

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>⚙ WorkflowPlatform</Typography>
          <Box sx={{ flex: 1 }} />
          <TextField
            id="actor-name" size="small" placeholder="Nguoi thao tac"
            sx={{ bgcolor: 'rgba(255,255,255,.15)', borderRadius: 1, width: 200 }}
            slotProps={{ htmlInput: { style: { color: '#fff', padding: '6px 10px' } } }}
          />
        </Toolbar>
      </AppBar>
      <Drawer variant="permanent" sx={{ width: DRAWER_WIDTH, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}>
        <Toolbar />
        <List sx={{ pt: 1 }}>
          {nav.map(n => (
            <ListItemButton key={n.path} selected={loc.pathname === n.path} onClick={() => navi(n.path)}>
              <ListItemIcon><Typography>{['◫','⊞','☰','◉'][nav.indexOf(n)]}</Typography></ListItemIcon>
              <ListItemText primary={n.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box sx={{ flex: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
