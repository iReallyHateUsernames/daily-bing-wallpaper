# -*- coding: utf-8 -*-
"""
Unit tests for Bing Wallpaper Downloader
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Import functions to test
from bing_wallpaper import (
    load_config,
    sanitize,
    extract_slug,
    date_from_img,
    build_filename,
    guess_ext_from_ct,
    build_candidate_urls
)


class TestConfigLoading:
    """Test configuration file loading"""
    
    def test_load_config_file_not_exists(self, monkeypatch):
        """Test loading config when file doesn't exist - should create default config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_config = Path(tmpdir) / "nonexistent" / "config.json"
            monkeypatch.setattr("bing_wallpaper.CONFIG_FILE", fake_config)
            
            config = load_config()
            # Should return default config with all required fields
            assert "download_folder" in config
            assert "market" in config
            assert "fallback_markets" in config
            assert "resolution" in config
            assert "image_count" in config
            assert "set_latest" in config
            assert "file_mode" in config
            assert "name_mode" in config
            # Verify the config file was created
            assert fake_config.exists()
    
    def test_load_config_valid_json(self, monkeypatch):
        """Test loading valid config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            config_file = config_dir / "config.json"
            
            test_config = {
                "download_folder": "C:\\Test\\Path",
                "market": "en-US",
                "image_count": 5
            }
            config_file.write_text(json.dumps(test_config), encoding='utf-8')
            
            monkeypatch.setattr("bing_wallpaper.CONFIG_FILE", config_file)
            
            config = load_config()
            assert config == test_config
            assert config["market"] == "en-US"
            assert config["image_count"] == 5
    
    def test_load_config_invalid_json(self, monkeypatch):
        """Test loading invalid JSON returns empty dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            config_file = config_dir / "config.json"
            
            config_file.write_text("invalid json {{{", encoding='utf-8')
            
            monkeypatch.setattr("bing_wallpaper.CONFIG_FILE", config_file)
            
            config = load_config()
            assert config == {}


class TestSanitize:
    """Test filename sanitization"""
    
    def test_sanitize_removes_invalid_chars(self):
        """Test that invalid filename characters are replaced"""
        result = sanitize('test<>:"/\\|?*file')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
    
    def test_sanitize_normal_string(self):
        """Test that normal strings are unchanged"""
        result = sanitize('normal_filename_123')
        assert result == 'normal_filename_123'
    
    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is removed"""
        result = sanitize('  test file  ')
        assert result == 'test file'


class TestExtractSlug:
    """Test slug extraction from image metadata"""
    
    def test_extract_slug_with_ohr(self):
        """Test extracting slug from OHR-style URL"""
        img = {"urlbase": "/th?id=OHR.Waterfall_DE-de12345"}
        result = extract_slug(img)
        assert result == "Waterfall"
    
    def test_extract_slug_without_ohr(self):
        """Test extracting slug from non-OHR URL"""
        img = {"urlbase": "/th?id=something/MyImage_test"}
        result = extract_slug(img)
        # Should return part after last /
        assert "MyImage" in result
    
    def test_extract_slug_with_underscore(self):
        """Test that slug stops at first underscore"""
        img = {"urlbase": "/th?id=OHR.TestImage_EN_US_1234"}
        result = extract_slug(img)
        assert result == "TestImage"
    
    def test_extract_slug_empty_urlbase(self):
        """Test handling of empty urlbase"""
        img = {"urlbase": ""}
        result = extract_slug(img)
        assert result == "unknown"


class TestDateFromImg:
    """Test date extraction from image metadata"""
    
    def test_date_from_img_valid(self):
        """Test valid date parsing"""
        img = {"startdate": "20250117"}
        result = date_from_img(img)
        assert result == "2025-01-17"
    
    def test_date_from_img_invalid(self):
        """Test invalid date returns 'unknown' when no index provided"""
        img = {"startdate": "invalid"}
        result = date_from_img(img)
        # Should return 'unknown' when parsing fails and no fallback index
        assert result == "unknown"
    
    def test_date_from_img_invalid_with_index(self):
        """Test invalid date uses fallback index to estimate date"""
        from datetime import datetime, timedelta
        img = {"startdate": "invalid"}
        result = date_from_img(img, fallback_idx=2)
        # Should estimate date as 2 days ago
        expected = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_date_from_img_missing(self):
        """Test missing date field returns 'unknown' when no index provided"""
        img = {}
        result = date_from_img(img)
        # Should return 'unknown' when no startdate and no fallback index
        assert result == "unknown"
    
    def test_date_from_img_missing_with_index(self):
        """Test missing date uses fallback index to estimate date"""
        from datetime import datetime, timedelta
        img = {}
        result = date_from_img(img, fallback_idx=0)
        # Should estimate date as today
        expected = datetime.utcnow().strftime("%Y-%m-%d")
        assert result == expected


class TestGuessExtFromCt:
    """Test content-type to extension conversion"""
    
    def test_guess_ext_jpeg(self):
        """Test JPEG content type"""
        assert guess_ext_from_ct("image/jpeg") == ".jpg"
        assert guess_ext_from_ct("image/jpg") == ".jpg"
    
    def test_guess_ext_png(self):
        """Test PNG content type"""
        assert guess_ext_from_ct("image/png") == ".png"
    
    def test_guess_ext_webp(self):
        """Test WebP content type"""
        assert guess_ext_from_ct("image/webp") == ".webp"
    
    def test_guess_ext_bmp(self):
        """Test BMP content type"""
        assert guess_ext_from_ct("image/bmp") == ".bmp"
    
    def test_guess_ext_unknown(self):
        """Test unknown content type defaults to jpg"""
        assert guess_ext_from_ct("image/unknown") == ".jpg"
        assert guess_ext_from_ct(None) == ".jpg"
        assert guess_ext_from_ct("") == ".jpg"


class TestBuildFilename:
    """Test filename building from image metadata"""
    
    def test_build_filename_slug_mode(self):
        """Test filename generation in slug mode"""
        img = {
            "urlbase": "/th?id=OHR.TestImage_EN_US",
            "startdate": "20250117"
        }
        result = build_filename(img, "image/jpeg", name_mode="slug")
        assert result == "2025-01-17_TestImage.jpg"
    
    def test_build_filename_title_mode(self):
        """Test filename generation in title mode"""
        img = {
            "title": "Beautiful Sunset",
            "startdate": "20250117"
        }
        result = build_filename(img, "image/jpeg", name_mode="title")
        assert result == "2025-01-17_Beautiful Sunset.jpg"
    
    def test_build_filename_sanitizes(self):
        """Test that filename is sanitized"""
        img = {
            "title": "Test<>:File",
            "startdate": "20250117"
        }
        result = build_filename(img, "image/jpeg", name_mode="title")
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
    
    def test_build_filename_png(self):
        """Test filename with PNG extension"""
        img = {
            "urlbase": "/th?id=OHR.TestImage",
            "startdate": "20250117"
        }
        result = build_filename(img, "image/png", name_mode="slug")
        assert result.endswith(".png")


class TestBuildCandidateUrls:
    """Test URL candidate generation"""
    
    def test_build_candidate_urls_basic(self):
        """Test basic URL generation"""
        img = {
            "url": "/test.jpg",
            "urlbase": "/th?id=OHR.Test"
        }
        preferred_res = ["UHD", "1920x1080"]
        
        urls = build_candidate_urls(img, preferred_res)
        
        assert len(urls) > 0
        assert any("test.jpg" in url for url in urls)
    
    def test_build_candidate_urls_with_resolutions(self):
        """Test URL generation includes all resolutions"""
        img = {
            "urlbase": "/th?id=OHR.Test"
        }
        preferred_res = ["3840x2160", "1920x1080"]
        
        urls = build_candidate_urls(img, preferred_res)
        
        # Should include URLs with resolution suffixes
        assert any("3840x2160" in url for url in urls)
        assert any("1920x1080" in url for url in urls)
    
    def test_build_candidate_urls_includes_extensions(self):
        """Test URL generation includes multiple extensions"""
        img = {
            "urlbase": "/th?id=OHR.Test"
        }
        preferred_res = ["1920x1080"]
        
        urls = build_candidate_urls(img, preferred_res)
        
        # Should try multiple extensions
        url_string = " ".join(urls)
        assert ".jpg" in url_string
        assert ".png" in url_string
        assert ".webp" in url_string
    
    def test_build_candidate_urls_deduplicates(self):
        """Test that duplicate URLs are removed"""
        img = {
            "url": "/test.jpg",
            "urlbase": "/test"
        }
        preferred_res = ["UHD"]
        
        urls = build_candidate_urls(img, preferred_res)
        
        # Check no duplicates
        assert len(urls) == len(set(urls))
    
    def test_build_candidate_urls_no_url(self):
        """Test URL generation with only urlbase"""
        img = {
            "urlbase": "/th?id=OHR.Test"
        }
        preferred_res = ["1920x1080"]
        
        urls = build_candidate_urls(img, preferred_res)
        
        assert len(urls) > 0
        assert all("bing.com" in url for url in urls)


class TestIntegration:
    """Integration tests for main workflow"""
    
    @mock.patch.dict(os.environ, {"APPDATA": str(Path.cwd() / "test_appdata")})
    def test_config_file_location(self):
        """Test that config file path is constructed correctly"""
        # Import after patching environment
        import importlib
        import bing_wallpaper
        importlib.reload(bing_wallpaper)
        
        expected_path = Path.cwd() / "test_appdata" / "BingWallpaperDownloader" / "config.json"
        assert str(bing_wallpaper.CONFIG_FILE) == str(expected_path)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
