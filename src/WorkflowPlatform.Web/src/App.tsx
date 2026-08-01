import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Designer from './pages/Designer';
import Cases from './pages/Cases';
import Monitor from './pages/Monitor';

const theme = createTheme({
  palette: {
    primary: { main: '#1565c0' },
    secondary: { main: '#ef6c00' },
  },
  typography: { fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif' },
  shape: { borderRadius: 10 },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/designer" element={<Designer />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/monitor" element={<Monitor />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}
