import { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Table, TableBody, TableCell, TableContainer, TableRow, Chip, Stack, Button, Box } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

export default function Monitor() {
  const [live, setLive] = useState<'loading' | 'up' | 'down'>('loading');
  const [ready, setReady] = useState<'loading' | 'up' | 'down'>('loading');

  const check = async () => {
    setLive('loading'); setReady('loading');
    try { const r = await fetch('/health/live'); setLive(r.ok ? 'up' : 'down'); } catch { setLive('down'); }
    try { const r = await fetch('/health/ready'); setReady(r.ok ? 'up' : 'down'); } catch { setReady('down'); }
  };

  useEffect(() => { check(); }, []);

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={600}>Giám sát</Typography>
        <Button startIcon={<RefreshIcon />} onClick={check} size="small">Refresh</Button>
      </Stack>

      <Stack direction="row" spacing={2} mb={4}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="overline" color="text.secondary">Liveness</Typography>
            <Chip label={live === 'up' ? '● Online' : live === 'down' ? '✕ Offline' : '...'} color={live === 'up' ? 'success' : 'error'} sx={{ mt: 1 }} />
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="overline" color="text.secondary">Readiness</Typography>
            <Chip label={ready === 'up' ? '● Ready' : ready === 'down' ? '✕ Unhealthy' : '...'} color={ready === 'up' ? 'success' : 'error'} sx={{ mt: 1 }} />
          </CardContent>
        </Card>
      </Stack>

      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>API Endpoints</Typography>
          <TableContainer>
            <Table size="small">
              <TableBody>
                {[
                  ['GET', '/health/live', 'Liveness probe'],
                  ['GET', '/health/ready', 'Readiness + DB check'],
                  ['GET', '/cases', 'Danh sách hồ sơ (phân quyền)'],
                  ['POST', '/cases', 'Tạo hồ sơ mới'],
                  ['GET', '/cases/{id}', 'Chi tiết hồ sơ (ETag)'],
                  ['POST', '/cases/{id}/complete-task', 'Hoàn thành bước (ETag + enforce)'],
                  ['POST', '/cases/{id}/cancel', 'Hủy tiến trình (async 202)'],
                  ['GET', '/cases/{id}/history', 'Lịch sử tiến trình'],
                  ['GET', '/cases/{id}/history/verify', 'Kiểm tra toàn vẹn audit'],
                  ['GET', '/definitions', 'Danh sách quy trình'],
                  ['POST', '/definitions', 'Tạo quy trình mới'],
                  ['GET', '/processes/{key}/state', 'Trạng thái engine'],
                ].map(([method, path, desc]) => (
                  <TableRow key={path}>
                    <TableCell width={80}>
                      <Chip label={method} size="small" color={method === 'POST' ? 'warning' : 'info'} />
                    </TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: 13 }}>{path}</TableCell>
                    <TableCell>{desc}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
