# -*- coding: utf-8 -*-
"""Gradio 界面与风险提示逻辑。"""
import os
import tempfile

import gradio as gr

from .pipeline import probe_video, process_video

RESOLUTION_PRESETS = {
    "与源一致": None,
    "512x512": (512, 512),
    "768x768": (768, 768),
    "1024x1024": (1024, 1024),
    "自定义": "custom",
}


def _fmt_info(info):
    return ("分辨率: {width}x{height}　|　帧率: {fps:.2f} fps　|　"
            "时长: {duration_sec:.2f} 秒　|　总帧数: {frame_count}").format(**info)


def on_upload(video_path):
    """上传/更换视频后：读取源信息并刷新提示。"""
    if not video_path:
        return "", gr.update(), gr.update()
    try:
        info = probe_video(video_path)
    except Exception as e:
        return "读取视频失败: %s" % e, gr.update(), gr.update()
    return _fmt_info(info), info["duration_sec"], info


def compute_warnings(video_info, preset, cust_w, cust_h, start_sec, end_sec):
    """根据当前参数生成风险提示列表（返回 Markdown 文本）。"""
    if not video_info:
        return ""
    src_w, src_h = video_info["width"], video_info["height"]
    fps, duration = video_info["fps"], video_info["duration_sec"]

    if preset == "与源一致":
        w, h = src_w, src_h
    elif preset == "自定义":
        w, h = int(cust_w or src_w), int(cust_h or src_h)
    else:
        w, h = RESOLUTION_PRESETS[preset]

    start = float(start_sec or 0)
    end = float(end_sec) if end_sec else duration

    msgs = []
    if end <= start or end > duration + 1e-6:
        return "❌ **裁剪区间非法**：结束时间必须大于开始时间，且不超过视频总长 %.2f 秒。" % duration
    if w > src_w or h > src_h:
        msgs.append("⚠️ 输出分辨率(%dx%d)超过源分辨率(%dx%d)：放大不会增加细节，只会更慢。"
                    % (w, h, src_w, src_h))
    if w * h > 1024 * 1024:
        msgs.append("⚠️ 输出总像素(%dx%d)超过 1024x1024：处理会明显变慢。" % (w, h))
    clip_len = end - start
    est_frames = int(round(clip_len * fps))
    if clip_len > 60:
        msgs.append("⚠️ 裁剪后时长 %.1f 秒，预计处理约 %d 帧，耗时较长，请耐心等待。"
                    % (clip_len, est_frames))
    else:
        msgs.append("ℹ️ 预计处理约 %d 帧（%.1f 秒）。" % (est_frames, clip_len))
    return "\n\n".join(msgs)


def run_process(video_path, video_info, preset, cust_w, cust_h,
                start_sec, end_sec, model_complexity, progress=gr.Progress()):
    if not video_path:
        raise gr.Error("请先上传视频。")
    if not video_info:
        video_info = probe_video(video_path)
    duration = video_info["duration_sec"]

    if preset == "与源一致":
        w = h = None
    elif preset == "自定义":
        if cust_w is None or cust_h is None:
            raise gr.Error("自定义分辨率不能为空。")
        w, h = int(cust_w), int(cust_h)
        if w <= 0 or h <= 0:
            raise gr.Error("自定义分辨率必须为正整数。")
    else:
        w, h = RESOLUTION_PRESETS[preset]

    start = float(start_sec or 0)
    end = float(end_sec) if end_sec else duration
    if end <= start or end > duration + 1e-6:
        raise gr.Error("裁剪区间非法：结束时间必须大于开始时间，且不超过视频总长 %.2f 秒。" % duration)

    out_dir = tempfile.mkdtemp(prefix="pose_extractor_")
    out_video = os.path.join(out_dir, "skeleton.mp4")
    out_json = os.path.join(out_dir, "keypoints.json")

    def cb(done, total):
        progress(done / total, desc="处理帧 %d/%d" % (done, total))

    result = process_video(
        video_path, out_video, out_json,
        out_width=w, out_height=h,
        start_sec=start, end_sec=end,
        model_complexity=int(model_complexity),
        progress_cb=cb,
    )
    summary = ("✅ 完成：写出 %d 帧，其中 %d 帧检出人体姿态。"
               % (result["frames_written"], result["frames_detected"]))
    if w and h and (result["width"], result["height"]) != (w, h):
        summary += "（奇数宽/高已调整为偶数 %dx%d，以满足 H.264 编码要求）" % (
            result["width"], result["height"])
    return result["out_video"], result["out_json"], summary


def build_ui():
    with gr.Blocks(title="PoseExtractor 骨架提取") as demo:
        gr.Markdown("# 人物动作视频 → 黑底骨架视频 + 关键点 JSON\n"
                    "使用 MediaPipe Pose（33 关键点），适用于 AI 视频生成（ControlNet OpenPose 风格）。")
        video_info = gr.State(None)

        with gr.Row():
            with gr.Column():
                video_in = gr.Video(label="上传视频（mp4/mov 等）", sources=["upload"])
                info_md = gr.Markdown("上传后显示源视频信息")
                gr.Markdown("### 参数")
                preset = gr.Radio(list(RESOLUTION_PRESETS.keys()), value="与源一致",
                                  label="输出分辨率预设")
                with gr.Row(visible=False) as cust_row:
                    cust_w = gr.Number(value=512, precision=0, label="自定义宽")
                    cust_h = gr.Number(value=512, precision=0, label="自定义高")
                with gr.Row():
                    start_sec = gr.Number(value=0, label="开始秒")
                    end_sec = gr.Number(value=0, label="结束秒（0=全长）")
                complexity = gr.Radio([0, 1, 2], value=1,
                                      label="MediaPipe model_complexity（越大越准越慢）")
                warn_md = gr.Markdown("")
                btn = gr.Button("开始处理", variant="primary")
            with gr.Column():
                video_out = gr.Video(label="骨架视频预览")
                json_out = gr.File(label="关键点 JSON 下载")
                status_md = gr.Markdown("")

        def on_preset_change(p):
            return gr.update(visible=(p == "自定义"))

        preset.change(on_preset_change, preset, cust_row)

        def refresh(video_path, info, p, cw, ch, s, e):
            info_text, dur, info = on_upload(video_path)
            if info:
                e_val = 0
                warn = compute_warnings(info, p, cw, ch, s, e_val)
                return info_text, info, warn
            return info_text, None, ""

        video_in.change(refresh,
                        [video_in, video_info, preset, cust_w, cust_h, start_sec, end_sec],
                        [info_md, video_info, warn_md])

        warn_inputs = [video_info, preset, cust_w, cust_h, start_sec, end_sec]
        for comp in (preset, cust_w, cust_h, start_sec, end_sec):
            comp.change(compute_warnings, warn_inputs, warn_md)

        btn.click(run_process,
                  [video_in, video_info, preset, cust_w, cust_h,
                   start_sec, end_sec, complexity],
                  [video_out, json_out, status_md])
    return demo
