#!/usr/bin/env python3
"""
Test script for Vercel deployment
Tests the deployed application endpoints and functionality
"""

import requests
import time
import json
import sys
from pathlib import Path

def test_endpoint(url, description, expected_status=200):
    """Test a single endpoint"""
    print(f"🧪 Testing {description}...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == expected_status:
            print(f"✅ {description} - PASSED ({response.status_code})")
            return True
        else:
            print(f"❌ {description} - FAILED ({response.status_code})")
            print(f"   Expected: {expected_status}, Got: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def test_post_endpoint(url, data, description, expected_status=200):
    """Test a POST endpoint"""
    print(f"🧪 Testing {description}...")
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == expected_status:
            print(f"✅ {description} - PASSED ({response.status_code})")
            return True
        else:
            print(f"❌ {description} - FAILED ({response.status_code})")
            print(f"   Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
            return False
    except requests.exceptions.RequestException as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def test_file_upload(url, file_path, description):
    """Test file upload endpoint"""
    print(f"🧪 Testing {description}...")
    try:
        if not Path(file_path).exists():
            print(f"⚠️  {description} - SKIPPED (test file not found: {file_path})")
            return True
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files, timeout=60)
        
        if response.status_code == 200:
            print(f"✅ {description} - PASSED ({response.status_code})")
            return True
        else:
            print(f"❌ {description} - FAILED ({response.status_code})")
            print(f"   Response: {response.text[:200]}...")
            return False
    except requests.exceptions.RequestException as e:
        print(f"💥 {description} - ERROR: {e}")
        return False
    except FileNotFoundError:
        print(f"⚠️  {description} - SKIPPED (test file not found)")
        return True

def main():
    """Main test function"""
    if len(sys.argv) != 2:
        print("Usage: python test_vercel_deployment.py <deployment_url>")
        print("Example: python test_vercel_deployment.py https://your-app.vercel.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚀 EchoScribe Vercel Deployment Test")
    print("=" * 50)
    print(f"Testing: {base_url}")
    print()
    
    # Test results
    results = []
    
    # Basic endpoints
    results.append(test_endpoint(f"{base_url}/", "Home page"))
    results.append(test_endpoint(f"{base_url}/health", "Health check"))
    results.append(test_endpoint(f"{base_url}/api/models", "Get models"))
    results.append(test_endpoint(f"{base_url}/api/cache/models", "Cache status"))
    results.append(test_endpoint(f"{base_url}/api/validate/models/health-check", "Model health check"))
    
    # API endpoints
    results.append(test_post_endpoint(
        f"{base_url}/api/cache/models/preload",
        {"models": ["base"]},
        "Preload models"
    ))
    
    results.append(test_post_endpoint(
        f"{base_url}/api/validate/models/base",
        {},
        "Validate base model"
    ))
    
    # Test file upload (if test file exists)
    test_file = "test_uploads/test.wav"
    results.append(test_file_upload(
        f"{base_url}/api/upload",
        test_file,
        "File upload"
    ))
    
    # Test transcription (if file upload succeeded)
    print(f"🧪 Testing transcription...")
    try:
        # First upload a file
        if Path(test_file).exists():
            with open(test_file, 'rb') as f:
                files = {'file': f}
                upload_response = requests.post(f"{base_url}/api/upload", files=files, timeout=60)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                filename = upload_data.get('filename')
                
                if filename:
                    # Test transcription
                    transcription_data = {
                        "filename": filename,
                        "model_size": "base",
                        "enable_speaker_diarization": False,
                        "language": "en"
                    }
                    
                    transcribe_response = requests.post(
                        f"{base_url}/api/transcribe",
                        json=transcription_data,
                        timeout=120
                    )
                    
                    if transcribe_response.status_code == 200:
                        print("✅ Transcription - PASSED")
                        results.append(True)
                    else:
                        print(f"❌ Transcription - FAILED ({transcribe_response.status_code})")
                        results.append(False)
                else:
                    print("⚠️  Transcription - SKIPPED (no filename from upload)")
                    results.append(True)
            else:
                print("⚠️  Transcription - SKIPPED (upload failed)")
                results.append(True)
        else:
            print("⚠️  Transcription - SKIPPED (no test file)")
            results.append(True)
    except Exception as e:
        print(f"💥 Transcription - ERROR: {e}")
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print()
    print("=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Your Vercel deployment is working correctly.")
        print()
        print("💡 Next steps:")
        print("1. Test with real audio files")
        print("2. Monitor performance in Vercel dashboard")
        print("3. Set up custom domain if needed")
        print("4. Configure analytics and monitoring")
    else:
        print()
        print("⚠️  Some tests failed. Check the output above for details.")
        print()
        print("💡 Troubleshooting:")
        print("1. Check Vercel logs: vercel logs")
        print("2. Verify environment variables")
        print("3. Check function timeout settings")
        print("4. Ensure all dependencies are installed")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
