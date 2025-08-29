from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import func

from database.database import get_db
from database.models import User, Workout, ExerciseLog
from api.auth import get_current_user

router = APIRouter()

class WorkoutCreate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None

class WorkoutUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    calories_burned: Optional[float] = None

class WorkoutResponse(BaseModel):
    id: int
    name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    calories_burned: Optional[float] = None
    exercise_count: int = 0
    notes: Optional[str] = None

class WorkoutListResponse(BaseModel):
    workouts: List[WorkoutResponse]
    total: int

@router.post("/start", response_model=WorkoutResponse)
async def start_workout(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new workout session"""
    # Check if user has an active workout
    active_workout = db.query(Workout).filter(
        Workout.user_id == current_user.id,
        Workout.end_time == None
    ).first()
    
    if active_workout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active workout session"
        )
    
    # Create new workout
    new_workout = Workout(
        user_id=current_user.id,
        name=workout.name,
        notes=workout.notes
    )
    
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    
    # Initialize with zero exercises
    setattr(new_workout, "exercise_count", 0)
    
    return new_workout

@router.put("/{workout_id}/end", response_model=WorkoutResponse)
async def end_workout(
    workout_id: int,
    workout_update: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End an active workout session"""
    # Get workout
    workout = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == current_user.id
    ).first()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    
    if workout.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This workout session is already completed"
        )
    
    # Update workout
    if workout_update.name:
        workout.name = workout_update.name
    
    if workout_update.notes:
        workout.notes = workout_update.notes
    
    # Set end time if provided, otherwise use current time
    workout.end_time = workout_update.end_time or datetime.now()
    
    # Calculate duration if not provided
    if workout_update.duration_seconds:
        workout.duration_seconds = workout_update.duration_seconds
    else:
        workout.duration_seconds = int((workout.end_time - workout.start_time).total_seconds())
    
    # Set calories burned if provided
    if workout_update.calories_burned:
        workout.calories_burned = workout_update.calories_burned
    
    db.commit()
    db.refresh(workout)
    
    # Get exercise count
    exercise_count = db.query(ExerciseLog).filter(
        ExerciseLog.workout_id == workout.id
    ).count()
    
    # Add exercise count to response
    setattr(workout, "exercise_count", exercise_count)
    
    return workout

@router.get("/active", response_model=Optional[WorkoutResponse])
async def get_active_workout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's active workout session if one exists"""
    workout = db.query(Workout).filter(
        Workout.user_id == current_user.id,
        Workout.end_time == None
    ).first()
    
    if not workout:
        return None
    
    # Get exercise count
    exercise_count = db.query(ExerciseLog).filter(
        ExerciseLog.workout_id == workout.id
    ).count()
    
    # Add exercise count to response
    setattr(workout, "exercise_count", exercise_count)
    
    return workout

@router.get("/", response_model=WorkoutListResponse)
async def get_workouts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """Get the current user's workout sessions"""
    # Get total count
    total = db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).count()
    
    # Get workouts with pagination
    workouts = db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).order_by(Workout.start_time.desc()).offset(skip).limit(limit).all()
    
    # Add exercise counts to each workout
    for workout in workouts:
        exercise_count = db.query(ExerciseLog).filter(
            ExerciseLog.workout_id == workout.id
        ).count()
        setattr(workout, "exercise_count", exercise_count)
    
    return {"workouts": workouts, "total": total}

@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workout session"""
    workout = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == current_user.id
    ).first()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    
    # Get exercise count
    exercise_count = db.query(ExerciseLog).filter(
        ExerciseLog.workout_id == workout.id
    ).count()
    
    # Add exercise count to response
    setattr(workout, "exercise_count", exercise_count)
    
    return workout

@router.get("/stats/summary")
async def get_workout_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workout summary statistics"""
    # Total workouts
    total_workouts = db.query(Workout).filter(
        Workout.user_id == current_user.id,
        Workout.end_time.isnot(None)  # Only count completed workouts
    ).count()
    
    # Total workout minutes
    total_minutes = db.query(func.sum(Workout.duration_seconds)).filter(
        Workout.user_id == current_user.id,
        Workout.duration_seconds.isnot(None)
    ).scalar()
    
    # Convert to minutes and handle None
    total_minutes = int(total_minutes / 60) if total_minutes else 0
    
    # Total calories burned
    total_calories = db.query(func.sum(Workout.calories_burned)).filter(
        Workout.user_id == current_user.id,
        Workout.calories_burned.isnot(None)
    ).scalar() or 0
    
    # Average workout duration
    avg_duration = db.query(func.avg(Workout.duration_seconds)).filter(
        Workout.user_id == current_user.id,
        Workout.duration_seconds.isnot(None)
    ).scalar()
    
    # Convert to minutes and handle None
    avg_duration_minutes = int(avg_duration / 60) if avg_duration else 0
    
    # Get most recent workout
    latest_workout = db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).order_by(Workout.start_time.desc()).first()
    
    # Calculate streak (consecutive days with workouts)
    streak = 0
    if latest_workout:
        # Start from today and go back to check consecutive days
        current_date = datetime.now().date()
        
        # If the latest workout was today, start counting
        if latest_workout.start_time.date() == current_date:
            streak = 1
            
            # Check previous days
            day_to_check = current_date - timedelta(days=1)
            
            while True:
                # Check if there's a workout on this day
                workout_on_day = db.query(Workout).filter(
                    Workout.user_id == current_user.id,
                    func.date(Workout.start_time) == day_to_check
                ).first()
                
                if workout_on_day:
                    streak += 1
                    day_to_check -= timedelta(days=1)
                else:
                    break
    
    return {
        "total_workouts": total_workouts,
        "total_minutes": total_minutes,
        "total_calories": round(total_calories, 1),
        "avg_duration_minutes": avg_duration_minutes,
        "current_streak": streak,
        "last_workout": latest_workout.start_time.isoformat() if latest_workout else None
    }