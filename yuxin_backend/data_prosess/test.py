import cv2
import os

def create_video_from_frames(frame_folder, output_video, fps=30, frame_size=None):
    # 获取文件夹中所有的帧文件，假设帧文件是按序号命名的，如 frame1.png, frame2.png 等
    frame_files = sorted([f for f in os.listdir(frame_folder) if f.endswith(('.jpg', '.png'))])

    # 获取第一帧的大小，假设所有帧的大小一致
    first_frame = cv2.imread(os.path.join(frame_folder, frame_files[0]))
    if frame_size is None:
        frame_size = (first_frame.shape[1], first_frame.shape[0])  # (宽, 高)

    # 设置视频写入器，编码器这里选择H.264
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter(output_video, fourcc, fps, frame_size)

    for frame_file in frame_files:
        frame_path = os.path.join(frame_folder, frame_file)
        frame = cv2.imread(frame_path)
        if frame is None:
            print(f"无法读取帧: {frame_path}")
            continue
        # 这里假设所有帧大小一致，若不同则可以在此处调整尺寸
        out.write(frame)

    # 释放资源
    out.release()
    print(f"视频已保存到: {output_video}")

# 示例用法
frame_folder = 'assets/数据集/data/image/train'  # 图片帧所在文件夹路径
output_video = 'assets/output/output_video.mp4'  # 输出视频
create_video_from_frames(frame_folder, output_video)
