import { useCases } from '../hooks/useCases';
import { Card, CardContent, Typography, Box, Chip, Stack } from '@mui/material';

export default function Dashboard() {
  const { cases } = useCases();
  const total = cases.length;
  const running = cases.filter(c => c.currentTaskId).length;
  const done = cases.filter(c => c.workflowStatus === 'Hoan tat').length;
  const rejected = cases.filter(c => c.workflowStatus === 'Tu choi').length;

  const stats = [
    { label: 'Tong ho so', value: total, color: '#1565c0' },
    { label: 'Dang xu ly', value: running, color: '#e65100' },
    { label: 'Hoan thanh', value: done, color: '#2e7d32' },
    { label: 'Tu choi', value: rejected, color: '#c62828' },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>Dashboard</Typography>
      <Stack direction="row" spacing={2} sx={{ mb: 4, flexWrap: 'wrap', gap: 2 }}>
        {stats.map(s => (
          <Card key={s.label} sx={{ flex: 1, minWidth: 180 }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">{s.label}</Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, color: s.color }}>{s.value}</Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Hoat dong gan day</Typography>
          {cases.slice(-5).reverse().map((c, i) => (
            <Box key={i} sx={{ py: 1, borderBottom: '1px solid', borderColor: 'divider', '&:last-child': { borderBottom: 0 } }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>{c.title}</Typography>
              <Chip label={c.workflowStatus} size="small" sx={{ mt: 0.5 }}
                color={c.workflowStatus === 'Hoan tat' ? 'success' : c.workflowStatus === 'Tu choi' ? 'error' : 'info'} />
            </Box>
          ))}
          {cases.length === 0 && <Typography color="text.secondary">Chua co hoat dong.</Typography>}
        </CardContent>
      </Card>
    </Box>
  );
}
