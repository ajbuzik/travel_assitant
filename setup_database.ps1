@echo off
REM setup_database.bat - Windows version
echo.
echo 🏰 Krakow POI App - Database Setup Script (Windows)
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows/
    pause
    exit /b 1
)

REM Create directory structure
echo 📁 Creating directory structure...
if not exist "init-scripts" mkdir init-scripts
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Create environment file
echo 📝 Creating environment file...
(
echo # Database Configuration
echo DB_HOST=localhost
echo DB_PORT=5432
echo DB_NAME=krakow_feedback
echo DB_USER=krakow_app
echo DB_PASSWORD=krakow_password123
echo.
echo # Admin Configuration ^(for setup only^)
echo DB_ADMIN_USER=postgres
echo DB_ADMIN_PASSWORD=postgres
echo.
echo # Application Configuration
echo GEMINI_API_KEY=your_gemini_api_key_here
echo INSERT_SAMPLE_DATA=true
echo.
echo # Docker Configuration
echo POSTGRES_DB=krakow_feedback
echo POSTGRES_USER=postgres
echo POSTGRES_PASSWORD=postgres
echo PGADMIN_DEFAULT_EMAIL=admin@krakow.com
echo PGADMIN_DEFAULT_PASSWORD=admin123
) > .env

echo ✅ Environment file created (.env)

REM Create init script for Docker
echo 📝 Creating database initialization script...
(
echo -- Create application user and grant permissions
echo CREATE USER krakow_app WITH PASSWORD 'krakow_password123'^;
echo GRANT ALL PRIVILEGES ON DATABASE krakow_feedback TO krakow_app^;
echo.
echo -- Connect to the application database
echo \c krakow_feedback
echo.
echo -- Grant schema permissions
echo GRANT ALL ON SCHEMA public TO krakow_app^;
echo GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO krakow_app^;
echo GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO krakow_app^;
echo.
echo -- Enable extensions
echo CREATE EXTENSION IF NOT EXISTS "uuid-ossp"^;
echo CREATE EXTENSION IF NOT EXISTS "pg_trgm"^;
echo.
echo -- Create tables
echo CREATE TABLE IF NOT EXISTS user_interactions ^(
echo     id SERIAL PRIMARY KEY,
echo     session_id VARCHAR^(255^) NOT NULL,
echo     query TEXT NOT NULL,
echo     response TEXT NOT NULL,
echo     feedback_rating INTEGER CHECK ^(feedback_rating ^>= 1 AND feedback_rating ^<= 5^),
echo     feedback_comment TEXT,
echo     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
echo     user_agent TEXT,
echo     search_results JSONB,
echo     query_intent VARCHAR^(100^),
echo     response_time_ms INTEGER,
echo     user_ip INET,
echo     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
echo     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
echo ^)^;
echo.
echo CREATE TABLE IF NOT EXISTS agent_actions ^(
echo     id SERIAL PRIMARY KEY,
echo     session_id VARCHAR^(255^) NOT NULL,
echo     action_type VARCHAR^(100^) NOT NULL,
echo     action_details JSONB,
echo     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
echo     processing_time_ms INTEGER,
echo     success BOOLEAN DEFAULT TRUE,
echo     error_message TEXT
echo ^)^;
echo.
echo CREATE TABLE IF NOT EXISTS user_sessions ^(
echo     id SERIAL PRIMARY KEY,
echo     session_id VARCHAR^(255^) UNIQUE NOT NULL,
echo     start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
echo     end_time TIMESTAMP,
echo     total_queries INTEGER DEFAULT 0,
echo     avg_rating DECIMAL^(3,2^),
echo     user_agent TEXT,
echo     user_ip INET,
echo     session_duration_minutes INTEGER
echo ^)^;
echo.
echo CREATE TABLE IF NOT EXISTS poi_analytics ^(
echo     id SERIAL PRIMARY KEY,
echo     poi_id INTEGER,
echo     poi_name VARCHAR^(500^),
echo     query_count INTEGER DEFAULT 1,
echo     last_queried TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
echo     avg_user_rating DECIMAL^(3,2^),
echo     total_ratings INTEGER DEFAULT 0
echo ^)^;
echo.
echo CREATE TABLE IF NOT EXISTS system_logs ^(
echo     id SERIAL PRIMARY KEY,
echo     log_level VARCHAR^(20^),
echo     message TEXT,
echo     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
echo     component VARCHAR^(100^),
echo     session_id VARCHAR^(255^),
echo     additional_data JSONB
echo ^)^;
echo.
echo -- Create indexes
echo CREATE INDEX IF NOT EXISTS idx_user_interactions_session_id ON user_interactions^(session_id^)^;
echo CREATE INDEX IF NOT EXISTS idx_user_interactions_timestamp ON user_interactions^(timestamp DESC^)^;
echo CREATE INDEX IF NOT EXISTS idx_user_interactions_rating ON user_interactions^(feedback_rating^)^;
echo CREATE INDEX IF NOT EXISTS idx_agent_actions_session_id ON agent_actions^(session_id^)^;
echo CREATE INDEX IF NOT EXISTS idx_agent_actions_timestamp ON agent_actions^(timestamp DESC^)^;
echo.
echo -- Grant permissions on new tables
echo GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO krakow_app^;
echo GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO krakow_app^;
echo.
echo -- Insert sample data
echo INSERT INTO user_interactions ^(session_id, query, response, feedback_rating, feedback_comment^) VALUES
echo ^('sample_session_1', 'Best restaurants in Krakow', 'Here are some great restaurants in Krakow Old Town...', 5, 'Very helpful!'^),
echo ^('sample_session_1', 'Museums to visit', 'Top museums include National Museum, Wawel Castle...', 4, 'Good suggestions'^),
echo ^('sample_session_2', 'Parks and nature', 'Planty Park is a beautiful green ring around the old town...', 5, 'Perfect for my morning jog!'^)^;
echo.
echo INSERT INTO poi_analytics ^(poi_id, poi_name, query_count, avg_user_rating, total_ratings^) VALUES
echo ^(1, 'Main Market Square', 15, 4.8, 12^),
echo ^(2, 'Wawel Castle', 12, 4.9, 10^),
echo ^(3, 'Kazimierz District', 8, 4.6, 7^)^;
) > init-scripts\01-init.sql

echo ✅ Database init script created

REM Start Docker containers
echo 🐳 Starting Docker containers...
docker-compose up -d

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 15 /nobreak > nul

REM Check if containers are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo ❌ Failed to start containers. Check the logs:
    docker-compose logs
    pause
    exit /b 1
) else (
    echo ✅ Docker containers are running successfully!
    echo.
    echo 🎉 Setup completed! Here's what's available:
    echo ===========================================
    echo 📊 PostgreSQL Database:
    echo    - Host: localhost
    echo    - Port: 5432
    echo    - Database: krakow_feedback
    echo    - User: krakow_app
    echo    - Password: krakow_password123
    echo.
    echo 🔧 PgAdmin Web Interface:
    echo    - URL: http://localhost:8080
    echo    - Email: admin@krakow.com
    echo    - Password: admin123
    echo.
    echo 📝 Next steps:
    echo    1. Set your GEMINI_API_KEY in the .env file
    echo    2. Install Python dependencies: pip install -r requirements.txt
    echo    3. Run your Streamlit app: streamlit run app.py
    echo.
    echo 🛠️ Useful commands:
    echo    - Stop containers: docker-compose down
    echo    - View logs: docker-compose logs postgres
    echo    - Reset database: docker-compose down -v ^&^& docker-compose up -d
    echo.
)

pause