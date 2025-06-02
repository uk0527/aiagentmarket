import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Badge,
  Box,
  Menu,
  MenuItem
} from '@mui/material';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleClose();
    logout();
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography
          variant="h6"
          component={RouterLink}
          to="/"
          sx={{
            flexGrow: 1,
            textDecoration: 'none',
            color: 'inherit'
          }}
        >
          AI Agent Marketplace
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            color="inherit"
            component={RouterLink}
            to="/agents"
          >
            Browse Agents
          </Button>
          
          {isAuthenticated && (
            <IconButton
              color="inherit"
              component={RouterLink}
              to="/cart"
            >
              <Badge badgeContent={2} color="secondary">
                <ShoppingCartIcon />
              </Badge>
            </IconButton>
          )}
          
          {isAuthenticated ? (
            <>
              <IconButton
                color="inherit"
                onClick={handleMenu}
              >
                <AccountCircleIcon />
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem
                  component={RouterLink}
                  to="/profile"
                  onClick={handleClose}
                >
                  Profile
                </MenuItem>
                <MenuItem
                  component={RouterLink}
                  to="/purchases"
                  onClick={handleClose}
                >
                  My Purchases
                </MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button
                color="inherit"
                component={RouterLink}
                to="/login"
              >
                Sign In
              </Button>
              <Button
                color="inherit"
                component={RouterLink}
                to="/signup"
                variant="outlined"
              >
                Sign Up
              </Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation; 