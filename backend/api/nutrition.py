from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_

from database.database import get_db
from database.models import User, NutritionLog, WaterIntake
from api.auth import get_current_user

router = APIRouter()

class NutritionCreate(BaseModel):
    meal_type: str
    food_name: str
    calories: float
    protein: float
    carbs: float
    fats: float
    portion_size: Optional[float] = None

class NutritionResponse(BaseModel):
    id: int
    meal_type: str
    food_name: str
    calories: float
    protein: float
    carbs: float
    fats: float
    portion_size: Optional[float]
    date: datetime

class WaterIntakeCreate(BaseModel):
    amount_ml: int

class WaterIntakeResponse(BaseModel):
    id: int
    amount_ml: int
    date: datetime

class BMICalculation(BaseModel):
    height: float  # in cm
    weight: float  # in kg

class BMIResponse(BaseModel):
    bmi: float
    category: str
    healthy_weight_min: float
    healthy_weight_max: float

@router.post("/log", response_model=NutritionResponse)
async def log_nutrition(
    nutrition: NutritionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log nutrition intake"""
    nutrition_log = NutritionLog(
        user_id=current_user.id,
        meal_type=nutrition.meal_type,
        food_name=nutrition.food_name,
        calories=nutrition.calories,
        protein=nutrition.protein,
        carbs=nutrition.carbs,
        fats=nutrition.fats,
        portion_size=nutrition.portion_size
    )
    
    db.add(nutrition_log)
    db.commit()
    db.refresh(nutrition_log)
    
    return nutrition_log

@router.get("/daily", response_model=List[NutritionResponse])
async def get_daily_nutrition(
    target_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get nutrition logs for a specific date"""
    if target_date:
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        date_obj = datetime.now().date()
    
    nutrition_logs = db.query(NutritionLog).filter(
        and_(
            NutritionLog.user_id == current_user.id,
            func.date(NutritionLog.date) == date_obj
        )
    ).all()
    
    return nutrition_logs

@router.get("/weekly-stats")
async def get_weekly_nutrition_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly nutrition statistics"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Get weekly totals
    weekly_stats = db.query(
        func.sum(NutritionLog.calories).label('total_calories'),
        func.sum(NutritionLog.protein).label('total_protein'),
        func.sum(NutritionLog.carbs).label('total_carbs'),
        func.sum(NutritionLog.fats).label('total_fats'),
        func.avg(NutritionLog.calories).label('avg_calories')
    ).filter(
        and_(
            NutritionLog.user_id == current_user.id,
            NutritionLog.date >= start_date,
            NutritionLog.date <= end_date
        )
    ).first()
    
    return {
        "total_calories": round(weekly_stats.total_calories or 0, 1),
        "total_protein": round(weekly_stats.total_protein or 0, 1),
        "total_carbs": round(weekly_stats.total_carbs or 0, 1),
        "total_fats": round(weekly_stats.total_fats or 0, 1),
        "avg_daily_calories": round(weekly_stats.avg_calories or 0, 1)
    }

@router.post("/water", response_model=WaterIntakeResponse)
async def log_water_intake(
    water: WaterIntakeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log water intake"""
    water_log = WaterIntake(
        user_id=current_user.id,
        amount_ml=water.amount_ml
    )
    
    db.add(water_log)
    db.commit()
    db.refresh(water_log)
    
    return water_log

@router.get("/water/daily")
async def get_daily_water_intake(
    target_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily water intake total"""
    if target_date:
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        date_obj = datetime.now().date()
    
    total_water = db.query(func.sum(WaterIntake.amount_ml)).filter(
        and_(
            WaterIntake.user_id == current_user.id,
            func.date(WaterIntake.date) == date_obj
        )
    ).scalar() or 0
    
    # Recommended daily intake (2000ml = 8 cups)
    recommended = 2000
    percentage = min(100, (total_water / recommended) * 100)
    
    return {
        "total_ml": total_water,
        "recommended_ml": recommended,
        "percentage": round(percentage, 1),
        "cups": round(total_water / 250, 1)  # 250ml per cup
    }

@router.post("/bmi", response_model=BMIResponse)
async def calculate_bmi(
    bmi_data: BMICalculation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate BMI and category"""
    height_m = bmi_data.height / 100  # Convert cm to meters
    bmi = bmi_data.weight / (height_m ** 2)
    
    # Determine BMI category
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    # Calculate healthy weight range
    healthy_min = 18.5 * (height_m ** 2)
    healthy_max = 24.9 * (height_m ** 2)
    
    # Update user profile with latest measurements
    current_user.height = bmi_data.height
    current_user.weight = bmi_data.weight
    db.commit()
    
    return {
        "bmi": round(bmi, 1),
        "category": category,
        "healthy_weight_min": round(healthy_min, 1),
        "healthy_weight_max": round(healthy_max, 1)
    }

@router.get("/daily-summary")
async def get_daily_nutrition_summary(
    target_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive daily nutrition summary"""
    if target_date:
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        date_obj = datetime.now().date()
    
    # Get daily nutrition totals
    daily_totals = db.query(
        func.sum(NutritionLog.calories).label('total_calories'),
        func.sum(NutritionLog.protein).label('total_protein'),
        func.sum(NutritionLog.carbs).label('total_carbs'),
        func.sum(NutritionLog.fats).label('total_fats'),
        func.count(NutritionLog.id).label('meal_count')
    ).filter(
        and_(
            NutritionLog.user_id == current_user.id,
            func.date(NutritionLog.date) == date_obj
        )
    ).first()
    
    # Get water intake
    total_water = db.query(func.sum(WaterIntake.amount_ml)).filter(
        and_(
            WaterIntake.user_id == current_user.id,
            func.date(WaterIntake.date) == date_obj
        )
    ).scalar() or 0
    
    return {
        "calories": round(daily_totals.total_calories or 0, 1),
        "protein": round(daily_totals.total_protein or 0, 1),
        "carbs": round(daily_totals.total_carbs or 0, 1),
        "fats": round(daily_totals.total_fats or 0, 1),
        "meal_count": daily_totals.meal_count or 0,
        "water_ml": total_water,
        "water_percentage": min(100, (total_water / 2000) * 100)
    }
