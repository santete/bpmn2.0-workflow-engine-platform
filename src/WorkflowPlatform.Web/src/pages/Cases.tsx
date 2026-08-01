import { useState } from 'react';
import { useCases } from '../hooks/useCases';
import { useDefinitions } from '../hooks/useDefinitions';
import { apiGet } from '../api/client';
import type { CaseHistoryEntry } from '../types/models';
import { Card, CardContent, Typography, TextField, Button, Select, MenuItem, FormControl, InputLabel,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, IconButton, Drawer, Box, Stack } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HistoryIcon from '@mui/icons-material/History';

const kindLabels: Record<string, string> = { TaskCompleted: 'Hoan thanh', ProcessCompleted: 'Ket thuc', ProcessRejected: 'Tu choi', ProcessCancelled: 'Da huy' };

export default function Cases() {
  const { cases, create, complete, cancel } = useCases();
  const { defs } = useDefinitions();
  const [title, setTitle] = useState('');
  const [defKey, setDefKey] = useState('case-approval');
  const [filter, setFilter] = useState('');
  const [history, setHistory] = useState<CaseHistoryEntry[]>([]);
  const [drawer, setDrawer] = useState(false);

  const filtered = cases.filter(c => !filter || c.title.toLowerCase().includes(filter.toLowerCase()) || (c.currentTaskName || '').toLowerCase().includes(filter.toLowerCase()));

  const isDecision = (c: typeof cases[0]) => {
    const def = defs.find(d => d.key === c.definitionKey);
    if (!def || !def.endsWithDecision) return false;
    return def.steps[def.steps.length - 1]?.id === c.currentTaskId;
  };

  const showHistory = async (id: string) => {
    try { setHistory(await apiGet<CaseHistoryEntry[]>(`/cases/${id}/history`)); setDrawer(true); }
    catch { alert('Khong the tai lich su.'); }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>Ho so</Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-end', flexWrap: 'wrap', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Quy trinh</InputLabel>
              <Select value={defKey} label="Quy trinh" onChange={e => setDefKey(e.target.value)}>
                {defs.map(d => <MenuItem key={d.key} value={d.key}>{d.name}</MenuItem>)}
              </Select>
            </FormControl>
            <TextField size="small" label="Tieu de ho so" value={title} onChange={e => setTitle(e.target.value)} placeholder="VD: Ho so so 01" sx={{ flex: 1 }} />
            <Button variant="contained" color="secondary" onClick={() => { create({ title: title.trim() || 'Ho so moi', definitionKey: defKey }); setTitle(''); }}>
              Tao ho so
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <Box sx={{ px: 2, pt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Danh sach ho so ({cases.length})</Typography>
          <TextField size="small" placeholder="Loc..." value={filter} onChange={e => setFilter(e.target.value)} sx={{ width: 200 }} />
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Ho so</TableCell><TableCell>Quy trinh</TableCell><TableCell>Trang thai</TableCell>
                <TableCell>Buoc hien tai</TableCell><TableCell>Nguoi TH</TableCell><TableCell>Thao tac</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.length === 0 && <TableRow><TableCell colSpan={6} align="center"><Typography color="text.secondary" sx={{ py: 4 }}>Chua co ho so nao.</Typography></TableCell></TableRow>}
              {filtered.map(c => {
                const dn = defs.find(d => d.key === c.definitionKey)?.name || c.definitionKey;
                const decision = isDecision(c);
                return (
                  <TableRow key={c.id} hover>
                    <TableCell><Typography sx={{ fontWeight: 600 }}>{c.title}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>{c.id.slice(0, 8)}</Typography></TableCell>
                    <TableCell>{dn}</TableCell>
                    <TableCell><Chip label={c.workflowStatus} size="small"
                      color={c.workflowStatus === 'Hoan tat' ? 'success' : c.workflowStatus === 'Tu choi' ? 'error' : c.workflowStatus === 'Da huy' ? 'default' : 'info'} /></TableCell>
                    <TableCell>{c.currentTaskName ? <Chip label={c.currentTaskName} size="small" variant="outlined" /> : '—'}
                      {c.pendingCounterSign && <Typography variant="caption" color="warning.main" sx={{ display: 'block' }}>Cho ky duyet</Typography>}</TableCell>
                    <TableCell>{c.currentTaskAssignee || '—'}</TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={0.5} sx={{ gap: 0.5 }}>
                        {c.currentTaskId && (decision
                          ? <><Button size="small" variant="contained" color="success" onClick={() => complete(c.id, c.currentTaskId!, 'APPROVED')}>Duyet</Button>
                            <Button size="small" variant="contained" color="error" onClick={() => complete(c.id, c.currentTaskId!, 'REJECTED')}>Tu choi</Button></>
                          : <Button size="small" variant="outlined" onClick={() => complete(c.id, c.currentTaskId!)}> ▶ {c.currentTaskName}</Button>)}
                        <IconButton size="small" onClick={() => showHistory(c.id)}><HistoryIcon fontSize="small" /></IconButton>
                        {c.currentTaskId && <Button size="small" color="error" onClick={() => cancel(c.id)}>✕</Button>}
                      </Stack>
                    </TableCell>
                  </TableRow>);
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      <Drawer anchor="right" open={drawer} onClose={() => setDrawer(false)}>
        <Box sx={{ width: 400, p: 3 }}>
          <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Lich su tien trinh</Typography>
            <IconButton onClick={() => setDrawer(false)}><CloseIcon /></IconButton>
          </Stack>
          {history.map((e, i) => (
            <Box key={i} sx={{ pl: 3, borderLeft: '2px solid', borderColor: e.kind === 'ProcessRejected' || e.kind === 'ProcessCancelled' ? 'error.main' : 'primary.main', py: 1, position: 'relative' }}>
              <Box sx={{ position: 'absolute', left: -7, top: 6, width: 12, height: 12, borderRadius: '50%', bgcolor: e.kind === 'ProcessRejected' || e.kind === 'ProcessCancelled' ? 'error.main' : 'primary.main' }} />
              <Typography variant="body2" sx={{ fontWeight: 600 }}>{kindLabels[e.kind] || e.kind}{e.taskName ? `: ${e.taskName}` : ''}</Typography>
              <Typography variant="caption" color="text.secondary">{e.actor || ''}{e.decision ? ` [${e.decision}]` : ''} · {new Date(e.occurredAt).toLocaleTimeString('vi-VN')}</Typography>
            </Box>
          ))}
        </Box>
      </Drawer>
    </Box>
  );
}
