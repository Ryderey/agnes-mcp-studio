import asyncio
import os
import tempfile
import threading
import unittest
from unittest import mock


class AgnesMediaMcpTests(unittest.TestCase):
    def test_image_payload_places_images_and_response_format_in_extra_body(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_image_payload(
            prompt="turn this into a watercolor poster",
            model="agnes-image-test",
            size="1024x1024",
            response_format="url",
            image_urls=["https://example.test/input.png"],
            extra_body={"strength": 0.65},
        )

        self.assertEqual(payload["model"], "agnes-image-test")
        self.assertEqual(payload["prompt"], "turn this into a watercolor poster")
        self.assertEqual(payload["size"], "1024x1024")
        self.assertNotIn("tags", payload)
        self.assertNotIn("response_format", payload)
        self.assertEqual(
            payload["extra_body"],
            {
                "strength": 0.65,
                "response_format": "url",
                "image": ["https://example.test/input.png"],
            },
        )

    def test_image_payload_supports_ratio_and_return_base64(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_image_payload(
            prompt="a futuristic city",
            model="agnes-image-2.1-flash",
            size="2K",
            ratio="16:9",
            return_base64=True,
        )

        self.assertEqual(payload["model"], "agnes-image-2.1-flash")
        self.assertEqual(payload["size"], "2K")
        self.assertEqual(payload["ratio"], "16:9")
        self.assertTrue(payload["return_base64"])
        self.assertNotIn("extra_body", payload)

    def test_image_payload_does_not_include_n_or_quality(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_image_payload(
            prompt="simple image",
            model="agnes-image-test",
            size="1024x1024",
        )

        self.assertNotIn("n", payload)
        self.assertNotIn("quality", payload)
        self.assertNotIn("tags", payload)

    def test_image_edit_rejects_mask_without_api_call(self):
        import agnes_media_mcp.server as agnes

        with mock.patch.object(agnes, "_request_json") as request_json:
            result = agnes._agnes_image_edit_impl(
                prompt="replace the sky",
                image_paths=["https://example.test/source.png"],
                mask_path="mask.png",
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "unsupported_parameter")
        request_json.assert_not_called()

    def test_image_success_omits_raw_and_data_url(self):
        import agnes_media_mcp.server as agnes

        response = {
            "created": 1780000000,
            "data": [{"url": "data:image/png;base64,iVBORw0KGgo="}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict(os.environ, {"AGNES_OUTPUT_DIR": temp_dir}, clear=False):
                with mock.patch.object(agnes, "_request_json", return_value=(True, response)):
                    result = agnes._agnes_image_generate_impl("a validation image")

        self.assertTrue(result["ok"])
        self.assertNotIn("raw", result)
        self.assertEqual(result["image_urls"], [])
        self.assertEqual(len(result["local_paths"]), 1)

    def test_provider_error_body_is_preserved(self):
        import agnes_media_mcp.server as agnes

        error = {
            "ok": False,
            "error": {
                "code": "http_error",
                "message": "provider error",
                "details": {"status_code": 400, "body": {"message": "invalid size"}},
            },
        }
        with mock.patch.object(agnes, "_request_json", return_value=(False, error)):
            result = agnes._agnes_image_generate_impl("a validation image")

        self.assertEqual(result, error)

    def test_video_payload_converts_duration_and_aligns_to_8n_plus_1(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_video_payload(
            prompt="slow dolly shot of a porcelain vase",
            model="agnes-video-test",
            duration=5.0,
            frame_rate=24,
            resolution="720p",
            aspect_ratio="16:9",
            extra_body={"seed": 123},
        )

        self.assertEqual(payload["model"], "agnes-video-test")
        self.assertEqual(payload["prompt"], "slow dolly shot of a porcelain vase")
        # 5.0 * 24 = 120, aligned to 8n+1 -> 121
        self.assertEqual(payload["num_frames"], 121)
        self.assertEqual(payload["frame_rate"], 24)
        self.assertEqual(payload["width"], 1280)
        self.assertEqual(payload["height"], 720)
        self.assertEqual(payload["extra_body"], {"seed": 123})

    def test_video_payload_num_frames_capped_at_441(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_video_payload(
            prompt="very long video",
            model="agnes-video-test",
            duration=30.0,
            frame_rate=24,
            resolution="720p",
            aspect_ratio="16:9",
        )

        # 30 * 24 = 720, capped at 441
        self.assertEqual(payload["num_frames"], 441)

    def test_video_payload_uses_image_and_mode(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_video_payload(
            prompt="animate this image",
            model="agnes-video-test",
            duration=5.0,
            frame_rate=24,
            resolution="720p",
            aspect_ratio="16:9",
            image="https://example.test/input.png",
            mode="ti2vid",
        )

        self.assertEqual(payload["image"], "https://example.test/input.png")
        self.assertEqual(payload["mode"], "ti2vid")
        self.assertNotIn("extra_body", payload)

    def test_video_payload_keyframes_merges_into_extra_body(self):
        import agnes_media_mcp.server as agnes

        payload = agnes._build_video_payload(
            prompt="smooth transition between keyframes",
            model="agnes-video-test",
            duration=5.0,
            frame_rate=24,
            resolution="720p",
            aspect_ratio="16:9",
            mode="keyframes",
            extra_body={"image": ["https://a.png", "https://b.png"]},
        )

        self.assertEqual(
            payload["extra_body"],
            {"mode": "keyframes", "image": ["https://a.png", "https://b.png"]},
        )
        self.assertNotIn("image", payload)
        self.assertNotIn("mode", payload)

    def test_video_payload_rejects_frame_rate_above_60(self):
        import agnes_media_mcp.server as agnes

        with self.assertRaises(ValueError) as ctx:
            agnes._build_video_payload(
                prompt="too fast",
                model="agnes-video-test",
                duration=5.0,
                frame_rate=61,
                resolution="720p",
                aspect_ratio="16:9",
            )

        self.assertIn("60", str(ctx.exception))

    def test_video_status_extracts_url_from_metadata(self):
        import agnes_media_mcp.server as agnes

        response = {
            "id": "task-123",
            "video_id": "video-456",
            "status": "completed",
            "progress": 100,
            "seconds": "5.0",
            "size": "1152x768",
            "metadata": {
                "url": "https://cdn.example.test/video.mp4",
            },
        }

        with mock.patch.dict(os.environ, {"AGNES_API_KEY": "test-key"}, clear=False):
            with mock.patch.object(agnes, "_request_json", return_value=(True, response)):
                result = agnes._agnes_video_status_impl("video-456")

        self.assertTrue(result["ok"])
        self.assertEqual(result["video_id"], "video-456")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["video_url"], "https://cdn.example.test/video.mp4")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(result["seconds"], "5.0")
        self.assertEqual(result["size"], "1152x768")
        self.assertNotIn("raw", result)

    def test_video_status_uses_agnesapi_endpoint(self):
        import agnes_media_mcp.server as agnes

        response = {"id": "task-1", "video_id": "vid-1", "status": "queued"}

        with mock.patch.dict(os.environ, {"AGNES_API_KEY": "test-key"}, clear=False):
            with mock.patch.object(agnes, "_request_json", return_value=(True, response)) as mock_req:
                agnes._agnes_video_status_impl("vid-1")

        mock_req.assert_called_once_with(
            "GET",
            "/agnesapi?video_id=vid-1",
            base_url="https://api.agnes-ai.cn",
        )

    def test_video_status_full_url_has_no_v1_prefix(self):
        """The agnesapi query endpoint lives at the domain root, not under /v1."""
        import agnes_media_mcp.server as agnes

        response = {"id": "task-2", "video_id": "vid-2", "status": "completed"}
        captured_urls = []

        original_request_json = agnes._request_json

        def spy_request_json(method, path, **kwargs):
            base = kwargs.get("base_url") or agnes._base_url()
            captured_urls.append(f"{base}{path}")
            return True, response

        with mock.patch.dict(os.environ, {"AGNES_API_KEY": "test-key"}, clear=False):
            with mock.patch.object(agnes, "_request_json", side_effect=spy_request_json):
                agnes._agnes_video_status_impl("vid-2")

        self.assertEqual(len(captured_urls), 1)
        self.assertEqual(
            captured_urls[0],
            "https://api.agnes-ai.cn/agnesapi?video_id=vid-2",
        )
        self.assertNotIn("/v1/", captured_urls[0])

    def test_video_submit_returns_video_id(self):
        import agnes_media_mcp.server as agnes

        response = {
            "id": "task-abc",
            "task_id": "task-abc",
            "video_id": "video-xyz",
            "status": "queued",
            "progress": 0,
            "seconds": "5.0",
            "size": "1152x768",
        }

        with mock.patch.dict(os.environ, {"AGNES_API_KEY": "test-key"}, clear=False):
            with mock.patch.object(agnes, "_request_json", return_value=(True, response)):
                result = agnes._agnes_video_submit_impl("a cat walking")

        self.assertTrue(result["ok"])
        self.assertEqual(result["task_id"], "task-abc")
        self.assertEqual(result["video_id"], "video-xyz")
        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["progress"], 0)
        self.assertNotIn("raw", result)

    def test_video_wait_times_out_with_last_response(self):
        import agnes_media_mcp.server as agnes

        status_response = {
            "ok": True,
            "task_id": "task-123",
            "video_id": "video-123",
            "status": "in_progress",
            "raw": {"status": "in_progress"},
        }

        with mock.patch.object(
            agnes, "_agnes_video_status_impl", return_value=status_response
        ):
            with mock.patch.object(agnes.time, "sleep"):
                result = agnes._agnes_video_wait_impl(
                    "video-123",
                    timeout_seconds=0.01,
                    poll_interval_seconds=0.01,
                    download=False,
                )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "timeout")
        self.assertEqual(result["video_id"], "video-123")
        self.assertEqual(result["last_response"], status_response)

    def test_video_wait_retries_transient_status_errors(self):
        import agnes_media_mcp.server as agnes

        rate_limited = {
            "ok": False,
            "error": {
                "code": "http_error",
                "message": "Agnes returned a non-success HTTP response.",
                "details": {"status_code": 429},
            },
        }
        completed = {
            "ok": True,
            "task_id": "task-123",
            "video_id": "video-123",
            "status": "completed",
            "video_url": "https://cdn.example.test/video.mp4",
            "raw": {"status": "completed"},
        }

        with mock.patch.object(
            agnes, "_agnes_video_status_impl", side_effect=[rate_limited, completed]
        ) as status_impl:
            with mock.patch.object(agnes.time, "sleep") as sleep:
                result = agnes._agnes_video_wait_impl(
                    "video-123",
                    timeout_seconds=20,
                    poll_interval_seconds=10,
                    download=False,
                )

        self.assertTrue(result["ok"])
        self.assertNotIn("raw", result)
        self.assertEqual(status_impl.call_count, 2)
        sleep.assert_called_once_with(10)

    def test_video_generate_omits_submit_result_on_success_and_keeps_it_on_error(self):
        import agnes_media_mcp.server as agnes

        submit_result = {
            "ok": True,
            "video_id": "video-123",
            "status": "queued",
            "raw": {"video_id": "video-123", "status": "queued"},
        }
        with mock.patch.object(
            agnes, "_agnes_video_submit_impl", return_value=submit_result
        ):
            with mock.patch.object(
                agnes,
                "_agnes_video_wait_impl",
                return_value={"ok": True, "video_id": "video-123", "status": "completed"},
            ):
                success = agnes._agnes_video_generate_impl("a cat walking")
            with mock.patch.object(
                agnes,
                "_agnes_video_wait_impl",
                return_value={"ok": False, "error": {"code": "timeout"}},
            ):
                failure = agnes._agnes_video_generate_impl("a cat walking")

        self.assertNotIn("submit_result", success)
        self.assertEqual(failure["submit_result"], submit_result)

    def test_long_video_tools_run_outside_event_loop_thread(self):
        import agnes_media_mcp.server as agnes

        async def call(tool):
            event_loop_thread = threading.get_ident()
            result = await tool("value", download=False)
            return event_loop_thread, result["thread_id"]

        cases = (
            (agnes.agnes_video_wait, "_agnes_video_wait_impl"),
            (agnes.agnes_video_generate, "_agnes_video_generate_impl"),
        )
        for tool, implementation in cases:
            with self.subTest(tool=tool.__name__):
                with mock.patch.object(
                    agnes,
                    implementation,
                    side_effect=lambda *args, **kwargs: {"thread_id": threading.get_ident()},
                ):
                    event_loop_thread, worker_thread = asyncio.run(call(tool))

                self.assertNotEqual(event_loop_thread, worker_thread)

    def test_output_directories_are_created_from_env(self):
        import agnes_media_mcp.server as agnes

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict(os.environ, {"AGNES_OUTPUT_DIR": temp_dir}, clear=False):
                image_dir = agnes._ensure_output_dir("images")
                video_dir = agnes._ensure_output_dir("videos")

        self.assertEqual(image_dir.name, "images")
        self.assertEqual(video_dir.name, "videos")

    def test_align_num_frames(self):
        import agnes_media_mcp.server as agnes

        # Exact 8n+1 values pass through
        self.assertEqual(agnes._align_num_frames(1), 1)
        self.assertEqual(agnes._align_num_frames(121), 121)
        self.assertEqual(agnes._align_num_frames(441), 441)
        # Non-aligned values snap to nearest
        self.assertEqual(agnes._align_num_frames(120), 121)
        self.assertEqual(agnes._align_num_frames(119), 121)
        self.assertEqual(agnes._align_num_frames(80), 81)
        # Over max capped at 441
        self.assertEqual(agnes._align_num_frames(500), 441)
        self.assertEqual(agnes._align_num_frames(1000), 441)

    def test_sanitize_filename_blocks_traversal(self):
        import agnes_media_mcp.server as agnes

        # Normal filenames pass through
        self.assertEqual(agnes._sanitize_filename("photo.png"), "photo.png")
        self.assertEqual(agnes._sanitize_filename("my-video.mp4"), "my-video.mp4")
        # None / empty returns None
        self.assertIsNone(agnes._sanitize_filename(None))
        self.assertIsNone(agnes._sanitize_filename(""))
        # Absolute paths rejected
        self.assertIsNone(agnes._sanitize_filename("/etc/passwd"))
        self.assertIsNone(agnes._sanitize_filename("C:\\Windows\\evil.exe"))
        # Traversal components stripped to basename
        self.assertEqual(agnes._sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(agnes._sanitize_filename("..\\..\\evil.png"), "evil.png")
        self.assertEqual(agnes._sanitize_filename("sub/dir/file.png"), "file.png")
        # Pure traversal rejected
        self.assertIsNone(agnes._sanitize_filename(".."))
        self.assertIsNone(agnes._sanitize_filename("."))
        # Windows-reserved names and trailing spaces/dots rejected on every OS
        for filename in ("CON.png", "nul", "PrN.txt", "AUX", "COM1.mp4", "LPT9"):
            with self.subTest(filename=filename):
                self.assertIsNone(agnes._sanitize_filename(filename))
        self.assertIsNone(agnes._sanitize_filename("photo.png."))
        self.assertIsNone(agnes._sanitize_filename("photo.png "))


if __name__ == "__main__":
    unittest.main()
