/**
 * Notification bell component
 */

import { useState } from 'react';
import {
  Badge,
  Box,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
  Chip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  NotificationsNone as NotificationsNoneIcon,
} from '@mui/icons-material';

import { formatRelativeTime, getStatusColor } from '@/utils/helpers';
import { Notification } from '@/types/api';

// Mock notifications - in real app, these would come from an API
const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'warning',
    title: 'Patching job failed',
    message: 'Server web-01 patching failed with error: connection timeout',
    read: false,
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
  },
  {
    id: '2',
    type: 'success',
    title: 'Patching completed',
    message: 'Successfully patched 5 servers in production environment',
    read: false,
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
  },
  {
    id: '3',
    type: 'info',
    title: 'Approval required',
    message: '3 servers are pending approval for Q3 patching',
    read: true,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
  },
];

export const NotificationBell = () => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [notifications] = useState<Notification[]>(mockNotifications);

  const unreadCount = notifications.filter(n => !n.read).length;

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <Box>
      <IconButton
        size="large"
        aria-label="notifications"
        aria-controls="notification-menu"
        aria-haspopup="true"
        onClick={handleMenuOpen}
        color="inherit"
      >
        <Badge badgeContent={unreadCount} color="error">
          {unreadCount > 0 ? <NotificationsIcon /> : <NotificationsNoneIcon />}
        </Badge>
      </IconButton>

      <Menu
        id="notification-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            minWidth: 360,
            maxWidth: 400,
            maxHeight: 400,
            '&:before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              top: 0,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: 'background.paper',
              transform: 'translateY(-50%) rotate(45deg)',
              zIndex: 0,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">
            Notifications
            {unreadCount > 0 && (
              <Chip
                label={unreadCount}
                size="small"
                color="error"
                sx={{ ml: 1 }}
              />
            )}
          </Typography>
        </Box>

        <List sx={{ p: 0, maxHeight: 300, overflow: 'auto' }}>
          {notifications.length === 0 ? (
            <ListItem>
              <ListItemText
                primary="No notifications"
                secondary="You're all caught up!"
              />
            </ListItem>
          ) : (
            notifications.map((notification) => (
              <MenuItem
                key={notification.id}
                onClick={handleMenuClose}
                sx={{
                  borderLeft: 4,
                  borderLeftColor: `${getTypeColor(notification.type)}.main`,
                  backgroundColor: notification.read ? 'transparent' : 'action.hover',
                  '&:hover': {
                    backgroundColor: 'action.selected',
                  },
                }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2" noWrap>
                        {notification.title}
                      </Typography>
                      {!notification.read && (
                        <Box
                          sx={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: 'primary.main',
                            flexShrink: 0,
                          }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatRelativeTime(notification.timestamp)}
                      </Typography>
                    </Box>
                  }
                />
              </MenuItem>
            ))
          )}
        </List>

        {notifications.length > 0 && (
          <Box sx={{ p: 1, borderTop: 1, borderColor: 'divider' }}>
            <MenuItem onClick={handleMenuClose}>
              <Typography variant="body2" color="primary" align="center" sx={{ width: '100%' }}>
                View all notifications
              </Typography>
            </MenuItem>
          </Box>
        )}
      </Menu>
    </Box>
  );
};