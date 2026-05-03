# MedScan AI - Testing Guide

## Test Suite Overview

The comprehensive test suite for MedScan AI includes **30+ test cases** organized into 5 categories:

### 1. **Positive Cases** (5 tests)
✅ Happy path scenarios - verify successful workflows
- Home page loads with correct title & UI
- Upload and analysis completes successfully
- Analysis contains all required sections
- PDF download works
- Uploaded image displays correctly

### 2. **Negative Cases** (6 tests)
❌ Error handling & invalid inputs
- POST /analyze without file → 400 error
- Empty file upload → fails gracefully
- Corrupted image data → 500 error
- Text file instead of image → 500 error
- Cancel nonexistent request → 404 error
- Wrong field name in upload → 400 error

### 3. **Edge Cases** (6 tests)
⚠️ Boundary conditions & unusual inputs
- Very large file upload (10MB+)
- Filenames with special characters (@#$%)
- Multiple file fields in one request
- Zero-byte file upload
- Unicode characters in filename (日本語)

### 4. **Heartbreak Cases** (9 tests)
💔 Unexpected failures & race conditions
- Rapid consecutive uploads (threading issues)
- Cancel request during analysis
- API response JSON structure validation
- Concurrent analysis requests (3x simultaneous)
- Loader element visibility/hiding
- PDF file size verification (>1KB)
- Drop zone visibility state changes

### 5. **Integration Tests** (2 tests)
🔗 Full end-to-end workflows
- Complete user journey (upload → analyze → download)
- UI reset after "New Analysis" click

---

## Running Tests Locally

### Setup
```bash
cd /home/bunnyblack/program/medicalai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python3 -m playwright install chromium
```

### Generate Fixture Image
```bash
python3 scripts/generate_rx_fixture.py
```

### Build & Start Docker
```bash
docker build -t medscanai-ci .
docker run -d --name medscanai-ci -p 5000:5000 -e TEST_MODE=true medscanai-ci
```

### Run All Tests
```bash
pytest tests/test_app.py -v
```

### Run Specific Test Category
```bash
# Positive tests only
pytest tests/test_app.py::TestPositiveCases -v

# Negative tests only
pytest tests/test_app.py::TestNegativeCases -v

# Edge cases only
pytest tests/test_app.py::TestEdgeCases -v

# Heartbreak tests only
pytest tests/test_app.py::TestHeartbreakerCases -v

# Integration tests only
pytest tests/test_app.py::TestIntegration -v
```

### Generate HTML Report
```bash
mkdir -p reports
pytest tests/test_app.py --html=reports/test-report.html
# Open: reports/test-report.html in browser
```

### Run Single Test
```bash
pytest tests/test_app.py::TestPositiveCases::test_pdf_download_success -v
```

---

## Running Tests in GitHub Actions

The workflow is defined in `.github/workflows/test.yml`.

It automatically:
1. ✅ Checks out the repository
2. ✅ Builds the Docker image
3. ✅ Starts container with `TEST_MODE=true`
4. ✅ Installs Playwright & browsers
5. ✅ Runs all tests
6. ✅ Uploads HTML report as artifact

**Trigger on:**
- Push to `main` branch
- Pull requests

**View Results:**
- Download artifact in GitHub Actions tab
- Open `test-report.html` locally

---

## Test Output Example

```
tests/test_app.py::TestPositiveCases::test_app_home_page_loads PASSED
tests/test_app.py::TestPositiveCases::test_upload_and_analysis_complete_flow PASSED
tests/test_app.py::TestPositiveCases::test_analysis_contains_all_sections PASSED
tests/test_app.py::TestPositiveCases::test_pdf_download_success PASSED
tests/test_app.py::TestPositiveCases::test_image_displays_after_upload PASSED

tests/test_app.py::TestNegativeCases::test_analyze_without_file_upload_api PASSED
tests/test_app.py::TestNegativeCases::test_analyze_with_empty_file PASSED
tests/test_app.py::TestNegativeCases::test_analyze_with_invalid_image_data PASSED
tests/test_app.py::TestNegativeCases::test_analyze_with_text_file PASSED
tests/test_app.py::TestNegativeCases::test_cancel_nonexistent_request PASSED
tests/test_app.py::TestNegativeCases::test_upload_missing_field_name PASSED

tests/test_app.py::TestEdgeCases::test_very_large_file_upload PASSED
tests/test_app.py::TestEdgeCases::test_filename_with_special_characters PASSED
tests/test_app.py::TestEdgeCases::test_multiple_file_fields PASSED
tests/test_app.py::TestEdgeCases::test_zero_byte_file PASSED
tests/test_app.py::TestEdgeCases::test_filename_unicode_characters PASSED

tests/test_app.py::TestHeartbreakerCases::test_rapid_consecutive_uploads PASSED
tests/test_app.py::TestHeartbreakerCases::test_cancel_during_analysis PASSED
tests/test_app.py::TestHeartbreakerCases::test_api_response_json_structure PASSED
tests/test_app.py::TestHeartbreakerCases::test_concurrent_analysis_requests PASSED
tests/test_app.py::TestHeartbreakerCases::test_loader_disappears_after_analysis PASSED
tests/test_app.py::TestHeartbreakerCases::test_pdf_contains_image_and_analysis PASSED
tests/test_app.py::TestHeartbreakerCases::test_drop_zone_visibility PASSED

tests/test_app.py::TestIntegration::test_complete_user_journey PASSED
tests/test_app.py::TestIntegration::test_reset_after_new_analysis_click PASSED

====== 28 passed in 45.2s ======
```

---

## Cleanup After Testing

```bash
# Stop Docker container
docker stop medscanai-ci
docker rm medscanai-ci

# Deactivate venv
deactivate
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Tests timeout | Increase timeout values in test code |
| Playwright browsers not found | Run `python3 -m playwright install chromium` |
| Container won't start | Check Docker: `docker logs medscanai-ci` |
| Port 5000 in use | Kill existing container or use different port |
| Fixture image missing | Run `python3 scripts/generate_rx_fixture.py` |

---

## Test Statistics

- **Total Tests:** 28
- **Positive Cases:** 5
- **Negative Cases:** 6
- **Edge Cases:** 6
- **Heartbreak Cases:** 9
- **Integration Tests:** 2
- **Coverage:** UI flows, API endpoints, error handling, concurrency, file validation
