from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc

from database.database import get_db
from database.models import User, PostureLog
from api.auth import get_current_user

router = APIRouter()

class PostureAnalysis(BaseModel):
    posture_score: float
    posture_analysis: Dict[str, Any]
    keypoints: List[Dict[str, float]]

class PostureResponse(BaseModel):
    id: int
    posture_score: float
    posture_analysis: Dict[str, Any]
    alert_triggered: bool
    correction_applied: bool
    timestamp: datetime

class PostureStats(BaseModel):
    avg_score: float
    total_sessions: int
    alerts_triggered: int
    corrections_applied: int
    improvement_rate: float

@router.post("/analyze", response_model=PostureResponse)
async def analyze_posture(
    analysis: PostureAnalysis,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze posture from keypoints and store results"""
    
    # Enhanced posture analysis
    keypoints = analysis.keypoints
    detailed_analysis = analyze_posture_keypoints(keypoints)
    
    # Determine if alert should be triggered (score < 60)
    alert_triggered = analysis.posture_score < 60.0
    
    # Create posture log
    posture_log = PostureLog(
        user_id=current_user.id,
        posture_score=analysis.posture_score,
        posture_analysis={
            **analysis.posture_analysis,
            **detailed_analysis,
            "keypoints_count": len(keypoints),
            "analysis_timestamp": datetime.now().isoformat()
        },
        alert_triggered=alert_triggered
    )
    
    db.add(posture_log)
    db.commit()
    db.refresh(posture_log)
    
    return posture_log

@router.get("/current")
async def get_current_posture_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the most recent posture analysis"""
    
    latest_posture = db.query(PostureLog).filter(
        PostureLog.user_id == current_user.id
    ).order_by(desc(PostureLog.timestamp)).first()
    
    if not latest_posture:
        return {
            "status": "no_data",
            "message": "No posture data available. Start monitoring to see results.",
            "posture_score": 0,
            "needs_correction": False
        }
    
    # Check if data is recent (within last 5 minutes)
    time_diff = datetime.now() - latest_posture.timestamp
    is_recent = time_diff.total_seconds() < 300  # 5 minutes
    
    return {
        "status": "active" if is_recent else "inactive",
        "posture_score": latest_posture.posture_score,
        "needs_correction": latest_posture.posture_score < 60.0,
        "last_updated": latest_posture.timestamp.isoformat(),
        "analysis": latest_posture.posture_analysis,
        "alert_triggered": latest_posture.alert_triggered
    }

@router.get("/daily-stats")
async def get_daily_posture_stats(
    target_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily posture statistics"""
    
    if target_date:
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        date_obj = datetime.now().date()
    
    # Get daily stats
    daily_stats = db.query(
        func.avg(PostureLog.posture_score).label('avg_score'),
        func.count(PostureLog.id).label('total_checks'),
        func.sum(func.cast(PostureLog.alert_triggered, db.Integer)).label('alerts'),
        func.sum(func.cast(PostureLog.correction_applied, db.Integer)).label('corrections')
    ).filter(
        and_(
            PostureLog.user_id == current_user.id,
            func.date(PostureLog.timestamp) == date_obj
        )
    ).first()
    
    return {
        "avg_posture_score": round(daily_stats.avg_score or 0, 1),
        "total_checks": daily_stats.total_checks or 0,
        "alerts_triggered": daily_stats.alerts or 0,
        "corrections_applied": daily_stats.corrections or 0,
        "monitoring_time": calculate_monitoring_time(current_user.id, date_obj, db)
    }

@router.get("/weekly-trend")
async def get_weekly_posture_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly posture trend data"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Get daily averages for the week
    weekly_data = db.query(
        func.date(PostureLog.timestamp).label('date'),
        func.avg(PostureLog.posture_score).label('avg_score'),
        func.count(PostureLog.id).label('checks')
    ).filter(
        and_(
            PostureLog.user_id == current_user.id,
            PostureLog.timestamp >= start_date,
            PostureLog.timestamp <= end_date
        )
    ).group_by(func.date(PostureLog.timestamp)).all()
    
    # Fill in missing days
    trend_data = []
    current_date = start_date.date()
    
    while current_date <= end_date.date():
        day_data = next((d for d in weekly_data if d.date == current_date), None)
        trend_data.append({
            "date": current_date.isoformat(),
            "avg_score": round(day_data.avg_score or 0, 1) if day_data else 0,
            "checks": day_data.checks if day_data else 0
        })
        current_date += timedelta(days=1)
    
    return {"trend_data": trend_data}

@router.post("/{log_id}/correct")
async def mark_correction_applied(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark that user applied posture correction"""
    
    posture_log = db.query(PostureLog).filter(
        and_(
            PostureLog.id == log_id,
            PostureLog.user_id == current_user.id
        )
    ).first()
    
    if not posture_log:
        raise HTTPException(status_code=404, detail="Posture log not found")
    
    posture_log.correction_applied = True
    db.commit()
    
    return {"message": "Correction marked as applied"}

@router.get("/recommendations")
async def get_posture_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized posture improvement recommendations"""
    
    # Get recent posture data (last 24 hours)
    recent_data = db.query(PostureLog).filter(
        and_(
            PostureLog.user_id == current_user.id,
            PostureLog.timestamp >= datetime.now() - timedelta(hours=24)
        )
    ).all()
    
    if not recent_data:
        return {
            "recommendations": [
                "Start posture monitoring to get personalized recommendations",
                "Maintain good posture while working",
                "Take regular breaks every 30 minutes"
            ]
        }
    
    avg_score = sum(log.posture_score for log in recent_data) / len(recent_data)
    
    recommendations = generate_posture_recommendations(avg_score, recent_data)
    
    return {"recommendations": recommendations}

def analyze_posture_keypoints(keypoints):
    """Analyze keypoints to determine posture quality"""
    if not keypoints or len(keypoints) < 17:  # MoveNet has 17 keypoints
        return {"error": "Insufficient keypoints for analysis"}
    
    try:
        # Key points indices for MoveNet
        # 5: left shoulder, 6: right shoulder
        # 11: left hip, 12: right hip
        # 0: nose, 1: left eye, 2: right eye
        
        left_shoulder = keypoints[5] if len(keypoints) > 5 else None
        right_shoulder = keypoints[6] if len(keypoints) > 6 else None
        left_hip = keypoints[11] if len(keypoints) > 11 else None
        right_hip = keypoints[12] if len(keypoints) > 12 else None
        nose = keypoints[0] if len(keypoints) > 0 else None
        
        analysis = {}
        
        # Shoulder alignment
        if left_shoulder and right_shoulder:
            shoulder_diff = abs(left_shoulder['y'] - right_shoulder['y'])
            analysis['shoulder_alignment'] = "good" if shoulder_diff < 0.05 else "poor"
            analysis['shoulder_difference'] = shoulder_diff
        
        # Head position relative to shoulders
        if nose and left_shoulder and right_shoulder:
            avg_shoulder_x = (left_shoulder['x'] + right_shoulder['x']) / 2
            head_offset = abs(nose['x'] - avg_shoulder_x)
            analysis['head_alignment'] = "good" if head_offset < 0.08 else "forward"
            analysis['head_offset'] = head_offset
        
        # Spine alignment
        if left_shoulder and left_hip:
            spine_angle = calculate_spine_angle(left_shoulder, left_hip)
            analysis['spine_alignment'] = "good" if abs(spine_angle) < 15 else "slouched"
            analysis['spine_angle'] = spine_angle
        
        return analysis
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def calculate_spine_angle(shoulder, hip):
    """Calculate the angle of the spine from vertical"""
    import math
    
    dx = shoulder['x'] - hip['x']
    dy = shoulder['y'] - hip['y']
    
    # Calculate angle from vertical (90 degrees is perfect upright)
    angle = math.degrees(math.atan2(dx, dy))
    return abs(angle - 90)  # Return deviation from upright

def calculate_monitoring_time(user_id, date_obj, db):
    """Calculate total monitoring time for a day"""
    logs = db.query(PostureLog).filter(
        and_(
            PostureLog.user_id == user_id,
            func.date(PostureLog.timestamp) == date_obj
        )
    ).order_by(PostureLog.timestamp).all()
    
    if len(logs) < 2:
        return 0
    
    # Calculate time between first and last log
    total_seconds = (logs[-1].timestamp - logs[0].timestamp).total_seconds()
    return round(total_seconds / 60, 1)  # Return minutes

def generate_posture_recommendations(avg_score, recent_data):
    """Generate personalized posture recommendations"""
    recommendations = []
    
    if avg_score < 40:
        recommendations.extend([
            "🚨 Critical: Your posture needs immediate attention",
            "📚 Consider using a standing desk or ergonomic chair",
            "⏰ Set hourly reminders to check your posture",
            "🧘 Practice posture exercises daily"
        ])
    elif avg_score < 60:
        recommendations.extend([
            "⚠️ Your posture could be improved",
            "💺 Adjust your chair height and monitor position",
            "⏱️ Take posture breaks every 30 minutes",
            "💪 Strengthen your core and back muscles"
        ])
    elif avg_score < 80:
        recommendations.extend([
            "✅ Good posture! Keep it up",
            "🔄 Maintain regular posture checks",
            "🏃 Add some movement breaks to your routine"
        ])
    else:
        recommendations.extend([
            "🌟 Excellent posture!",
            "👍 You're doing great, keep maintaining good habits",
            "🎯 Consider helping others with posture tips"
        ])
    
    # Add specific recommendations based on analysis patterns
    poor_alignment_count = sum(1 for log in recent_data 
                             if log.posture_analysis and 
                             log.posture_analysis.get('shoulder_alignment') == 'poor')
    
    if poor_alignment_count > len(recent_data) * 0.5:
        recommendations.append("🤷 Focus on keeping your shoulders level and relaxed")
    
    return recommendations
