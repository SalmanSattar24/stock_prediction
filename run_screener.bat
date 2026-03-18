@echo off
REM Explosive Move Screener Launcher
REM Run this batch file to screen all stocks for explosive moves

echo.
echo ============================================================================
echo EXPLOSIVE MOVE STOCK SCREENER
echo ============================================================================
echo.

REM Set API Keys
if "%FINNHUB_API_KEY%"=="" (
  echo ERROR: FINNHUB_API_KEY is not set.
  echo Set it in your shell or .env file before running.
  goto :end
)
if "%NEWSAPI_KEY%"=="" (
  echo ERROR: NEWSAPI_KEY is not set.
  echo Set it in your shell or .env file before running.
  goto :end
)

REM Check if Gmail password is set
if "%GMAIL_APP_PASSWORD%"=="" (
    echo WARNING: GMAIL_APP_PASSWORD not set. Emails will not send.
    echo To enable emails, set: set GMAIL_APP_PASSWORD=your_16_char_password
    echo.
)

echo Starting comprehensive stock screening...
echo Target: 10%% gains in 3-30 days
echo Stocks to screen: 23,065
echo.

REM Run screener
python ^
  screener/run_explosive_screener.py

echo.
echo ============================================================================
echo SCREENING COMPLETE
echo Results saved to: explosive_picks.txt
echo ============================================================================
echo.

REM Show top 10 results
if exist explosive_picks.txt (
    echo TOP 10 CANDIDATES:
    echo.
  type explosive_picks.txt
)

:end
pause
