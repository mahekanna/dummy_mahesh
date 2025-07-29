/**
 * Sidebar navigation component
 */

import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Computer as ComputerIcon,
  Build as BuildIcon,
  CheckCircle as CheckCircleIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  ExpandLess,
  ExpandMore,
  Schedule as ScheduleIcon,
  History as HistoryIcon,
  SystemUpdateAlt as SystemUpdateIcon,
  Approval as ApprovalIcon,
} from '@mui/icons-material';
import { useState } from 'react';

import { useAuth } from '@/hooks/useAuth';
import { ROUTES, PERMISSIONS } from '@/constants';

interface NavItem {
  title: string;
  icon: React.ReactNode;
  path?: string;
  permission?: string;
  children?: NavItem[];
}

const navigationItems: NavItem[] = [
  {
    title: 'Dashboard',
    icon: <DashboardIcon />,
    path: ROUTES.DASHBOARD,
  },
  {
    title: 'Servers',
    icon: <ComputerIcon />,
    path: ROUTES.SERVERS,
    permission: PERMISSIONS.SERVERS_VIEW,
  },
  {
    title: 'Patching',
    icon: <BuildIcon />,
    permission: PERMISSIONS.PATCHING_VIEW,
    children: [
      {
        title: 'Jobs',
        icon: <SystemUpdateIcon />,
        path: `${ROUTES.PATCHING}/jobs`,
      },
      {
        title: 'Schedule',
        icon: <ScheduleIcon />,
        path: `${ROUTES.PATCHING}/schedule`,
      },
      {
        title: 'History',
        icon: <HistoryIcon />,
        path: `${ROUTES.PATCHING}/history`,
      },
    ],
  },
  {
    title: 'Approvals',
    icon: <ApprovalIcon />,
    path: ROUTES.APPROVALS,
    permission: PERMISSIONS.APPROVALS_VIEW,
  },
  {
    title: 'Reports',
    icon: <AssessmentIcon />,
    path: ROUTES.REPORTS,
    permission: PERMISSIONS.REPORTS_VIEW,
  },
  {
    title: 'System',
    icon: <SettingsIcon />,
    permission: PERMISSIONS.SYSTEM_VIEW,
    children: [
      {
        title: 'Health',
        icon: <CheckCircleIcon />,
        path: `${ROUTES.SYSTEM}/health`,
      },
      {
        title: 'Settings',
        icon: <SettingsIcon />,
        path: `${ROUTES.SYSTEM}/settings`,
        permission: PERMISSIONS.SYSTEM_CONFIGURE,
      },
      {
        title: 'Audit Logs',
        icon: <SecurityIcon />,
        path: `${ROUTES.SYSTEM}/audit`,
        permission: PERMISSIONS.AUDIT_VIEW,
      },
    ],
  },
];

export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const [openItems, setOpenItems] = useState<string[]>([]);

  const handleItemClick = (item: NavItem) => {
    if (item.children) {
      const isOpen = openItems.includes(item.title);
      setOpenItems(prev => 
        isOpen 
          ? prev.filter(title => title !== item.title)
          : [...prev, item.title]
      );
    } else if (item.path) {
      navigate(item.path);
    }
  };

  const isItemSelected = (item: NavItem): boolean => {
    if (item.path) {
      return location.pathname === item.path;
    }
    if (item.children) {
      return item.children.some(child => child.path === location.pathname);
    }
    return false;
  };

  const shouldShowItem = (item: NavItem): boolean => {
    if (item.permission && !hasPermission(item.permission)) {
      return false;
    }
    if (item.children) {
      return item.children.some(child => shouldShowItem(child));
    }
    return true;
  };

  const renderNavItem = (item: NavItem, level = 0) => {
    if (!shouldShowItem(item)) {
      return null;
    }

    const isOpen = openItems.includes(item.title);
    const isSelected = isItemSelected(item);
    const hasChildren = item.children && item.children.length > 0;

    return (
      <Box key={item.title}>
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => handleItemClick(item)}
            selected={isSelected}
            sx={{
              pl: 2 + level * 2,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '& .MuiListItemIcon-root': {
                  color: 'primary.contrastText',
                },
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 40,
                color: isSelected ? 'inherit' : 'text.secondary',
              }}
            >
              {item.icon}
            </ListItemIcon>
            <ListItemText 
              primary={item.title}
              sx={{
                '& .MuiListItemText-primary': {
                  fontSize: level > 0 ? '0.875rem' : '1rem',
                },
              }}
            />
            {hasChildren && (
              isOpen ? <ExpandLess /> : <ExpandMore />
            )}
          </ListItemButton>
        </ListItem>

        {hasChildren && (
          <Collapse in={isOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children?.map(child => renderNavItem(child, level + 1))}
            </List>
          </Collapse>
        )}
      </Box>
    );
  };

  return (
    <Box sx={{ overflow: 'auto' }}>
      <List>
        {navigationItems.map(item => renderNavItem(item))}
      </List>
      <Divider />
    </Box>
  );
};