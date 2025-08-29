import { Box, Button, Card, CardContent, Chip, Grid, List, ListItem, ListItemText, Typography } from '@mui/material';
import axios from 'axios';
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

const WorkoutHistory = () => {
  const { token } = useAuth();
  const [workouts, setWorkouts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWorkouts = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/workouts/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setWorkouts(response.data.workouts);
      } catch (error) {
        console.error('Error fetching workouts:', error);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchWorkouts();
    }
  }, [token]);

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <Box sx={{ py: 4, px: 3, maxWidth: 1200, mx: 'auto' }}>
        <Typography>Loading workout history...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 4, px: 3, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h3" component="h1" gutterBottom>
        Workout History
      </Typography>

      {workouts.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No workouts yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Start your first workout to see your progress here!
            </Typography>
            <Button variant="contained" href="/exercise-tracker">
              Start Workout
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {workouts.map((workout) => (
            <Grid item xs={12} md={6} lg={4} key={workout.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6">
                      {workout.name || 'Workout Session'}
                    </Typography>
                    {!workout.end_time && (
                      <Chip label="Active" color="success" size="small" />
                    )}
                  </Box>

                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {new Date(workout.start_time).toLocaleDateString()} at {' '}
                    {new Date(workout.start_time).toLocaleTimeString()}
                  </Typography>

                  <List dense>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary="Duration"
                        secondary={formatDuration(workout.duration_seconds)}
                      />
                    </ListItem>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary="Exercises"
                        secondary={`${workout.exercise_count} exercises`}
                      />
                    </ListItem>
                    {workout.calories_burned && (
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText
                          primary="Calories"
                          secondary={`${Math.round(workout.calories_burned)} cal`}
                        />
                      </ListItem>
                    )}
                  </List>

                  {workout.notes && (
                    <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
                      {workout.notes}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default WorkoutHistory;
