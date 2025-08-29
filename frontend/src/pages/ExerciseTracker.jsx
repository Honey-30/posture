import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, Card, Grid, CircularProgress, Paper, 
        Divider, Chip, IconButton, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { styled } from '@mui/material/styles';
import { PlayArrow, Stop, Pause, Save, Info, Error, CheckCircle } from '@mui/icons-material';
import Webcam from 'react-webcam';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../context/AuthContext';
import PoseDetector from '../utils/poseDetector';

// Styled components
const VideoContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  height: '480px',
  borderRadius: theme.shape.borderRadius,
  overflow: 'hidden',
  backgroundColor: '#000',
  boxShadow: theme.shadows[4],
  margin: theme.spacing(2, 0)
}));

const StatsCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(2),
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between'
}));

const FeedbackItem = styled(Box)(({ theme, severity }) => ({
  padding: theme.spacing(1, 2),
  marginBottom: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: 
    severity === 'good' ? theme.palette.success.light :
    severity === 'warning' ? theme.palette.warning.light :
    theme.palette.error.light,
  color: 
    severity === 'good' ? theme.palette.success.contrastText :
    severity === 'warning' ? theme.palette.warning.contrastText :
    theme.palette.error.contrastText,
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1)
}));

const CircularProgressWithLabel = styled(Box)(({ theme }) => ({
  position: 'relative',
  display: 'inline-flex',
  justifyContent: 'center',
  alignItems: 'center'
}));

const ExerciseTracker = () => {
  const { token } = useAuth();
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  const poseDetectorRef = useRef(null);
  const requestRef = useRef();
  
  const [isActive, setIsActive] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [exerciseType, setExerciseType] = useState('auto');
  const [detectedExercise, setDetectedExercise] = useState(null);
  const [repCount, setRepCount] = useState(0);
  const [formScore, setFormScore] = useState(0);
  const [formFeedback, setFormFeedback] = useState([]);
  const [timer, setTimer] = useState(0);
  const [workoutId, setWorkoutId] = useState(null);
  const [cameraLoaded, setCameraLoaded] = useState(false);
  const [exerciseStage, setExerciseStage] = useState('neutral');
  const [prevStage, setPrevStage] = useState('neutral');
  const [jointAngles, setJointAngles] = useState({});
  const [calories, setCalories] = useState(0);

  const timerRef = useRef(null);
  const repCountRef = useRef(0);
  const lastRepTimeRef = useRef(0);
  
  // Initialize pose detector
  useEffect(() => {
    const initPoseDetector = async () => {
      poseDetectorRef.current = new PoseDetector();
      await poseDetectorRef.current.initialize();
    };
    
    initPoseDetector();
    
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Handle workout session
  useEffect(() => {
    const checkForActiveWorkout = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/workouts/active', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data) {
          setWorkoutId(response.data.id);
        }
      } catch (error) {
        console.error('Error checking active workout:', error);
      }
    };
    
    if (token) {
      checkForActiveWorkout();
    }
  }, [token]);

  // Timer logic for plank and calorie counting
  useEffect(() => {
    if (isActive && !isPaused) {
      timerRef.current = setInterval(() => {
        setTimer(prevTimer => {
          const newTimer = prevTimer + 1;
          
          // Calculate calories every second
          if (detectedExercise === 'plank') {
            // Plank burns ~5 calories per minute (0.083 per second)
            setCalories(prev => prev + 0.083);
          }
          
          return newTimer;
        });
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isActive, isPaused, detectedExercise]);

  // Start exercise detection
  const startDetection = async () => {
    if (!poseDetectorRef.current?.isReady) {
      toast.error("Pose detector not ready yet. Please wait a moment.");
      return;
    }
    
    // Start or create workout
    if (!workoutId) {
      try {
        const response = await axios.post(
          'http://localhost:8000/api/workouts/start',
          { name: 'Workout Session' },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setWorkoutId(response.data.id);
      } catch (error) {
        console.error('Error starting workout:', error);
        toast.error("Could not start workout session");
        return;
      }
    }
    
    setIsActive(true);
    setIsPaused(false);
    
    // Reset counters when starting
    setRepCount(0);
    repCountRef.current = 0;
    setCalories(0);
    
    // Start animation loop
    if (!requestRef.current) {
      requestRef.current = requestAnimationFrame(detectPose);
    }
  };

  // Pause detection
  const pauseDetection = () => {
    setIsPaused(true);
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
  };

  // Stop detection and save workout
  const stopDetection = async () => {
    setIsActive(false);
    setIsPaused(false);
    
    if (requestRef.current) {
      cancelAnimationFrame(requestRef.current);
      requestRef.current = undefined;
    }
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    // End workout if one is active
    if (workoutId) {
      try {
        await axios.put(
          `http://localhost:8000/api/workouts/${workoutId}/end`,
          { 
            calories_burned: calories,
            duration_seconds: timer
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        setWorkoutId(null);
        toast.success("Workout saved successfully!");
        
        // Log exercise
        if (detectedExercise && repCount > 0) {
          try {
            await axios.post(
              'http://localhost:8000/api/exercises/log',
              {
                exercise_type: detectedExercise,
                reps: repCount,
                sets: 1,
                duration_seconds: timer,
                form_score: formScore / 100,
                workout_id: workoutId
              },
              { headers: { Authorization: `Bearer ${token}` } }
            );
          } catch (error) {
            console.error('Error logging exercise:', error);
          }
        }
        
      } catch (error) {
        console.error('Error ending workout:', error);
        toast.error("Could not save workout data");
      }
    }
  };

  // Process pose and analyze exercise
  const detectPose = async () => {
    if (webcamRef.current && webcamRef.current.video?.readyState === 4) {
      // Set camera as loaded once we have video
      if (!cameraLoaded) {
        setCameraLoaded(true);
      }
      
      const video = webcamRef.current.video;
      const canvas = canvasRef.current;
      
      // Set canvas size to match video
      const videoWidth = video.videoWidth;
      const videoHeight = video.videoHeight;
      canvas.width = videoWidth;
      canvas.height = videoHeight;
      
      // Detect pose with MoveNet
      const pose = await poseDetectorRef.current.detectPose(video);
      
      // Draw pose on canvas
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      if (pose) {
        // Draw the pose
        poseDetectorRef.current.drawPose(ctx, pose);
        
        // Analyze exercise form using backend API
        try {
          const response = await axios.post(
            'http://localhost:8000/api/exercises/analyze',
            {
              keypoints: JSON.stringify(pose.keypoints),
              exercise_type: exerciseType === 'auto' ? null : exerciseType
            },
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                Authorization: `Bearer ${token}`
              }
            }
          );
          
          const analysis = response.data;
          
          // Update UI with exercise data
          if (analysis.exercise_detected) {
            setDetectedExercise(analysis.exercise_type);
            setFormScore(Math.round(analysis.form_score * 100));
            setFormFeedback(analysis.feedback);
            setJointAngles(analysis.joint_angles);
            
            // Handle rep counting based on exercise stage transitions
            const currentStage = analysis.stage;
            setExerciseStage(currentStage);
            
            // Count a rep when transitioning from down to up
            if (prevStage === 'down' && currentStage === 'up') {
              const newRepCount = repCountRef.current + 1;
              repCountRef.current = newRepCount;
              setRepCount(newRepCount);
              
              // Update calories based on exercise type
              const now = Date.now();
              const timeSinceLastRep = (now - lastRepTimeRef.current) / 1000; // in seconds
              
              const calorieMultiplier = {
                push_up: 0.3,
                squat: 0.32,
                jumping_jack: 0.2
              };
              
              // Add calories for this rep
              if (analysis.exercise_type in calorieMultiplier) {
                setCalories(prev => prev + calorieMultiplier[analysis.exercise_type]);
              }
              
              lastRepTimeRef.current = now;
            }
            
            setPrevStage(currentStage);
          }
        } catch (error) {
          console.error('Error analyzing exercise:', error);
        }
      }
    }
    
    // Continue the animation loop
    if (isActive && !isPaused) {
      requestRef.current = requestAnimationFrame(detectPose);
    }
  };

  // Format time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Box sx={{ py: 4, px: 2, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Exercise Tracker
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <VideoContainer>
            <Webcam
              ref={webcamRef}
              audio={false}
              mirrored
              style={{
                position: "absolute",
                width: "100%",
                height: "100%",
                objectFit: "cover"
              }}
              onUserMedia={() => setCameraLoaded(true)}
            />
            <canvas
              ref={canvasRef}
              style={{
                position: "absolute",
                width: "100%",
                height: "100%",
                objectFit: "cover"
              }}
            />
            
            {!cameraLoaded && (
              <Box sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                flexDirection: 'column'
              }}>
                <CircularProgress color="secondary" sx={{ mb: 2 }} />
                <Typography variant="h6">Loading Camera...</Typography>
                <Typography variant="body2" color="gray" sx={{ mt: 1 }}>
                  Please allow camera access when prompted
                </Typography>
              </Box>
            )}
            
            <Box sx={{
              position: 'absolute',
              top: 10,
              left: 10,
              p: 1,
              borderRadius: 1,
              bgcolor: 'rgba(0,0,0,0.6)',
              color: 'white'
            }}>
              {detectedExercise ? (
                <Chip 
                  label={`${detectedExercise.replace('_', ' ')} (${exerciseStage})`}
                  color="primary"
                />
              ) : (
                <Chip label="No exercise detected" color="default" />
              )}
            </Box>
            
            {detectedExercise === 'plank' && (
              <Box sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                p: 2,
                borderRadius: 2,
                bgcolor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '3rem',
                fontWeight: 'bold'
              }}>
                {formatTime(timer)}
              </Box>
            )}
          </VideoContainer>
          
          <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center' }}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel id="exercise-select-label">Exercise Type</InputLabel>
              <Select
                labelId="exercise-select-label"
                value={exerciseType}
                label="Exercise Type"
                onChange={(e) => setExerciseType(e.target.value)}
                disabled={isActive && !isPaused}
              >
                <MenuItem value="auto">Auto Detect</MenuItem>
                <MenuItem value="push_up">Push-up</MenuItem>
                <MenuItem value="squat">Squat</MenuItem>
                <MenuItem value="plank">Plank</MenuItem>
                <MenuItem value="jumping_jack">Jumping Jack</MenuItem>
              </Select>
            </FormControl>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              {!isActive ? (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<PlayArrow />}
                  onClick={startDetection}
                  size="large"
                >
                  Start Tracking
                </Button>
              ) : isPaused ? (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<PlayArrow />}
                  onClick={() => {
                    setIsPaused(false);
                    requestRef.current = requestAnimationFrame(detectPose);
                  }}
                  size="large"
                >
                  Resume
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<Pause />}
                  onClick={pauseDetection}
                  size="large"
                >
                  Pause
                </Button>
              )}
              
              {isActive && (
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<Stop />}
                  onClick={stopDetection}
                  size="large"
                >
                  End Workout
                </Button>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4} container spacing={2} direction="column">
          <Grid item>
            <StatsCard>
              <Typography variant="h6" gutterBottom>
                Statistics
              </Typography>
              
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Rep Count
                    </Typography>
                    <Typography variant="h3">
                      {repCount}
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Workout Time
                    </Typography>
                    <Typography variant="h5">
                      {formatTime(timer)}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <CircularProgressWithLabel>
                  <CircularProgress
                    