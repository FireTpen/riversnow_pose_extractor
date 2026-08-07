# -*- coding: utf-8 -*-
"""Gradio 界面与风险提示逻辑（含中英文 i18n）。"""
import os
import tempfile

import gradio as gr

# ---------------------------------------------------------------------------
# i18n 文案表
# ---------------------------------------------------------------------------
LANGS = {"中文": "zh", "English": "en"}
DEFAULT_LANG = "zh"

TEXT = {
    "zh": {
        "title_md": "# 人物动作视频 → 黑底骨架视频 + 关键点 JSON\n"
                    "使用 MediaPipe Pose（33 个身体关键点）+ Hands（每只手 21 个手指关键点），"
                    "适用于 AI 视频生成（ControlNet OpenPose 风格）。",
        "video_in_label": "上传视频（mp4/mov 等）",
        "info_placeholder": "上传后显示源视频信息",
        "params_md": "### 参数",
        "preset_label": "输出分辨率预设",
        "preset_source": "与源一致",
        "preset_custom": "自定义",
        "cust_w_label": "自定义宽",
        "cust_h_label": "自定义高",
        "start_label": "开始秒",
        "end_label": "结束秒（0=全长）",
        "complexity_label": "MediaPipe model_complexity（越大越准越慢）",
        "btn_label": "开始处理",
        "video_out_label": "骨架视频预览",
        "json_out_label": "关键点 JSON 下载",
        "fbx_btn_label": "导出 FBX 动画（实验）",
        "fbx_out_label": "FBX 动画下载",
        "thumb_btn": "缩略",
        "wide_btn": "宽屏",
        "full_btn": "全屏",
        "info_fmt": "分辨率: {width}x{height}　|　帧率: {fps:.2f} fps　|　"
                    "时长: {duration_sec:.2f} 秒　|　总帧数: {frame_count}",
        "read_fail": "读取视频失败: %s",
        "note_transcoded": "\n\nℹ️ 源视频编码（如 HEVC）浏览器无法直接预览，已自动转换为 H.264。",
        "err_no_video": "请先上传视频。",
        "err_custom_empty": "自定义分辨率不能为空。",
        "err_custom_positive": "自定义分辨率必须为正整数。",
        "err_clip_invalid": "裁剪区间非法：结束时间必须大于开始时间，且不超过视频总长 %.2f 秒。",
        "warn_clip_invalid_md": "❌ **裁剪区间非法**：结束时间必须大于开始时间，且不超过视频总长 %.2f 秒。",
        "warn_upscale": "⚠️ 输出分辨率(%dx%d)超过源分辨率(%dx%d)：放大不会增加细节，只会更慢。",
        "warn_pixels": "⚠️ 输出总像素(%dx%d)超过 1024x1024：处理会明显变慢。",
        "warn_long": "⚠️ 裁剪后时长 %.1f 秒，预计处理约 %d 帧，耗时较长，请耐心等待。",
        "info_frames": "ℹ️ 预计处理约 %d 帧（%.1f 秒）。",
        "progress_desc": "处理帧 %d/%d",
        "summary_done": "✅ 完成：写出 %d 帧，其中 %d 帧检出身体或手部关键点。",
        "summary_even": "（奇数宽/高已调整为偶数 %dx%d，以满足 H.264 编码要求）",
        "err_process_failed": "❌ 处理失败：%s",
        "err_no_json": "请先完成视频处理，生成关键点 JSON。",
        "fbx_exporting": "正在用 Blender 解算骨骼并导出 FBX…",
        "fbx_done": "✅ FBX 动画已导出（Mixamo 命名风格骨架，建议在游戏引擎中重定向）。",
        "err_fbx_failed": "❌ FBX 导出失败：%s",
    },
    "en": {
        "title_md": "# Motion Video → Black-Background Skeleton Video + Keypoints JSON\n"
                    "Powered by MediaPipe Pose (33 body landmarks) + Hands (21 finger landmarks "
                    "per hand). Designed for AI video generation (ControlNet OpenPose style).",
        "video_in_label": "Upload video (mp4/mov etc.)",
        "info_placeholder": "Source video info will appear here after upload",
        "params_md": "### Parameters",
        "preset_label": "Output resolution preset",
        "preset_source": "Same as source",
        "preset_custom": "Custom",
        "cust_w_label": "Custom width",
        "cust_h_label": "Custom height",
        "start_label": "Start (sec)",
        "end_label": "End (sec, 0 = full length)",
        "complexity_label": "MediaPipe model_complexity (higher = more accurate, slower)",
        "btn_label": "Start Processing",
        "video_out_label": "Skeleton video preview",
        "json_out_label": "Keypoints JSON download",
        "fbx_btn_label": "Export FBX Animation (Experimental)",
        "fbx_out_label": "FBX animation download",
        "thumb_btn": "Thumbnail",
        "wide_btn": "Wide",
        "full_btn": "Fullscreen",
        "info_fmt": "Resolution: {width}x{height}  |  FPS: {fps:.2f}  |  "
                    "Duration: {duration_sec:.2f} s  |  Frames: {frame_count}",
        "read_fail": "Failed to read video: %s",
        "note_transcoded": "\n\nℹ️ Source codec (e.g. HEVC) is not browser-playable; auto-converted to H.264.",
        "err_no_video": "Please upload a video first.",
        "err_custom_empty": "Custom resolution must not be empty.",
        "err_custom_positive": "Custom resolution must be positive integers.",
        "err_clip_invalid": "Invalid clip range: end time must be greater than start time "
                            "and within the total duration of %.2f s.",
        "warn_clip_invalid_md": "❌ **Invalid clip range**: end time must be greater than start "
                                "time and within the total duration of %.2f s.",
        "warn_upscale": "⚠️ Output resolution (%dx%d) exceeds source resolution (%dx%d): "
                        "upscaling adds no detail, only slows processing.",
        "warn_pixels": "⚠️ Output pixels (%dx%d) exceed 1024x1024: processing will be "
                       "noticeably slower.",
        "warn_long": "⚠️ Clipped duration is %.1f s (~%d frames). This will take a while, "
                     "please be patient.",
        "info_frames": "ℹ️ About %d frames to process (%.1f s).",
        "progress_desc": "Frame %d/%d",
        "summary_done": "✅ Done: wrote %d frames; body or hand landmarks detected in %d of them.",
        "summary_even": " (odd width/height rounded to even %dx%d for H.264 encoding)",
        "err_process_failed": "❌ Processing failed: %s",
        "err_no_json": "Process a video first to generate a keypoints JSON file.",
        "fbx_exporting": "Solving the skeleton and exporting FBX with Blender…",
        "fbx_done": "✅ FBX animation exported (Mixamo-style bone names; retarget in your engine).",
        "err_fbx_failed": "❌ FBX export failed: %s",
    },
}


def T(lang, key, *args):
    """查文案表；带 % 占位符的用 args 格式化。"""
    s = TEXT.get(lang, TEXT[DEFAULT_LANG])[key]
    return s % args if args else s


# 分辨率预设内部 key（不随语言变化）；显示名随语言生成 choices。
RESOLUTION_PRESETS = {
    "source": None,
    "512x512": (512, 512),
    "768x768": (768, 768),
    "1024x1024": (1024, 1024),
    "custom": "custom",
}


def preset_choices(lang):
    return [
        (T(lang, "preset_source"), "source"),
        ("512x512", "512x512"),
        ("768x768", "768x768"),
        ("1024x1024", "1024x1024"),
        (T(lang, "preset_custom"), "custom"),
    ]


def _fmt_info(info, lang):
    return T(lang, "info_fmt").format(**info)


def compute_warnings(video_info, preset, cust_w, cust_h, start_sec, end_sec, lang):
    """根据当前参数生成风险提示列表（返回 Markdown 文本）。"""
    if not video_info:
        return ""
    src_w, src_h = video_info["width"], video_info["height"]
    fps, duration = video_info["fps"], video_info["duration_sec"]

    if preset == "source":
        w, h = src_w, src_h
    elif preset == "custom":
        w, h = int(cust_w or src_w), int(cust_h or src_h)
    else:
        w, h = RESOLUTION_PRESETS[preset]

    start = float(start_sec or 0)
    end = float(end_sec) if end_sec else duration

    msgs = []
    if end <= start or end > duration + 1e-6:
        return T(lang, "warn_clip_invalid_md", duration)
    if w > src_w or h > src_h:
        msgs.append(T(lang, "warn_upscale", w, h, src_w, src_h))
    if w * h > 1024 * 1024:
        msgs.append(T(lang, "warn_pixels", w, h))
    clip_len = end - start
    est_frames = int(round(clip_len * fps))
    if clip_len > 60:
        msgs.append(T(lang, "warn_long", clip_len, est_frames))
    else:
        msgs.append(T(lang, "info_frames", est_frames, clip_len))
    return "\n\n".join(msgs)


def run_process(video_path, video_info, preset, cust_w, cust_h,
                start_sec, end_sec, model_complexity, lang,
                progress=gr.Progress()):
    # 延后加载 OpenCV / NumPy / MediaPipe；这些依赖只在真正开始处理时才需要，
    # 不再拖慢应用窗口和网页首次打开。
    from .pipeline import probe_video, process_video

    if not video_path:
        raise gr.Error(T(lang, "err_no_video"))
    if not video_info:
        try:
            video_info = probe_video(video_path)
        except Exception as e:
            raise gr.Error(T(lang, "read_fail", e))
    duration = video_info["duration_sec"]

    if preset == "source":
        w = h = None
    elif preset == "custom":
        if cust_w is None or cust_h is None:
            raise gr.Error(T(lang, "err_custom_empty"))
        w, h = int(cust_w), int(cust_h)
        if w <= 0 or h <= 0:
            raise gr.Error(T(lang, "err_custom_positive"))
    else:
        w, h = RESOLUTION_PRESETS[preset]

    start = float(start_sec or 0)
    end = float(end_sec) if end_sec else duration
    if end <= start or end > duration + 1e-6:
        raise gr.Error(T(lang, "err_clip_invalid", duration))

    out_dir = tempfile.mkdtemp(prefix="pose_extractor_")
    out_video = os.path.join(out_dir, "skeleton.mp4")
    out_json = os.path.join(out_dir, "keypoints.json")

    def cb(done, total):
        progress(done / total, desc=T(lang, "progress_desc", done, total))

    try:
        result = process_video(
            video_path, out_video, out_json,
            out_width=w, out_height=h,
            start_sec=start, end_sec=end,
            model_complexity=int(model_complexity),
            progress_cb=cb,
        )
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(T(lang, "err_process_failed", e))
    summary = T(lang, "summary_done", result["frames_written"], result["frames_detected"])
    if w and h and (result["width"], result["height"]) != (w, h):
        summary += T(lang, "summary_even", result["width"], result["height"])
    return result["out_video"], result["out_json"], summary


def run_export_fbx(keypoints_path, lang, progress=gr.Progress()):
    """从已生成的 world-landmarks JSON 导出 animation-only FBX。"""
    if not keypoints_path:
        raise gr.Error(T(lang, "err_no_json"))
    from .fbx_export import export_fbx

    progress(0.1, desc=T(lang, "fbx_exporting"))
    out_fbx = os.path.join(os.path.dirname(keypoints_path), "animation.fbx")
    try:
        export_fbx(keypoints_path, out_fbx, root_motion=False)
    except Exception as e:
        raise gr.Error(T(lang, "err_fbx_failed", e))
    progress(1.0, desc=T(lang, "fbx_done"))
    return out_fbx, T(lang, "fbx_done")


# ---------------------------------------------------------------------------
# 输出预览尺寸控制（缩略/宽屏/全屏）
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
#input_video { max-width: 480px !important; }
#input_video .wrap { max-width: 480px !important; height: 320px !important; }
#input_video video { width: 480px !important; height: 320px !important; object-fit: contain; }
#output_video { max-width: 340px; }
#output_video video { max-height: 360px; object-fit: contain; }
#output_video.preview-wide { max-width: 100%; }
"""

JS_THUMB = "() => { const el = document.getElementById('output_video'); if (el) el.classList.remove('preview-wide'); }"
JS_WIDE = "() => { const el = document.getElementById('output_video'); if (el) el.classList.add('preview-wide'); }"
JS_FULL = "() => { const v = document.querySelector('#output_video video'); if (v && v.requestFullscreen) { v.requestFullscreen(); } }"


def build_ui():
    # analytics_enabled=False：关闭遥测。否则 gradio 会往自身包目录写 launches.json，
    # PyInstaller 打包后这会破坏已签名 .app 的 seal（codesign 校验失败）。
    with gr.Blocks(title="PoseExtractor", css=CUSTOM_CSS, analytics_enabled=False) as demo:
        lang_state = gr.State(DEFAULT_LANG)
        video_info = gr.State(None)

        with gr.Row():
            with gr.Column(scale=5):
                title_md = gr.Markdown(T("zh", "title_md"))
            with gr.Column(scale=1, min_width=180):
                lang_radio = gr.Radio(list(LANGS.keys()), value="中文",
                                      label="Language / 语言", container=False)

        with gr.Row():
            with gr.Column():
                # 限制预览尺寸：不会改变上传文件或后续检测使用的原始分辨率。
                video_in = gr.Video(label=T("zh", "video_in_label"), sources=["upload"],
                                    width=480, height=320, elem_id="input_video")
                info_md = gr.Markdown(T("zh", "info_placeholder"))
                params_md = gr.Markdown(T("zh", "params_md"))
                preset = gr.Radio(preset_choices("zh"), value="source",
                                  label=T("zh", "preset_label"))
                with gr.Row(visible=False) as cust_row:
                    cust_w = gr.Number(value=512, precision=0, label=T("zh", "cust_w_label"))
                    cust_h = gr.Number(value=512, precision=0, label=T("zh", "cust_h_label"))
                with gr.Row():
                    start_sec = gr.Number(value=0, label=T("zh", "start_label"))
                    end_sec = gr.Number(value=0, label=T("zh", "end_label"))
                complexity = gr.Radio([0, 1, 2], value=1,
                                      label=T("zh", "complexity_label"))
                warn_md = gr.Markdown("")
                btn = gr.Button(T("zh", "btn_label"), variant="primary")
            with gr.Column():
                video_out = gr.Video(label=T("zh", "video_out_label"),
                                     elem_id="output_video")
                with gr.Row():
                    btn_thumb = gr.Button(T("zh", "thumb_btn"), size="sm")
                    btn_wide = gr.Button(T("zh", "wide_btn"), size="sm")
                    btn_full = gr.Button(T("zh", "full_btn"), size="sm")
                json_out = gr.File(label=T("zh", "json_out_label"))
                btn_fbx = gr.Button(T("zh", "fbx_btn_label"))
                fbx_out = gr.File(label=T("zh", "fbx_out_label"))
                status_md = gr.Markdown("")

        # --- 语言切换 ---
        def on_lang_change(display_lang, info, p, cw, ch, s, e):
            lang = LANGS.get(display_lang, DEFAULT_LANG)
            info_text = _fmt_info(info, lang) if info else T(lang, "info_placeholder")
            warn = compute_warnings(info, p, cw, ch, s, e, lang)
            return (
                gr.update(value=T(lang, "title_md")),
                gr.update(label=T(lang, "video_in_label")),
                gr.update(value=info_text),
                gr.update(value=T(lang, "params_md")),
                gr.update(choices=preset_choices(lang), label=T(lang, "preset_label")),
                gr.update(label=T(lang, "cust_w_label")),
                gr.update(label=T(lang, "cust_h_label")),
                gr.update(label=T(lang, "start_label")),
                gr.update(label=T(lang, "end_label")),
                gr.update(label=T(lang, "complexity_label")),
                gr.update(value=T(lang, "btn_label")),
                gr.update(label=T(lang, "video_out_label")),
                gr.update(value=T(lang, "thumb_btn")),
                gr.update(value=T(lang, "wide_btn")),
                gr.update(value=T(lang, "full_btn")),
                gr.update(label=T(lang, "json_out_label")),
                gr.update(value=T(lang, "fbx_btn_label")),
                gr.update(label=T(lang, "fbx_out_label")),
                gr.update(value=warn),
                gr.update(value=""),
                lang,
            )

        lang_radio.change(
            on_lang_change,
            [lang_radio, video_info, preset, cust_w, cust_h, start_sec, end_sec],
            [title_md, video_in, info_md, params_md, preset, cust_w, cust_h,
             start_sec, end_sec, complexity, btn, video_out,
             btn_thumb, btn_wide, btn_full, json_out, btn_fbx, fbx_out,
             warn_md, status_md, lang_state],
            api_name="switch_lang",
        )

        # --- 预览尺寸控制（纯前端） ---
        btn_thumb.click(None, None, None, js=JS_THUMB)
        btn_wide.click(None, None, None, js=JS_WIDE)
        btn_full.click(None, None, None, js=JS_FULL)

        def on_preset_change(p):
            return gr.update(visible=(p == "custom"))

        preset.change(on_preset_change, preset, cust_row)

        def refresh(video_path, info, p, cw, ch, s, e, lang):
            if not video_path:
                return "", None, "", gr.update()
            try:
                # 同样延后导入视频处理依赖，让初始界面尽快可用。
                from .pipeline import ensure_browser_playable, probe_video
                # HEVC 等浏览器播不了的编码 -> 转成 H.264 副本，预览和处理都用它
                play_path, converted = ensure_browser_playable(video_path)
                info = probe_video(play_path)
            except Exception as ex:
                return T(lang, "read_fail", ex), None, "", gr.update()
            info_text = _fmt_info(info, lang)
            if converted:
                info_text += T(lang, "note_transcoded")
            warn = compute_warnings(info, p, cw, ch, s, 0, lang)
            return info_text, info, warn, gr.update(value=play_path)

        video_in.change(refresh,
                        [video_in, video_info, preset, cust_w, cust_h,
                         start_sec, end_sec, lang_state],
                        [info_md, video_info, warn_md, video_in])

        warn_inputs = [video_info, preset, cust_w, cust_h, start_sec, end_sec, lang_state]
        for comp in (preset, cust_w, cust_h, start_sec, end_sec):
            comp.change(compute_warnings, warn_inputs, warn_md)

        btn.click(run_process,
                  [video_in, video_info, preset, cust_w, cust_h,
                   start_sec, end_sec, complexity, lang_state],
                  [video_out, json_out, status_md],
                  api_name="process")
        btn_fbx.click(run_export_fbx, [json_out, lang_state], [fbx_out, status_md],
                      api_name="export_fbx")
    return demo
