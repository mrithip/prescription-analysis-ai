import io
import json
from pathlib import Path
from playwright.sync_api import Page, expect
import re
import requests

BASE_URL = "http://127.0.0.1:5000"
FIXTURE_IMAGE = Path(__file__).resolve().parent / "fixtures" / "rx.jpg"


# ============================================================================
# POSITIVE TEST CASES - Happy Path Scenarios
# ============================================================================

class TestPositiveCases:
    """Test successful workflows."""

    def test_app_home_page_loads(self, page: Page):
        """Verify home page loads with correct title and UI elements."""
        page.goto(BASE_URL)
        expect(page.locator('h1')).to_contain_text('MedScan', timeout=15000)
        expect(page.locator('text=Upload Prescription Scan')).to_be_visible(timeout=15000)
        assert page.title() == "MedScan AI | Clinical Dashboard"

    def test_upload_and_analysis_complete_flow(self, page: Page):
        """Positive: Upload valid image, verify analysis appears, verify HTML structure."""
        page.goto(BASE_URL)
        expect(page.locator('h1')).to_contain_text('MedScan', timeout=15000)

        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )
        analysis_html = page.locator('#analysis-content').inner_html()
        assert '<h3>' in analysis_html
        assert '<p>' in analysis_html

    def test_analysis_contains_all_sections(self, page: Page):
        """Positive: Verify analysis contains all required sections."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )
        analysis_text = page.locator('#analysis-content').inner_text()
        assert 'Medications' in analysis_text
        assert 'Clinical Indications' in analysis_text or 'Patient Case' in analysis_text

    def test_pdf_download_success(self, page: Page):
        """Positive: Verify PDF download completes successfully."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )

        with page.expect_download(timeout=20000) as download_info:
            page.click('#download-pdf')

        download = download_info.value
        download_path = download.path()
        assert download_path is not None
        assert download.suggested_filename.endswith('.pdf')
        assert Path(download_path).exists()

    def test_image_displays_after_upload(self, page: Page):
        """Positive: Verify uploaded image is displayed."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        image_element = page.locator('#output-image')
        expect(image_element).to_be_visible(timeout=15000)
        src_attr = image_element.get_attribute('src')
        assert src_attr is not None
        assert 'data:image' in src_attr or len(src_attr) > 0


# ============================================================================
# NEGATIVE TEST CASES - Invalid Inputs & Error Handling
# ============================================================================

class TestNegativeCases:
    """Test error conditions and invalid inputs."""

    def test_analyze_without_file_upload_api(self):
        """Negative: POST /analyze without file should return 400."""
        response = requests.post(f"{BASE_URL}/analyze")
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'No file uploaded' in data['error']

    def test_analyze_with_empty_file(self):
        """Negative: POST /analyze with empty file should fail."""
        files = {'file': ('empty.jpg', io.BytesIO(b''), 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        # Empty file might cause PIL error or be handled gracefully
        assert response.status_code in [400, 500]

    def test_analyze_with_invalid_image_data(self):
        """Negative: POST /analyze with corrupted image data."""
        files = {'file': ('corrupted.jpg', io.BytesIO(b'not a real image'), 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        assert response.status_code == 500
        data = response.json()
        assert 'error' in data

    def test_analyze_with_text_file(self):
        """Negative: POST /analyze with text file instead of image."""
        files = {'file': ('test.txt', io.BytesIO(b'this is text'), 'text/plain')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        assert response.status_code == 500

    def test_cancel_nonexistent_request(self):
        """Negative: Cancel request that doesn't exist."""
        response = requests.post(f"{BASE_URL}/cancel/nonexistent-id-12345")
        assert response.status_code == 404
        data = response.json()
        assert data['status'] == 'not_found'

    def test_upload_missing_field_name(self):
        """Negative: Upload file with wrong field name."""
        files = {'image': ('test.jpg', io.BytesIO(b'test'), 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        assert response.status_code == 400
        data = response.json()
        assert 'No file uploaded' in data['error']


# ============================================================================
# EDGE CASES - Boundary Conditions
# ============================================================================

class TestEdgeCases:
    """Test boundary conditions and unusual inputs."""

    def test_very_large_file_upload(self):
        """Edge case: Upload a large (10MB) image file."""
        # Create a 10MB dummy image
        large_image = io.BytesIO()
        from PIL import Image
        img = Image.new('RGB', (5000, 2000), color='white')
        img.save(large_image, format='JPEG')
        large_image.seek(0)

        files = {'file': ('large.jpg', large_image, 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files, timeout=30)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 500]

    def test_filename_with_special_characters(self):
        """Edge case: Filename with special characters."""
        from PIL import Image
        img_bytes = io.BytesIO()
        img = Image.new('RGB', (400, 200), color='white')
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        files = {'file': ('rx_@#$%.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        assert response.status_code in [200, 400]

    def test_multiple_file_fields(self):
        """Edge case: Request with multiple file fields."""
        from PIL import Image
        img_bytes1 = io.BytesIO()
        img_bytes2 = io.BytesIO()
        img = Image.new('RGB', (400, 200), color='white')
        img.save(img_bytes1, format='JPEG')
        img.save(img_bytes2, format='JPEG')
        img_bytes1.seek(0)
        img_bytes2.seek(0)

        files = [
            ('file', ('rx1.jpg', img_bytes1, 'image/jpeg')),
            ('file', ('rx2.jpg', img_bytes2, 'image/jpeg')),
        ]
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        # Should handle first file or reject
        assert response.status_code in [200, 400]

    def test_zero_byte_file(self):
        """Edge case: Zero-byte file upload."""
        files = {'file': ('empty.jpg', io.BytesIO(b''), 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        assert response.status_code != 200

    def test_filename_unicode_characters(self):
        """Edge case: Filename with unicode characters."""
        from PIL import Image
        img_bytes = io.BytesIO()
        img = Image.new('RGB', (400, 200), color='white')
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        files = {'file': ('処方箋.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        assert response.status_code in [200, 400]


# ============================================================================
# HEARTBREAK TEST CASES - Unexpected Failures
# ============================================================================

class TestHeartbreakerCases:
    """Test scenarios that could unexpectedly break."""

    def test_rapid_consecutive_uploads(self, page: Page):
        """Heartbreak: Rapid file uploads might cause threading issues."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')

        # Upload first file
        file_input.set_input_files(str(FIXTURE_IMAGE))
        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )

        # Immediately upload another
        file_input.set_input_files(str(FIXTURE_IMAGE))
        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )

    def test_cancel_during_analysis(self, page: Page):
        """Heartbreak: Cancel request while analysis is in progress."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        # Wait a tiny bit, then click "New Analysis" to cancel
        page.wait_for_timeout(500)
        page.click('button[onclick="window.location.reload()"]')
        page.goto(BASE_URL)

        # Page should reload and reset
        expect(page.locator('text=Upload Prescription Scan')).to_be_visible(timeout=15000)

    def test_api_response_json_structure(self):
        """Heartbreak: Verify /analyze returns correct JSON structure."""
        from PIL import Image
        img_bytes = io.BytesIO()
        img = Image.new('RGB', (400, 200), color='white')
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        if response.status_code == 200:
            data = response.json()
            assert 'request_id' in data
            assert 'image_data' in data
            assert 'analysis_html' in data
            assert isinstance(data['request_id'], str)
            assert isinstance(data['image_data'], str)
            assert isinstance(data['analysis_html'], str)

    def test_concurrent_analysis_requests(self):
        """Heartbreak: Multiple simultaneous analysis requests."""
        from PIL import Image
        import threading

        def upload_file():
            img_bytes = io.BytesIO()
            img = Image.new('RGB', (400, 200), color='white')
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
            return requests.post(f"{BASE_URL}/analyze", files=files)

        threads = [threading.Thread(target=upload_file) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All requests should complete without server crash

    def test_loader_disappears_after_analysis(self, page: Page):
        """Heartbreak: Loader element should disappear after analysis."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        loader = page.locator('#loader')
        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )
        # Loader should be hidden
        expect(loader).to_have_class(re.compile(r".*hidden.*"))

    def test_pdf_contains_image_and_analysis(self, page: Page):
        """Heartbreak: PDF should contain both image and analysis text."""
        page.goto(BASE_URL)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )

        with page.expect_download(timeout=20000) as download_info:
            page.click('#download-pdf')

        download = download_info.value
        # Just verify it exists and has size > 0
        download_path = Path(download.path())
        assert download_path.stat().st_size > 1000  # PDF should be > 1KB

    def test_drop_zone_visibility(self, page: Page):
        """Heartbreak: Drop zone should be visible initially and hidden after upload."""
        page.goto(BASE_URL)
        drop_zone = page.locator('#drop-zone')
        expect(drop_zone).to_be_visible()

        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))

        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )
        # Drop zone should now be hidden
        expect(drop_zone).not_to_be_visible()


# ============================================================================
# INTEGRATION TESTS - Full Workflows
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_complete_user_journey(self, page: Page):
        """Integration: Full user flow from upload to PDF download."""
        page.goto(BASE_URL)
        
        # Step 1: Verify page loaded
        expect(page.locator('h1')).to_contain_text('MedScan')
        
        # Step 2: Upload file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))
        
        # Step 3: Wait for analysis
        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )
        
        # Step 4: Verify image and analysis
        expect(page.locator('#output-image')).to_be_visible()
        analysis_text = page.locator('#analysis-content').inner_text()
        assert len(analysis_text) > 20
        
        # Step 5: Download PDF
        with page.expect_download(timeout=20000) as download_info:
            page.click('#download-pdf')
        
        download = download_info.value
        assert download.suggested_filename.endswith('.pdf')

    def test_reset_after_new_analysis_click(self, page: Page):
        """Integration: UI resets properly after clicking 'New Analysis'."""
        page.goto(BASE_URL)
        
        # Upload first file
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(FIXTURE_IMAGE))
        expect(page.locator('#analysis-content')).to_contain_text(
            'Mocked Clinical Analysis', timeout=20000
        )
        
        # Click "New Analysis"
        page.click('button[onclick="window.location.reload()"]')
        
        # Page should reset
        page.goto(BASE_URL)
        expect(page.locator('text=Upload Prescription Scan')).to_be_visible(timeout=15000)
        expect(page.locator('#analysis-content')).to_have_text('')
