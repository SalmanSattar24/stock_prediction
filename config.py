"""
Environment Configuration Helper
Loads and validates all API keys and configuration settings
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class EnvironmentConfig:
    """Manage environment configuration and API keys"""

    def __init__(self, env_file: str = '.env'):
        """Initialize configuration loader"""
        self.env_file = env_file
        self.config = {}
        self.missing_keys = []
        self.invalid_keys = []

    def load_env_file(self) -> bool:
        """Load .env file using python-dotenv"""
        try:
            from dotenv import load_dotenv
            result = load_dotenv(self.env_file)
            if not result and Path(self.env_file).exists():
                print(f"⚠️  Warning: .env file exists but couldn't load")
            elif not Path(self.env_file).exists():
                print(f"⚠️  Warning: {self.env_file} not found")
            return True
        except ImportError:
            print("Error: python-dotenv not installed. Install with: pip install python-dotenv")
            return False

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate all required API keys are present"""
        required_keys = {
            'FINNHUB_API_KEY': 'Finnhub (real-time quotes)',
            'NEWSAPI_KEY': 'NewsAPI (news sentiment)',
        }

        optional_keys = {
            'ALPHAVANTAGE_KEY': 'Alpha Vantage (earnings)',
            'EODHD_KEY': 'EODHD (EOD data)',
            'REDDIT_CLIENT_ID': 'Reddit (social sentiment)',
            'REDDIT_CLIENT_SECRET': 'Reddit (social sentiment)',
            'REDDIT_USER_AGENT': 'Reddit user agent',
        }

        results = {}

        print("\n" + "="*70)
        print("API KEY VALIDATION")
        print("="*70)

        # Check required keys
        print("\n📍 REQUIRED KEYS:")
        for key, description in required_keys.items():
            value = os.getenv(key)
            if value:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
                print(f"  ✓ {key:<30} {description:<30} [{masked}]")
                results[key] = True
            else:
                print(f"  ✗ {key:<30} {description:<30} [MISSING]")
                results[key] = False
                self.missing_keys.append(key)

        # Check optional keys
        print("\n🔧 OPTIONAL KEYS:")
        for key, description in optional_keys.items():
            value = os.getenv(key)
            if value:
                masked = value[:4] + "*" * max(0, len(value) - 8) + (value[-4:] if len(value) > 4 else "")
                print(f"  ✓ {key:<30} {description:<30} [{masked}]")
                results[key] = True
            else:
                print(f"  ○ {key:<30} {description:<30} [not set]")
                results[key] = False

        return results

    def get_summary(self) -> Tuple[int, int]:
        """Get summary of configuration status"""
        self.load_env_file()
        results = self.validate_api_keys()

        required = {'FINNHUB_API_KEY', 'NEWSAPI_KEY'}
        keys_found = sum(1 for k, v in results.items() if v and k in required)

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Required keys configured: {keys_found}/2")
        print(f"Optional keys configured: {sum(1 for k, v in results.items() if v and k not in required)}/5")

        if self.missing_keys:
            print(f"\n⚠️  Missing required keys:")
            for key in self.missing_keys:
                print(f"   - {key}")
            print(f"\n→ See SETUP_INSTRUCTIONS.md for how to get these keys")

        return keys_found, len(results)

    def get_all_config(self) -> Dict[str, str]:
        """Get all configuration values (only loaded, not defaults)"""
        self.load_env_file()

        config = {
            # Financial Data
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', ''),
            'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', ''),
            'ALPHAVANTAGE_KEY': os.getenv('ALPHAVANTAGE_KEY', ''),
            'EODHD_KEY': os.getenv('EODHD_KEY', ''),

            # Reddit
            'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID', ''),
            'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET', ''),
            'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT', 'QuantSignalSystem/1.0'),

            # System
            'INITIAL_CAPITAL': os.getenv('INITIAL_CAPITAL', '100000'),
            'RISK_PER_TRADE': os.getenv('RISK_PER_TRADE', '0.02'),
            'MAX_POSITION_SIZE': os.getenv('MAX_POSITION_SIZE', '0.05'),
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
        }

        return config

    def create_env_file_template(self, output_path: str = '.env') -> bool:
        """Create .env file from template if it doesn't exist"""
        if Path(output_path).exists():
            print(f"✓ {output_path} already exists")
            return True

        template = """# Stock Signal System - API Keys
# See SETUP_INSTRUCTIONS.md for how to get these keys

# Finnhub (Real-time stock quotes)
FINNHUB_API_KEY=your_finnhub_key_here

# NewsAPI (Financial news sentiment)
NEWSAPI_KEY=your_newsapi_key_here

# Alpha Vantage (Earnings data - optional)
ALPHAVANTAGE_KEY=your_alphavantage_key_here

# EODHD (End-of-day data - optional)
EODHD_KEY=your_eodhd_key_here

# Reddit API (Social sentiment - optional)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=QuantSignalSystem/1.0 by YourUsername

# Trading Configuration
INITIAL_CAPITAL=100000
RISK_PER_TRADE=0.02
MAX_POSITION_SIZE=0.05
ENVIRONMENT=development
"""

        try:
            with open(output_path, 'w') as f:
                f.write(template)
            print(f"✓ Created {output_path} template")
            print(f"→ Edit {output_path} and add your API keys")
            return True
        except Exception as e:
            print(f"✗ Failed to create {output_path}: {e}")
            return False


def setup_environment():
    """Quick setup function - creates .env and validates"""
    print("\n" + "="*70)
    print("STOCK SIGNAL SYSTEM - ENVIRONMENT SETUP")
    print("="*70)

    config = EnvironmentConfig()

    # Create template if needed
    if not Path('.env').exists():
        print("\n1️⃣  Creating .env file template...")
        config.create_env_file_template()
        print("→ Please edit .env and add your API keys")
        print("→ See SETUP_INSTRUCTIONS.md for detailed instructions\n")
        return False

    # Validate existing config
    print("\n2️⃣  Validating environment configuration...")
    required_found, total_found = config.get_summary()

    if required_found >= 2:
        print("\n✓ READY TO USE! All required keys are configured.")
        return True
    else:
        print("\n✗ Please configure required API keys before proceeding.")
        return False


def get_api_key(key_name: str) -> str:
    """Safely get an API key from environment"""
    from dotenv import load_dotenv
    load_dotenv()

    value = os.getenv(key_name)
    if not value:
        print(f"Error: {key_name} not found in environment")
        print(f"Please add it to .env file (see SETUP_INSTRUCTIONS.md)")
        return None

    return value


if __name__ == "__main__":
    # Run setup check
    if len(sys.argv) > 1:
        if sys.argv[1] == '--setup':
            success = setup_environment()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == '--validate':
            config = EnvironmentConfig()
            config.get_summary()
            sys.exit(0)
        elif sys.argv[1] == '--show':
            config = EnvironmentConfig()
            all_config = config.get_all_config()
            print("\nConfiguration:")
            for key, value in all_config.items():
                if value and key.endswith('_KEY'):
                    masked = value[:4] + "*" * max(0, len(value) - 8) + (value[-4:] if len(value) > 4 else "")
                    print(f"  {key}: {masked}")
                elif value:
                    print(f"  {key}: {value}")
            sys.exit(0)
    else:
        # Default: validate and show status
        setup_environment()
