import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Layout = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            FitTrack AI
          </Typography>
          <Button color="inherit" onClick={() => handleNavigation('/dashboard')}>
            Dashboard
          </Button>
          <Button color="inherit" onClick={() => handleNavigation('/exercise-tracker')}>
            Exercise Tracker
          </Button>
          <Button color="inherit" onClick={() => handleNavigation('/workout-history')}>
            History
          </Button>
          <Button color="inherit" onClick={() => handleNavigation('/profile')}>
            Profile
          </Button>
          <Button color="inherit" onClick={handleLogout}>
            Logout ({user?.username || 'User'})
          </Button>
        </Toolbar>
      </AppBar>
      
      <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default' }}>
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;
