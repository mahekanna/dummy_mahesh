/**
 * Status chip component
 */

import { Chip, ChipProps } from '@mui/material';
import { getStatusColor } from '@/utils/helpers';

interface StatusChipProps extends Omit<ChipProps, 'color'> {
  status: string;
}

export const StatusChip = ({ status, ...props }: StatusChipProps) => {
  const color = getStatusColor(status);
  
  return (
    <Chip
      label={status}
      size="small"
      color={color as ChipProps['color']}
      variant="outlined"
      {...props}
    />
  );
};