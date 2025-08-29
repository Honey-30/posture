import * as poseDetection from '@tensorflow-models/pose-detection';
import * as tf from '@tensorflow/tfjs';

class PoseDetector {
  constructor() {
    this.detector = null;
    this.modelType = 'lightning'; // 'lightning' is faster, 'thunder' is more accurate
    this.isReady = false;
    this.minConfidence = 0.3;
    this.smoothingFactor = 0.7; // Higher = more smoothing
    this.lastPose = null;
  }

  async initialize() {
    if (this.detector) {
      return true;
    }

    try {
      console.log('Initializing TensorFlow.js...');
      await tf.ready();
      
      // Check for WebGL support
      if (tf.getBackend() !== 'webgl') {
        console.warn('WebGL not available, using CPU. Performance may be limited.');
        await tf.setBackend('cpu');
      }

      console.log(`Initializing MoveNet ${this.modelType} model...`);
      this.detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        {
          modelType: this.modelType,
          enableSmoothing: true,
          minPoseScore: 0.25
        }
      );
      
      console.log('MoveNet model loaded successfully!');
      this.isReady = true;
      localStorage.setItem('model_preloaded', 'true');
      return true;
    } catch (error) {
      console.error('Failed to initialize pose detector:', error);
      this.isReady = false;
      return false;
    }
  }

  async detectPose(imageElement) {
    if (!this.isReady || !this.detector) {
      throw new Error('Pose detector not initialized');
    }

    try {
      // Detect poses
      const poses = await this.detector.estimatePoses(imageElement);
      
      if (poses.length === 0) {
        return null;
      }

      // Get first pose (assuming single person)
      let pose = poses[0];
      
      // Apply smoothing if we have a previous pose
      if (this.lastPose) {
        pose = this.smoothPose(pose, this.lastPose);
      }
      
      // Save current pose for next frame smoothing
      this.lastPose = pose;
      
      return pose;
    } catch (error) {
      console.error('Error detecting pose:', error);
      return null;
    }
  }

  smoothPose(currentPose, previousPose) {
    if (!previousPose || !currentPose || !previousPose.keypoints || !currentPose.keypoints) {
      return currentPose;
    }

    const smoothedKeypoints = currentPose.keypoints.map((keypoint, i) => {
      // Only smooth keypoints above confidence threshold
      if (keypoint.score > this.minConfidence && 
          previousPose.keypoints[i] && 
          previousPose.keypoints[i].score > this.minConfidence) {
        
        return {
          ...keypoint,
          x: (1 - this.smoothingFactor) * keypoint.x + this.smoothingFactor * previousPose.keypoints[i].x,
          y: (1 - this.smoothingFactor) * keypoint.y + this.smoothingFactor * previousPose.keypoints[i].y
        };
      }
      return keypoint;
    });

    return {
      ...currentPose,
      keypoints: smoothedKeypoints
    };
  }

  drawPose(ctx, pose) {
    if (!pose || !pose.keypoints) {
      return;
    }

    // Draw keypoints
    for (const keypoint of pose.keypoints) {
      if (keypoint.score >= this.minConfidence) {
        const { x, y } = keypoint;
        
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#4CAF50';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }

    // Draw connections
    const connections = [
      // Face
      ['nose', 'left_eye'], ['nose', 'right_eye'],
      ['left_eye', 'left_ear'], ['right_eye', 'right_ear'],
      
      // Torso
      ['left_shoulder', 'right_shoulder'],
      ['left_shoulder', 'left_hip'],
      ['right_shoulder', 'right_hip'],
      ['left_hip', 'right_hip'],
      
      // Arms
      ['left_shoulder', 'left_elbow'],
      ['left_elbow', 'left_wrist'],
      ['right_shoulder', 'right_elbow'],
      ['right_elbow', 'right_wrist'],
      
      // Legs
      ['left_hip', 'left_knee'],
      ['left_knee', 'left_ankle'],
      ['right_hip', 'right_knee'],
      ['right_knee', 'right_ankle']
    ];
    
    const keypointMap = {
      'nose': 0,
      'left_eye': 1,
      'right_eye': 2,
      'left_ear': 3,
      'right_ear': 4,
      'left_shoulder': 5,
      'right_shoulder': 6,
      'left_elbow': 7,
      'right_elbow': 8,
      'left_wrist': 9,
      'right_wrist': 10,
      'left_hip': 11,
      'right_hip': 12,
      'left_knee': 13,
      'right_knee': 14,
      'left_ankle': 15,
      'right_ankle': 16
    };

    ctx.lineWidth = 4;
    
    for (const [p1Name, p2Name] of connections) {
      const keypoint1 = pose.keypoints[keypointMap[p1Name]];
      const keypoint2 = pose.keypoints[keypointMap[p2Name]];

      if (keypoint1 && keypoint2 && 
          keypoint1.score >= this.minConfidence && 
          keypoint2.score >= this.minConfidence) {
          
        ctx.beginPath();
        ctx.moveTo(keypoint1.x, keypoint1.y);
        ctx.lineTo(keypoint2.x, keypoint2.y);
        ctx.strokeStyle = '#3f51b5';
        ctx.stroke();
      }
    }
  }
}

export default PoseDetector;