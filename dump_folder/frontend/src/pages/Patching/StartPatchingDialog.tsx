/**
 * Start patching dialog component
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  Box,
  Chip,
  Alert,
  Autocomplete,
  Stack,
  Divider,
} from '@mui/material';
import { toast } from 'react-hot-toast';

import { apiService } from '@/services/api';
import { QUARTERS } from '@/constants';
import { Server, PatchingJob } from '@/types/api';

interface StartPatchingDialogProps {
  open: boolean;
  onClose: () => void;
  preselectedServers?: string[];
}

export const StartPatchingDialog = ({ 
  open, 
  onClose, 
  preselectedServers = [] 
}: StartPatchingDialogProps) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    servers: preselectedServers,
    quarter: '',
    dryRun: false,
    force: false,
    skipPrecheck: false,
    skipPostcheck: false,
  });

  // Fetch servers for selection
  const { data: serversData } = useQuery({
    queryKey: ['servers-for-patching'],
    queryFn: () => apiService.getServers({ pageSize: 1000 }),
    enabled: open,
  });

  // Start patching mutation
  const startPatchingMutation = useMutation({
    mutationFn: (config: any) => apiService.startPatching(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patching-jobs'] });
      toast.success('Patching job started successfully');
      onClose();
      resetForm();
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to start patching job');
    },
  });

  const servers = serversData?.data.items || [];

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      servers: preselectedServers,
      quarter: '',
      dryRun: false,
      force: false,
      skipPrecheck: false,
      skipPostcheck: false,
    });
  };

  const handleSubmit = () => {
    if (!formData.name || formData.servers.length === 0) {
      toast.error('Please provide a job name and select at least one server');
      return;
    }

    startPatchingMutation.mutate({
      ...formData,
      servers: formData.servers,
    });
  };

  const handleClose = () => {
    onClose();
    resetForm();
  };

  const selectedServers = servers.filter(server => formData.servers.includes(server.id));

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Start Patching Job</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          {/* Job Details */}
          <Typography variant="h6" gutterBottom>
            Job Details
          </Typography>
          
          <TextField
            label="Job Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            fullWidth
            required
          />

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            fullWidth
            multiline
            rows={2}
          />

          <FormControl fullWidth>
            <InputLabel>Quarter</InputLabel>
            <Select
              value={formData.quarter}
              onChange={(e) => setFormData(prev => ({ ...prev, quarter: e.target.value }))}
            >
              {QUARTERS.map(quarter => (
                <MenuItem key={quarter.value} value={quarter.value}>
                  {quarter.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Divider />

          {/* Server Selection */}
          <Typography variant="h6" gutterBottom>
            Server Selection
          </Typography>

          <Autocomplete
            multiple
            options={servers}
            getOptionLabel={(server: Server) => server.serverName}
            value={selectedServers}
            onChange={(_, newValue) => {
              setFormData(prev => ({
                ...prev,
                servers: newValue.map(server => server.id),
              }));
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Select Servers"
                placeholder="Choose servers to patch"
              />
            )}
            renderTags={(value, getTagProps) =>
              value.map((server, index) => (
                <Chip
                  label={server.serverName}
                  {...getTagProps({ index })}
                  key={server.id}
                  size="small"
                />
              ))
            }
          />

          {formData.servers.length > 0 && (
            <Alert severity="info">
              Selected {formData.servers.length} server(s) for patching
            </Alert>
          )}

          <Divider />

          {/* Patching Options */}
          <Typography variant="h6" gutterBottom>
            Patching Options
          </Typography>

          <Stack spacing={1}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.dryRun}
                  onChange={(e) => setFormData(prev => ({ ...prev, dryRun: e.target.checked }))}
                />
              }
              label="Dry Run (Preview changes without applying)"
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.force}
                  onChange={(e) => setFormData(prev => ({ ...prev, force: e.target.checked }))}
                />
              }
              label="Force patching (Skip approval requirements)"
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.skipPrecheck}
                  onChange={(e) => setFormData(prev => ({ ...prev, skipPrecheck: e.target.checked }))}
                />
              }
              label="Skip pre-checks"
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.skipPostcheck}
                  onChange={(e) => setFormData(prev => ({ ...prev, skipPostcheck: e.target.checked }))}
                />
              }
              label="Skip post-checks"
            />
          </Stack>

          {(formData.force || formData.skipPrecheck || formData.skipPostcheck) && (
            <Alert severity="warning">
              Warning: Skipping safety checks may result in system instability. 
              Only use these options if you understand the risks.
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={startPatchingMutation.isPending || !formData.name || formData.servers.length === 0}
        >
          {startPatchingMutation.isPending ? 'Starting...' : 'Start Patching'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};