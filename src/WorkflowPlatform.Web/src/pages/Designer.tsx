import { useState } from 'react';
import { useDefinitions } from '../hooks/useDefinitions';
import { Card, CardContent, Typography, TextField, Button, Checkbox, FormControlLabel, Box, Chip, Stack } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

interface StepRow { name: string; assignee: string; }
const defaultSteps: StepRow[] = [
  { name: 'Tham dinh', assignee: 'thamdinh' },
  { name: 'Phe duyet', assignee: 'lanhdao' },
];

export default function Designer() {
  const { defs, create } = useDefinitions();
  const [name, setName] = useState('');
  const [steps, setSteps] = useState<StepRow[]>([...defaultSteps]);
  const [decision, setDecision] = useState(true);

  const add = () => setSteps([...steps, { name: '', assignee: '' }]);
  const remove = (i: number) => setSteps(steps.filter((_, j) => j !== i));
  const update = (i: number, f: keyof StepRow, v: string) => {
    const next = [...steps];
    next[i] = { ...next[i], [f]: v };
    setSteps(next);
  };

  const save = async () => {
    const names = steps.map(s => s.name.trim()).filter(Boolean);
    if (!names.length) return alert('Can it nhat mot buoc.');
    await create({ name: name.trim() || 'Quy trinh moi', steps: names, endsWithDecision: decision, assignees: steps.map(s => s.assignee.trim() || null) });
    setName('');
    setSteps([...defaultSteps]);
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>Thiet ke quy trinh</Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField label="Ten quy trinh" fullWidth value={name} onChange={e => setName(e.target.value)} sx={{ mb: 2 }} placeholder="VD: Quy trinh cap phep" />
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Cac buoc</Typography>
          {steps.map((s, i) => (
            <Stack key={i} direction="row" spacing={1} sx={{ mb: 1, alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ width: 24 }}>{i + 1}.</Typography>
              <TextField size="small" placeholder={`Ten buoc ${i + 1}`} value={s.name} onChange={e => update(i, 'name', e.target.value)} sx={{ flex: 3 }} />
              <TextField size="small" placeholder="Nguoi thuc hien" value={s.assignee} onChange={e => update(i, 'assignee', e.target.value)} sx={{ flex: 2 }} />
              <Button size="small" color="error" onClick={() => remove(i)}><DeleteIcon fontSize="small" /></Button>
            </Stack>
          ))}
          <Button startIcon={<AddIcon />} size="small" onClick={add} sx={{ mb: 2 }}>Them buoc</Button>
          <Box>
            <FormControlLabel control={<Checkbox checked={decision} onChange={e => setDecision(e.target.checked)} />} label="Buoc cuoi la quyet dinh (Duyet / Tu choi)" />
          </Box>
          <Button variant="contained" onClick={save} sx={{ mt: 2 }}>Luu & Nap quy trinh</Button>
        </CardContent>
      </Card>

      <Typography variant="h6" sx={{ mb: 2 }}>Quy trinh hien co</Typography>
      {defs.length === 0 && <Typography color="text.secondary">Chua co quy trinh nao.</Typography>}
      {defs.map(d => (
        <Card key={d.key} sx={{ mb: 1.5 }}>
          <CardContent>
            <Typography sx={{ fontWeight: 600 }}>{d.name} <Typography component="span" variant="caption" color="text.secondary">({d.key})</Typography></Typography>
            <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', gap: 0.5 }}>
              {d.steps.map(s => <Chip key={s.id} label={s.name} size="small" variant="outlined" />)}
              {d.endsWithDecision && <Chip label="Duyet/Tu choi" size="small" color="warning" variant="outlined" />}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}
