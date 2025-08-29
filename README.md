# FitTrack AI - Enhanced Fitness & Posture Monitoring System

![FitTrack AI](https://img.shields.io/badge/FitTrack-AI%20Powered-blue?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.2.0-61DAFB?style=for-the-badge&logo=react)
![Python](https://img.shields.io/badge/Python-Flask-green?style=for-the-badge&logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow.js-AI%20Powered-orange?style=for-the-badge&logo=tensorflow)

## 🚀 Overview

FitTrack AI is a comprehensive fitness tracking application that combines AI-powered posture monitoring, real-time exercise form analysis, nutrition tracking, and health insights. Built with React and Python, it offers a modern, animated interface with professional-grade health monitoring capabilities.

## ✨ Features

### 🎨 Modern UI Design
- **Custom Color Palette**: Electric Blue (#3A86FF), Vibrant Coral (#FF6B6B), Lime Green (#06D6A0)
- **Smooth Animations**: Framer Motion powered transitions and interactions
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Glass Morphism Effects**: Modern blur effects and transparency

### 🏥 Comprehensive Health Tracking
- **📊 Nutrition Tracking**: Log meals with detailed macronutrient breakdown
- **💧 Water Intake Monitoring**: Daily hydration tracking with visual progress
- **⚖️ BMI Calculator**: Interactive height/weight BMI calculation with health categories
- **📈 Weekly Progress Charts**: Visual trend analysis using Recharts
- **🧘 Posture Monitoring**: AI-powered real-time posture analysis
- **🤖 Smart Recommendations**: Personalized health insights and suggestions

### 🏃‍♂️ Exercise & Fitness
- **Real-time Pose Detection**: TensorFlow.js MoveNet integration
- **Exercise Form Analysis**: AI-powered form correction and scoring
- **Workout History**: Comprehensive session tracking and analytics
- **Progress Visualization**: Charts and graphs for fitness progress

### 🔐 User Management
- **Secure Authentication**: JWT-based user authentication system
- **Profile Management**: Personalized user profiles and settings
- **Data Persistence**: SQLite database for reliable data storage

## 🛠️ Technology Stack

### Frontend
- **React 18.2.0**: Modern React with hooks and functional components
- **Material-UI**: Professional UI components and theming
- **Framer Motion**: Smooth animations and transitions
- **Recharts**: Data visualization and charts
- **TensorFlow.js**: AI-powered pose detection and analysis
- **React Router**: Client-side routing and navigation

### Backend
- **Flask**: Lightweight Python web framework
- **SQLAlchemy**: Database ORM and management
- **SQLite**: Local database storage
- **Flask-CORS**: Cross-origin resource sharing
- **JWT Authentication**: Secure user authentication

### AI/ML
- **TensorFlow.js MoveNet**: Real-time pose estimation
- **Custom Pose Analysis**: Form correction algorithms
- **Smart Recommendations**: AI-powered health insights

## 🚀 Getting Started

### Prerequisites
- **Node.js** (v14 or higher)
- **Python** (v3.8 or higher)
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Honey-30/posture.git
   cd posture
   ```

2. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   ```

3. **Setup Backend**
   ```bash
   cd ../backend
   pip install flask flask-cors sqlite3
   ```

### Running the Application

1. **Start Backend Server**
   ```bash
   cd backend
   python simple_server.py
   ```
   Backend will run on http://localhost:8002

2. **Start Frontend Development Server**
   ```bash
   cd frontend
   npm start
   ```
   Frontend will run on http://localhost:3000

3. **Access the Application**
   Open your browser and navigate to http://localhost:3000

## 📱 Screenshots & Features

### Dashboard Overview
- Modern animated dashboard with health metrics
- Real-time posture monitoring with AI feedback
- Weekly progress visualization with interactive charts
- Quick action buttons for easy navigation

### Nutrition Tracking
- Detailed meal logging with macronutrient breakdown
- Interactive nutrition dialog with form validation
- Daily nutrition summary with visual indicators
- Water intake tracking with progress bars

### Exercise Monitoring
- Real-time pose detection using webcam
- AI-powered form analysis and corrections
- Exercise session tracking and history
- Progress charts and analytics

## 🎯 Usage

### Getting Started
1. **Registration**: Create an account or use demo credentials
2. **Dashboard**: View your health overview and quick stats
3. **Nutrition**: Log meals and track daily nutrition intake
4. **Water Intake**: Monitor hydration with one-click logging
5. **Exercise**: Start workout sessions with AI form analysis
6. **Posture**: Enable posture monitoring for real-time feedback

### Key Interactions
- **Hover Effects**: Interactive elements respond to mouse hover
- **Smooth Transitions**: All navigation and state changes are animated
- **Real-time Updates**: Data updates immediately without page refresh
- **Mobile Responsive**: Full functionality on mobile devices

## 🔧 Configuration

### API Configuration
Update the API base URL in `frontend/src/config/api.js`:
```javascript
export const API_BASE_URL = 'http://localhost:8002';
```

### Theme Customization
Modify the color theme in `frontend/src/pages/Dashboard.js`:
```javascript
const theme = {
  electricBlue: '#3A86FF',
  vibrantCoral: '#FF6B6B', 
  limeGreen: '#06D6A0',
  darkCharcoal: '#1B1B1F'
};
```

## 📊 Database Schema

The application uses SQLite with the following main tables:
- `users`: User authentication and profile data
- `workout_sessions`: Exercise session tracking
- `nutrition_logs`: Meal and nutrition data
- `water_intake`: Daily hydration tracking
- `posture_logs`: Posture monitoring data
- `user_stats`: Comprehensive user statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TensorFlow.js**: For providing the MoveNet pose detection model
- **Material-UI**: For the beautiful React components
- **Framer Motion**: For smooth animations and transitions
- **Recharts**: For data visualization capabilities

## 📞 Contact

**Developer**: Honey  
**GitHub**: [@Honey-30](https://github.com/Honey-30)  
**Repository**: [posture](https://github.com/Honey-30/posture)

---

**Built with ❤️ using React, Python, and AI**
