"""
Unit tests for CampaignExporter module in omnipost_social_engine.
"""

import json
import os
import tempfile
import pytest

from omnipost_social_engine.campaign_exporter import (
    Campaign,
    CampaignExporter,
    Post,
    PLATFORM_LIMITS,
)


class TestPostAndCampaignModels:
    def test_post_creation_and_dict(self):
        post = Post(
            content="Hello world! #test",
            platform="twitter",
            scheduled_time="2026-09-20T10:00:00Z",
            hashtags=["test", "python"],
            media_urls=["https://example.com/image.png"],
            thread_position=1,
            total_thread_posts=2,
            status="scheduled",
            notes="Morning post",
        )
        data = post.to_dict()
        assert data["content"] == "Hello world! #test"
        assert data["platform"] == "twitter"
        assert data["scheduled_time"] == "2026-09-20T10:00:00Z"
        assert data["hashtags"] == ["test", "python"]
        assert data["media_urls"] == ["https://example.com/image.png"]
        assert data["thread_position"] == 1
        assert data["status"] == "scheduled"

        # Test from_dict
        restored = Post.from_dict(data)
        assert restored.content == post.content
        assert restored.platform == post.platform
        assert restored.hashtags == post.hashtags

    def test_post_from_dict_string_conversions(self):
        data = {
            "text": "Alternative text key",
            "hashtags": "tag1, tag2, tag3",
            "media": "https://img1.png, https://img2.png",
            "date": "2026-09-20 12:00",
        }
        p = Post.from_dict(data)
        assert p.content == "Alternative text key"
        assert p.hashtags == ["tag1", "tag2", "tag3"]
        assert p.media_urls == ["https://img1.png", "https://img2.png"]
        assert p.scheduled_time == "2026-09-20 12:00"

    def test_campaign_add_post_and_to_dict(self):
        camp = Campaign(name="Q3 Growth Campaign", description="Scaling tests")
        p1 = camp.add_post({"content": "First post", "platform": "twitter"})
        assert p1.id == "post_1"
        assert len(camp.posts) == 1

        p2 = Post(content="Second post", platform="linkedin", id="custom_id")
        camp.add_post(p2)
        assert len(camp.posts) == 2

        d = camp.to_dict()
        assert d["name"] == "Q3 Growth Campaign"
        assert d["total_posts"] == 2
        assert len(d["posts"]) == 2

        restored_camp = Campaign.from_dict(d)
        assert restored_camp.name == "Q3 Growth Campaign"
        assert len(restored_camp.posts) == 2


class TestCampaignExporterParsing:
    def test_parse_campaign_from_instance(self):
        c = Campaign(name="Direct Instance")
        parsed = CampaignExporter.parse_campaign(c)
        assert parsed is c

    def test_parse_campaign_from_dict(self):
        d = {"name": "From Dict", "posts": [{"content": "P1"}]}
        parsed = CampaignExporter.parse_campaign(d)
        assert parsed.name == "From Dict"
        assert len(parsed.posts) == 1

    def test_parse_campaign_from_list(self):
        posts = [{"content": "Item 1"}, {"content": "Item 2"}]
        parsed = CampaignExporter.parse_campaign(posts)
        assert len(parsed.posts) == 2
        assert parsed.posts[0].id == "post_1"

    def test_parse_campaign_from_json_string(self):
        json_str = json.dumps({"name": "JSON Str Campaign", "posts": [{"content": "JSON post"}]})
        parsed = CampaignExporter.parse_campaign(json_str)
        assert parsed.name == "JSON Str Campaign"
        assert parsed.posts[0].content == "JSON post"

    def test_parse_campaign_from_raw_string(self):
        raw = "Just a single standalone post"
        parsed = CampaignExporter.parse_campaign(raw)
        assert len(parsed.posts) == 1
        assert parsed.posts[0].content == raw

    def test_parse_campaign_from_file(self):
        sample = CampaignExporter.create_sample_campaign("File Test")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(CampaignExporter.to_json(sample))
            tmp_path = f.name

        try:
            parsed = CampaignExporter.parse_campaign(tmp_path)
            assert parsed.name == "File Test"
            assert len(parsed.posts) == len(sample.posts)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_parse_invalid_type_raises(self):
        with pytest.raises(ValueError):
            CampaignExporter.parse_campaign(12345)  # type: ignore


class TestCampaignExporterFormats:
    @pytest.fixture
    def sample_campaign(self):
        return CampaignExporter.create_sample_campaign("Sample Launch")

    def test_to_json(self, sample_campaign):
        json_str = CampaignExporter.to_json(sample_campaign)
        data = json.loads(json_str)
        assert data["name"] == "Sample Launch"
        assert len(data["posts"]) >= 3
        assert "version" in data

    def test_to_csv_buffer(self, sample_campaign):
        csv_str = CampaignExporter.to_csv(sample_campaign, preset="buffer")
        lines = csv_str.strip().split("\r\n") if "\r\n" in csv_str else csv_str.strip().split("\n")
        assert len(lines) >= 4
        assert "Date,Text,Media,Campaign" in lines[0]
        # Check that post content is in CSV
        assert "Most developers" in csv_str

    def test_to_csv_hootsuite(self, sample_campaign):
        csv_str = CampaignExporter.to_csv(sample_campaign, preset="hootsuite")
        assert "Date (MM/DD/YYYY hh:mm),Post,Link" in csv_str
        assert "Most developers" in csv_str

    def test_to_csv_typefully(self, sample_campaign):
        csv_str = CampaignExporter.to_csv(sample_campaign, preset="typefully")
        assert "Scheduled Date,Content,Platform,Thread Position,Notes" in csv_str
        assert "twitter" in csv_str

    def test_to_csv_generic(self, sample_campaign):
        csv_str = CampaignExporter.to_csv(sample_campaign, preset="generic")
        assert "ID,Title,Platform,ScheduledTime,Content,Hashtags,MediaURLs,ThreadPosition,Status,Notes" in csv_str
        assert "post_1" in csv_str

    def test_to_markdown_calendar_table(self, sample_campaign):
        md = CampaignExporter.to_markdown(sample_campaign, view="calendar")
        assert "# 📅 Campaign Schedule: Sample Launch" in md
        assert "| # | Scheduled Time | Platform | Status | Preview | Chars |" in md
        assert "Twitter" in md

    def test_to_markdown_cards(self, sample_campaign):
        md = CampaignExporter.to_markdown(sample_campaign, view="cards")
        assert "### Post 1: Twitter" in md
        assert "```text" in md
        assert "**Hashtags**:" in md

    def test_to_markdown_checklist(self, sample_campaign):
        md = CampaignExporter.to_markdown(sample_campaign, view="checklist")
        assert "## 📋 Execution Checklist" in md
        assert "- [ ]" in md

    def test_to_raw_text(self, sample_campaign):
        raw = CampaignExporter.to_raw_text(sample_campaign)
        assert "POST #1 | PLATFORM: TWITTER" in raw
        assert "POST #2 | PLATFORM: TWITTER" in raw

    def test_export_router(self, sample_campaign):
        assert "{" in CampaignExporter.export(sample_campaign, format="json")
        assert "Date" in CampaignExporter.export(sample_campaign, format="csv", preset="buffer")
        assert "# 📅" in CampaignExporter.export(sample_campaign, format="md")
        assert "POST #1" in CampaignExporter.export(sample_campaign, format="txt")

        with pytest.raises(ValueError):
            CampaignExporter.export(sample_campaign, format="unsupported_format")

    def test_export_to_file(self, sample_campaign):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = os.path.join(tmpdir, "subdir", "camp.json")
            CampaignExporter.export_to_file(sample_campaign, out_json)
            assert os.path.exists(out_json)
            with open(out_json, "r", encoding="utf-8") as f:
                content = json.load(f)
                assert content["name"] == "Sample Launch"

            out_csv = os.path.join(tmpdir, "camp.csv")
            CampaignExporter.export_to_file(sample_campaign, out_csv)
            assert os.path.exists(out_csv)

            out_md = os.path.join(tmpdir, "camp.md")
            CampaignExporter.export_to_file(sample_campaign, out_md)
            assert os.path.exists(out_md)
