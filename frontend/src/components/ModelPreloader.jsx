import React, { useEffect, useState } from 'react';
import { Box, Typography, LinearProgress, Paper, Modal } from '@mui/material';
import * as tf from '@tensorflow/tfjs';
import * as poseDetection from '@tensorflow-models/pose-detection';

const ModelPreloader = ({ onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Initializing...');

  useEffect(() => {
    const loadModels = async () => {
      try {
        // Step 1: Initialize TensorFlow.js
        setStatus('Loading TensorFlow.js...');
        setProgress(10);
        await tf.ready();
        setProgress(20);
        
        // Step 2: Check backend
        const backend = tf.getBackend();
        setStatus(`Using ${backend} backend. Loading MoveNet...`);
        setProgress(30);
        
        // Step 3: Load lightning model (faster)
        const detectorConfig = {
          modelType: 'lightning',
          enableSmoothing: true
        };
        
        setStatus('Loading MoveNet lightning model...');
        const detector = await poseDetection.createDetector(
          poseDetection.SupportedModels.MoveNet,
          detectorConfig
        );
        setProgress(70);
        
        // Step 4: Load thunder model (optional, more accurate)
        try {
          setStatus('Loading MoveNet thunder model (for accuracy)...');
          const thunderDetectorConfig = {
            modelType: 'thunder',
            enableSmoothing: true
          };
          
          await poseDetection.createDetector(
            poseDetection.SupportedModels.MoveNet,
            thunderDetectorConfig
          );
          setProgress(90);
        } catch (error) {
          console.warn("Could not load thunder model:", error);
          // Continue without the thunder model
          setProgress(85);
        }
        
        // Step 5: Complete
        setStatus('Models loaded successfully!');
        setProgress(100);
        
        // Mark as preloaded
        localStorage.setItem('model_preloaded', 'true');
        
        // Wait a moment to show success message
        setTimeout(() => {
          onComplete();
        }, 1000);
        
      } catch (error) {
        console.error("Error preloading models:", error);
        setStatus(`Error loading models: ${error.message}`);
        
        // Try to continue anyway after a delay
        setTimeout(() => {
          onComplete();
        }, 3000);
      }
    };

    loadModels();
  }, [onComplete]);

  return (
    <Modal open={true} aria-labelledby="model-preloader-title">
      <Paper
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: { xs: '90%', sm: 400 },
          p: 4,
          borderRadius: 2,
          boxShadow: 24
        }}
      >
        <Typography id="model-preloader-title" variant="h5" component="h2" gutterBottom>
          Loading FitTrackAI
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          This will only happen once. Please wait while we prepare the AI models...
        </Typography>
        
        <LinearProgress variant="determinate" value={progress} sx={{ mb: 2, height: 10, borderRadius: 5 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            {status}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {`${Math.round(progress)}%`}
          </Typography>
        </Box>
      </Paper>
    </Modal>
  );
};

export default ModelPreloader;