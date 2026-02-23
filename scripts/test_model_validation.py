#!/usr/bin/env python3
"""
Test script for model validation system
Demonstrates how to validate models are correctly loaded and functioning
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model_validation():
    """Test the model validation system"""
    print("🧪 Testing Model Validation System")
    print("=" * 50)
    
    try:
        # Import validation components
        from app.services.model_validator import get_model_validator
        from app.services.model_cache_manager import get_model_cache_manager
        
        print("✅ Successfully imported validation components")
        
        # Initialize validator and cache manager
        validator = get_model_validator()
        cache_manager = get_model_cache_manager()
        
        print("✅ Successfully initialized validator and cache manager")
        
        # Test cache manager
        print("\n📊 Cache Manager Status:")
        cache_health = cache_manager.get_cache_health()
        print(f"  Status: {cache_health['status']}")
        print(f"  Loaded models: {cache_manager.get_loaded_models()}")
        print(f"  Available models: {cache_manager.get_available_models()}")
        
        # Test validator
        print("\n🔍 Validator Status:")
        validation_results = validator.get_validation_results()
        print(f"  Previous validations: {len(validation_results)}")
        
        # Test with a simple model if available
        available_models = cache_manager.get_available_models()
        if available_models:
            test_model = available_models[0]  # Use first available model
            print(f"\n🧪 Testing with model: {test_model}")
            
            # Try to get model from cache
            model = cache_manager.get_model(test_model)
            if model is not None:
                print(f"✅ Model {test_model} loaded from cache")
                
                # Run validation
                print(f"🔍 Validating model {test_model}...")
                start_time = time.time()
                result = validator.validate_model(test_model, model)
                validation_time = time.time() - start_time
                
                print(f"⏱️  Validation completed in {validation_time:.2f} seconds")
                print(f"📊 Status: {result['status']}")
                print(f"📊 Overall Score: {result['overall_score']:.2f}")
                
                # Show test results
                print("\n📋 Test Results:")
                for test_name, test_result in result['tests'].items():
                    status_emoji = "✅" if test_result['passed'] else "❌"
                    print(f"  {status_emoji} {test_name}: {test_result['score']:.2f}")
                
                if result['errors']:
                    print(f"\n❌ Errors: {result['errors']}")
                
                if result['warnings']:
                    print(f"\n⚠️  Warnings: {result['warnings']}")
                
            else:
                print(f"⚠️  Model {test_model} not available in cache")
                print("💡 Try running: python scripts/validate_models.py --models base --preload")
        else:
            print("⚠️  No models available for testing")
            print("💡 Make sure Whisper is installed and models are configured")
        
        print("\n✅ Model validation system test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints for model validation"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    try:
        import requests
        
        base_url = "http://localhost:5001"
        
        # Test health check endpoint
        print("🔍 Testing health check endpoint...")
        try:
            response = requests.get(f"{base_url}/api/validate/models/health-check", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check: {data['overall_status']}")
                print(f"   Healthy models: {data['healthy_count']}/{data['total_count']}")
            else:
                print(f"⚠️  Health check failed: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to API server")
            print("💡 Make sure the server is running: python app_main.py")
        except Exception as e:
            print(f"⚠️  Health check error: {e}")
        
        # Test cache status endpoint
        print("\n🔍 Testing cache status endpoint...")
        try:
            response = requests.get(f"{base_url}/api/cache/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cache status: {data['health']['status']}")
                print(f"   Loaded models: {data['loaded_models']}")
            else:
                print(f"⚠️  Cache status failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Cache status error: {e}")
        
    except ImportError:
        print("⚠️  Requests library not available for API testing")
        print("💡 Install with: pip install requests")
    except Exception as e:
        print(f"⚠️  API test error: {e}")

def main():
    """Main test function"""
    print("🚀 EchoScribe Model Validation Test Suite")
    print("=" * 60)
    
    # Test model validation system
    validation_success = test_model_validation()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    if validation_success:
        print("✅ All tests completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Run full validation: python scripts/validate_models.py --models base small")
        print("   2. Check API endpoints: curl http://localhost:5001/api/validate/models/health-check")
        print("   3. Monitor model health: python scripts/validate_models.py --quick")
    else:
        print("❌ Some tests failed!")
        print("\n💡 Troubleshooting:")
        print("   1. Check dependencies: pip install -r requirements.txt")
        print("   2. Verify Whisper installation: python -c 'import whisper'")
        print("   3. Check configuration: python scripts/validate_models.py --help")
    
    return validation_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
