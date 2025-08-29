import numpy as np
import math
from typing import Dict, List, Optional, Any, Union, Tuple

class PoseAnalyzer:
    """
    Analyzes pose keypoints from MoveNet to provide exercise form feedback.
    This service processes the pose data and provides detailed form analysis
    for different types of exercises.
    """
    
    def __init__(self):
        self.exercise_types = {
            "push_up": self._analyze_push_up,
            "squat": self._analyze_squat,
            "plank": self._analyze_plank,
            "jumping_jack": self._analyze_jumping_jack
        }
        
        # Joint indices for MoveNet model
        self.joint_indices = {
            "nose": 0,
            "left_eye": 1,
            "right_eye": 2,
            "left_ear": 3,
            "right_ear": 4,
            "left_shoulder": 5,
            "right_shoulder": 6,
            "left_elbow": 7,
            "right_elbow": 8,
            "left_wrist": 9,
            "right_wrist": 10,
            "left_hip": 11,
            "right_hip": 12,
            "left_knee": 13,
            "right_knee": 14,
            "left_ankle": 15,
            "right_ankle": 16,
        }

    def analyze_exercise(self, keypoints: List[Dict], exercise_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze pose keypoints and provide form feedback for a specific exercise.
        
        Args:
            keypoints: List of keypoints from MoveNet model
            exercise_type: Type of exercise to analyze. If None, will attempt to detect.
            
        Returns:
            Dictionary containing analysis results
        """
        # Calculate joint angles
        angles = self._calculate_joint_angles(keypoints)
        
        # Detect exercise type if not provided
        detected_type = exercise_type
        if not detected_type:
            detected_type = self._detect_exercise_type(keypoints, angles)
        
        # Default response
        response = {
            "exercise_detected": detected_type is not None,
            "exercise_type": detected_type or "unknown",
            "form_score": 0.0,
            "feedback": ["No valid exercise detected"],
            "joint_angles": angles
        }
        
        # Check if we have a valid exercise type to analyze
        if detected_type in self.exercise_types:
            # Call the appropriate analysis function
            form_score, feedback = self.exercise_types[detected_type](keypoints, angles)
            
            response["form_score"] = form_score
            response["feedback"] = feedback
            
            # Determine exercise stage (up/down)
            response["stage"] = self._detect_exercise_stage(detected_type, angles)
        
        return response

    def _calculate_joint_angles(self, keypoints: List[Dict]) -> Dict[str, float]:
        """
        Calculate angles between joints.
        
        Args:
            keypoints: List of keypoints from MoveNet model
            
        Returns:
            Dictionary of joint angles in degrees
        """
        angles = {}
        
        # Ensure we have valid keypoints
        if not keypoints or len(keypoints) < 17:
            return angles
        
        # Calculate elbow angles
        angles["left_elbow"] = self._calculate_angle(
            self._get_point(keypoints, "left_shoulder"),
            self._get_point(keypoints, "left_elbow"),
            self._get_point(keypoints, "left_wrist")
        )
        
        angles["right_elbow"] = self._calculate_angle(
            self._get_point(keypoints, "right_shoulder"),
            self._get_point(keypoints, "right_elbow"),
            self._get_point(keypoints, "right_wrist")
        )
        
        # Calculate shoulder angles
        angles["left_shoulder"] = self._calculate_angle(
            self._get_point(keypoints, "left_elbow"),
            self._get_point(keypoints, "left_shoulder"),
            self._get_point(keypoints, "left_hip")
        )
        
        angles["right_shoulder"] = self._calculate_angle(
            self._get_point(keypoints, "right_elbow"),
            self._get_point(keypoints, "right_shoulder"),
            self._get_point(keypoints, "right_hip")
        )
        
        # Calculate hip angles
        angles["left_hip"] = self._calculate_angle(
            self._get_point(keypoints, "left_shoulder"),
            self._get_point(keypoints, "left_hip"),
            self._get_point(keypoints, "left_knee")
        )
        
        angles["right_hip"] = self._calculate_angle(
            self._get_point(keypoints, "right_shoulder"),
            self._get_point(keypoints, "right_hip"),
            self._get_point(keypoints, "right_knee")
        )
        
        # Calculate knee angles
        angles["left_knee"] = self._calculate_angle(
            self._get_point(keypoints, "left_hip"),
            self._get_point(keypoints, "left_knee"),
            self._get_point(keypoints, "left_ankle")
        )
        
        angles["right_knee"] = self._calculate_angle(
            self._get_point(keypoints, "right_hip"),
            self._get_point(keypoints, "right_knee"),
            self._get_point(keypoints, "right_ankle")
        )
        
        # Calculate torso angle (vertical alignment)
        left_shoulder = self._get_point(keypoints, "left_shoulder")
        left_hip = self._get_point(keypoints, "left_hip")
        if left_shoulder and left_hip:
            # Create a point directly above the hip
            vertical_point = {"x": left_hip["x"], "y": left_hip["y"] - 100, "score": 1.0}
            angles["torso_vertical"] = self._calculate_angle(
                vertical_point, left_hip, left_shoulder
            )
        
        return angles

    def _calculate_angle(
        self, 
        point1: Optional[Dict], 
        point2: Optional[Dict], 
        point3: Optional[Dict]
    ) -> Optional[float]:
        """
        Calculate the angle between three points.
        Point2 is the vertex.
        
        Args:
            point1, point2, point3: Points with x, y coordinates
            
        Returns:
            Angle in degrees or None if points are invalid
        """
        # Check if all points are valid
        if not point1 or not point2 or not point3:
            return None
        
        # Check confidence scores if available
        min_confidence = 0.2  # Minimum confidence threshold
        if ("score" in point1 and point1["score"] < min_confidence) or \
           ("score" in point2 and point2["score"] < min_confidence) or \
           ("score" in point3 and point3["score"] < min_confidence):
            return None
        
        # Calculate vectors
        vector1 = [point1["x"] - point2["x"], point1["y"] - point2["y"]]
        vector2 = [point3["x"] - point2["x"], point3["y"] - point2["y"]]
        
        # Calculate dot product
        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
        magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)
        
        # Avoid division by zero
        if magnitude1 * magnitude2 == 0:
            return None
        
        # Calculate angle
        cosine = dot_product / (magnitude1 * magnitude2)
        cosine = max(-1, min(1, cosine))  # Ensure cosine is between -1 and 1
        angle_radians = math.acos(cosine)
        angle_degrees = math.degrees(angle_radians)
        
        return angle_degrees

    def _get_point(self, keypoints: List[Dict], joint_name: str) -> Optional[Dict]:
        """Get the point for a specific joint name."""
        if joint_name not in self.joint_indices:
            return None
            
        index = self.joint_indices[joint_name]
        if index >= len(keypoints):
            return None
            
        keypoint = keypoints[index]
        
        # Ensure the keypoint has required fields
        if "x" not in keypoint or "y" not in keypoint:
            return None
            
        return keypoint

    def _detect_exercise_type(self, keypoints: List[Dict], angles: Dict[str, float]) -> Optional[str]:
        """
        Detect the type of exercise based on pose keypoints and angles.
        
        Args:
            keypoints: List of keypoints from MoveNet model
            angles: Dictionary of joint angles
            
        Returns:
            Exercise type or None if cannot determine
        """
        # Get key body points
        left_shoulder = self._get_point(keypoints, "left_shoulder")
        right_shoulder = self._get_point(keypoints, "right_shoulder")
        left_hip = self._get_point(keypoints, "left_hip")
        right_hip = self._get_point(keypoints, "right_hip")
        left_knee = self._get_point(keypoints, "left_knee")
        right_knee = self._get_point(keypoints, "right_knee")
        
        # Check if we have enough keypoints for reliable detection
        if not all([left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        # Calculate body position metrics
        shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
        hip_y = (left_hip["y"] + right_hip["y"]) / 2
        
        # Vertical distance between shoulders and hips
        torso_vertical_dist = abs(shoulder_y - hip_y)
        
        # Horizontal distance between shoulders and hips
        shoulder_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
        hip_x = (left_hip["x"] + right_hip["x"]) / 2
        torso_horizontal_dist = abs(shoulder_x - hip_x)
        
        # Check if body is horizontal (push-up or plank)
        if torso_vertical_dist < 30:  # Small vertical difference indicates horizontal position
            # Differentiate between push-up and plank based on elbow angle
            left_elbow = angles.get("left_elbow")
            right_elbow = angles.get("right_elbow")
            
            if left_elbow and right_elbow:
                avg_elbow_angle = (left_elbow + right_elbow) / 2
                if avg_elbow_angle < 120:
                    return "push_up"  # Bent elbows suggest push-up
                else:
                    return "plank"    # Straight arms suggest plank
        
        # Check for squat (bent knees, vertical torso)
        if left_knee and right_knee:
            left_knee_angle = angles.get("left_knee")
            right_knee_angle = angles.get("right_knee")
            
            if left_knee_angle and right_knee_angle:
                avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
                if avg_knee_angle < 160:  # Bent knees
                    return "squat"
        
        # Check for jumping jack (wide arms)
        shoulder_width = abs(left_shoulder["x"] - right_shoulder["x"])
        hip_width = abs(left_hip["x"] - right_hip["x"])
        
        if shoulder_width > hip_width * 1.5:  # Arms spread wider than hips
            return "jumping_jack"
        
        return None

    def _detect_exercise_stage(self, exercise_type: str, angles: Dict[str, float]) -> str:
        """
        Detect if an exercise is in the 'up' or 'down' position.
        
        Args:
            exercise_type: Type of exercise
            angles: Dictionary of joint angles
            
        Returns:
            'up', 'down', or 'neutral'
        """
        if exercise_type == "push_up":
            left_elbow = angles.get("left_elbow", 180)
            right_elbow = angles.get("right_elbow", 180)
            avg_elbow_angle = (left_elbow + right_elbow) / 2 if left_elbow and right_elbow else 180
            
            if avg_elbow_angle < 100:
                return "down"
            elif avg_elbow_angle > 160:
                return "up"
                
        elif exercise_type == "squat":
            left_knee = angles.get("left_knee", 180)
            right_knee = angles.get("right_knee", 180)
            avg_knee_angle = (left_knee + right_knee) / 2 if left_knee and right_knee else 180
            
            if avg_knee_angle < 120:
                return "down"
            elif avg_knee_angle > 160:
                return "up"
                
        elif exercise_type == "jumping_jack":
            # For jumping jacks, 'up' means arms raised and legs spread
            # 'down' means arms down and legs together
            # This would require more complex logic checking arm and leg positions
            # Simplified version here
            left_shoulder = angles.get("left_shoulder", 0)
            right_shoulder = angles.get("right_shoulder", 0)
            
            if left_shoulder and right_shoulder:
                avg_shoulder_angle = (left_shoulder + right_shoulder) / 2
                if avg_shoulder_angle > 80:  # Arms raised
                    return "up"
                elif avg_shoulder_angle < 30:  # Arms down
                    return "down"
        
        return "neutral"

    def _analyze_push_up(self, keypoints: List[Dict], angles: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Analyze push-up form and provide feedback.
        
        Args:
            keypoints: List of keypoints
            angles: Dictionary of joint angles
            
        Returns:
            Tuple of (form_score, feedback_list)
        """
        feedback = []
        score = 1.0
        
        # Get key body points
        left_shoulder = self._get_point(keypoints, "left_shoulder")
        right_shoulder = self._get_point(keypoints, "right_shoulder")
        left_hip = self._get_point(keypoints, "left_hip")
        right_hip = self._get_point(keypoints, "right_hip")
        left_ankle = self._get_point(keypoints, "left_ankle")
        right_ankle = self._get_point(keypoints, "right_ankle")
        
        # Check back alignment (hips should be in line with shoulders)
        if left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
            hip_y = (left_hip["y"] + right_hip["y"]) / 2
            
            if abs(shoulder_y - hip_y) > 30:  # Hips not aligned with shoulders
                if hip_y < shoulder_y - 20:
                    feedback.append("Lower your hips - maintain a straight line from head to heels")
                    score -= 0.25
                elif hip_y > shoulder_y + 20:
                    feedback.append("Raise your hips - avoid sagging in the middle")
                    score -= 0.25
        
        # Check elbow angle
        left_elbow = angles.get("left_elbow")
        right_elbow = angles.get("right_elbow")
        
        if left_elbow and right_elbow:
            avg_elbow_angle = (left_elbow + right_elbow) / 2
            
            stage = self._detect_exercise_stage("push_up", angles)
            if stage == "down":
                # In down position, check if elbow angle is appropriate
                if avg_elbow_angle < 70:
                    feedback.append("You're going too deep - aim for 90° at the elbow")
                    score -= 0.15
                elif avg_elbow_angle > 110:
                    feedback.append("Go lower - aim for 90° at the elbow")
                    score -= 0.2
            elif stage == "up":
                # In up position, check if arms are extended
                if avg_elbow_angle < 160:
                    feedback.append("Fully extend your arms at the top of the push-up")
                    score -= 0.15
        
        # Check if legs are straight and together
        if left_ankle and right_ankle:
            ankle_dist = math.sqrt((left_ankle["x"] - right_ankle["x"])**2 + 
                                  (left_ankle["y"] - right_ankle["y"])**2)
            
            if ankle_dist > 50:  # Ankles too far apart
                feedback.append("Keep your legs together for better stability")
                score -= 0.1
        
        # Add positive feedback if form is good
        if not feedback:
            feedback.append("Great push-up form! Maintain a straight body line.")
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score, feedback

    def _analyze_squat(self, keypoints: List[Dict], angles: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Analyze squat form and provide feedback.
        
        Args:
            keypoints: List of keypoints
            angles: Dictionary of joint angles
            
        Returns:
            Tuple of (form_score, feedback_list)
        """
        feedback = []
        score = 1.0
        
        # Get key body points
        left_hip = self._get_point(keypoints, "left_hip")
        right_hip = self._get_point(keypoints, "right_hip")
        left_knee = self._get_point(keypoints, "left_knee")
        right_knee = self._get_point(keypoints, "right_knee")
        left_ankle = self._get_point(keypoints, "left_ankle")
        right_ankle = self._get_point(keypoints, "right_ankle")
        left_shoulder = self._get_point(keypoints, "left_shoulder")
        right_shoulder = self._get_point(keypoints, "right_shoulder")
        
        # Check knee angles for depth
        left_knee_angle = angles.get("left_knee")
        right_knee_angle = angles.get("right_knee")
        
        if left_knee_angle and right_knee_angle:
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
            
            stage = self._detect_exercise_stage("squat", angles)
            if stage == "down":
                # In down position, check if squat is deep enough
                if avg_knee_angle > 140:
                    feedback.append("Squat deeper - aim for thighs parallel to the ground")
                    score -= 0.25
                elif avg_knee_angle < 70:
                    feedback.append("You're squatting too deep - be careful with your knees")
                    score -= 0.15
        
        # Check knee position (should not extend past toes)
        if left_knee and left_ankle and right_knee and right_ankle:
            left_knee_past_toes = left_knee["x"] > left_ankle["x"] + 30
            right_knee_past_toes = right_knee["x"] > right_ankle["x"] + 30
            
            if left_knee_past_toes or right_knee_past_toes:
                feedback.append("Keep your knees behind your toes")
                score -= 0.2
        
        # Check back angle
        torso_vertical = angles.get("torso_vertical")
        if torso_vertical:
            if torso_vertical > 45:  # Back is leaning too far forward
                feedback.append("Keep your chest up and back more upright")
                score -= 0.15
        
        # Check foot stance
        if left_ankle and right_ankle:
            ankle_dist = abs(left_ankle["x"] - right_ankle["x"])
            hip_width = abs(left_hip["x"] - right_hip["x"]) if left_hip and right_hip else 100
            
            if ankle_dist < hip_width * 0.8:  # Feet too close together
                feedback.append("Widen your stance to shoulder width or slightly wider")
                score -= 0.1
            elif ankle_dist > hip_width * 1.8:  # Feet too far apart
                feedback.append("Narrow your stance slightly")
                score -= 0.1
        
        # Check if knees are aligned with feet (not caving in)
        if left_knee and right_knee and left_hip and right_hip:
            knee_width = abs(left_knee["x"] - right_knee["x"])
            hip_width = abs(left_hip["x"] - right_hip["x"])
            
            if knee_width < hip_width * 0.6:  # Knees caving in
                feedback.append("Keep your knees in line with your toes - don't let them cave inward")
                score -= 0.15
        
        # Add positive feedback if form is good
        if not feedback:
            feedback.append("Excellent squat form! Keep your weight in your heels.")
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score, feedback

    def _analyze_plank(self, keypoints: List[Dict], angles: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Analyze plank form and provide feedback.
        
        Args:
            keypoints: List of keypoints
            angles: Dictionary of joint angles
            
        Returns:
            Tuple of (form_score, feedback_list)
        """
        feedback = []
        score = 1.0
        
        # Get key body points
        left_shoulder = self._get_point(keypoints, "left_shoulder")
        right_shoulder = self._get_point(keypoints, "right_shoulder")
        left_hip = self._get_point(keypoints, "left_hip")
        right_hip = self._get_point(keypoints, "right_hip")
        left_ankle = self._get_point(keypoints, "left_ankle")
        right_ankle = self._get_point(keypoints, "right_ankle")
        left_elbow = self._get_point(keypoints, "left_elbow")
        right_elbow = self._get_point(keypoints, "right_elbow")
        
        # Check if body is in a straight line
        if left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
            hip_y = (left_hip["y"] + right_hip["y"]) / 2
            
            if abs(shoulder_y - hip_y) > 30:  # Body not straight
                if hip_y < shoulder_y - 20:
                    feedback.append("Lower your hips - your body should form a straight line")
                    score -= 0.25
                elif hip_y > shoulder_y + 20:
                    feedback.append("Raise your hips - don't let them sag toward the ground")
                    score -= 0.25
        
        # Check if ankles are in line with body
        if left_ankle and right_ankle and left_hip and right_hip:
            ankle_y = (left_ankle["y"] + right_ankle["y"]) / 2
            hip_y = (left_hip["y"] + right_hip["y"]) / 2
            
            if abs(ankle_y - hip_y) > 30:  # Ankles not in line
                feedback.append("Keep your legs straight and in line with your body")
                score -= 0.15
        
        # Check elbow position
        if left_elbow and right_elbow and left_shoulder and right_shoulder:
            left_dist = math.sqrt((left_elbow["x"] - left_shoulder["x"])**2 + 
                                 (left_elbow["y"] - left_shoulder["y"])**2)
            right_dist = math.sqrt((right_elbow["x"] - right_shoulder["x"])**2 + 
                                  (right_elbow["y"] - right_shoulder["y"])**2)
            
            if left_dist > 40 or right_dist > 40:  # Elbows too far from shoulders
                feedback.append("Position your elbows directly under your shoulders")
                score -= 0.15
        
        # Add positive feedback if form is good
        if not feedback:
            feedback.append("Great plank form! Keep your core engaged and breathe steadily.")
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score, feedback
        
    def _analyze_jumping_jack(self, keypoints: List[Dict], angles: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Analyze jumping jack form and provide feedback.
        
        Args:
            keypoints: List of keypoints
            angles: Dictionary of joint angles
            
        Returns:
            Tuple of (form_score, feedback_list)
        """
        feedback = []
        score = 1.0
        
        # Get key body points
        left_shoulder = self._get_point(keypoints, "left_shoulder")
        right_shoulder = self._get_point(keypoints, "right_shoulder")
        left_hip = self._get_point(keypoints, "left_hip")
        right_hip = self._get_point(keypoints, "right_hip")
        left_ankle = self._get_point(keypoints, "left_ankle")
        right_ankle = self._get_point(keypoints, "right_ankle")
        left_wrist = self._get_point(keypoints, "left_wrist")
        right_wrist = self._get_point(keypoints, "right_wrist")
        
        if not all([left_shoulder, right_shoulder, left_hip, right_hip, 
                    left_ankle, right_ankle, left_wrist, right_wrist]):
            return 0.5, ["Cannot fully analyze jumping jack - not all key points detected"]
        
        # Detect stage
        stage = self._detect_exercise_stage("jumping_jack", angles)
        
        # Analyze "up" position (arms up, legs apart)
        if stage == "up":
            # Check if arms are raised high enough
            left_arm_raised = left_wrist["y"] < left_shoulder["y"]
            right_arm_raised = right_wrist["y"] < right_shoulder["y"]
            
            if not (left_arm_raised and right_arm_raised):
                feedback.append("Raise your arms fully above your head")
                score -= 0.2
            
            # Check if legs are spread wide enough
            ankle_distance = abs(left_ankle["x"] - right_ankle["x"])
            hip_distance = abs(left_hip["x"] - right_hip["x"])
            
            if ankle_distance < hip_distance:
                feedback.append("Jump wider with your feet")
                score -= 0.15
        
        # Analyze "down" position (arms down, legs together)
        elif stage == "down":
            # Check if arms are by sides
            left_arm_down = left_wrist["y"] > left_hip["y"]
            right_arm_down = right_wrist["y"] > right_hip["y"]
            
            if not (left_arm_down and right_arm_down):
                feedback.append("Bring your arms fully down by your sides")
                score -= 0.15
            
            # Check if feet are together
            ankle_distance = abs(left_ankle["x"] - right_ankle["x"])
            
            if ankle_distance > 30:
                feedback.append("Bring your feet together between jumps")
                score -= 0.15
        
        # Check overall posture
        shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
        hip_y = (left_hip["y"] + right_hip["y"]) / 2
        
        if abs(left_hip["y"] - right_hip["y"]) > 20:
            feedback.append("Keep your hips level during the exercise")
            score -= 0.1
        
        # Add positive feedback if form is good
        if not feedback:
            if stage == "up":
                feedback.append("Great form! Full extension of arms and legs.")
            else:
                feedback.append("Good control on the landing! Maintain rhythm.")
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score, feedback